import re
from statistics import mean, stdev
from test_base import TestBase
from tool_evaluation import ToolEvaluation


class Test2(TestBase):
    """
    P2 - Label inaccuracy Assessment (thesis Section 5.5.2 / Table 13).

    Reads the tool's performance on the original ("user") dataset and on the
    five label-noise levels produced by Dispatcher.inject_label_engine_p2 in
    datapreprocessor.py (0.5%, 1%, 1.5%, 2%, 2.5% symmetric, per-class
    label-swap noise -- contract source code is byte-identical across all
    variants, only the ground-truth labels differ). Each level has
    P2_N_REPEATS (10) independent repeats -- P2_noise_{pct}pct_rep{1..10} --
    kept equal to the ReChecker baseline's repeat count for comparability.

    Per-repeat results are grouped by noise fraction and averaged (mean +
    sample stddev, N-1 -- each set of repeats is a sample of the space of
    possible executions, not the full population) before the
    monotonicity/proportionality analysis below runs on the resulting
    5 (+ baseline) points, rather than on 50 raw per-repeat points.

    For each recorded measure, this test compares performance on every noise
    level against the unperturbed baseline and checks whether the decline is
    gradual and roughly proportionate to the injected noise magnitude
    (indicating the tool has learned the real vulnerability signature) or
    shows an abrupt / disproportionate shift at some threshold (indicating
    instability / overfitting to labelling artefacts).
    """

    # matches "user" (baseline) or "P2_noise_{pct}pct_rep{rep}" -- parses
    # fraction and rep directly out of dataset_name instead of a static
    # name->fraction table, so it stays correct regardless of P2_N_REPEATS
    # or P2_NOISE_LEVELS in Dispatcher (datapreprocessor.py).
    NOISE_NAME_PATTERN = re.compile(r"^P2_noise_([\d.]+)pct_rep(\d+)$")

    # expected number of repeats per noise level -- kept equal to the
    # ReChecker baseline's repeat count (P2_N_REPEATS in datapreprocessor.py)
    # so results are directly comparable. A level with fewer than this many
    # results (e.g. a partially-finished run) still gets averaged, just with
    # a [WARN] instead of a crash.
    EXPECTED_REPEATS = 10

    # "accuracy" (fraction of samples where predicted == label) is used as
    # the primary series: it is numerically the "Label Agreement" measure
    # Table 13 names as the evaluation metric for P2. precision/recall/f1
    # are checked as secondary corroborating measures.
    PRIMARY_MEASURE = "accuracy"
    SECONDARY_MEASURES = ("precision", "recall", "f1")

    # tolerance (in metric points, e.g. 0.02 = 2 percentage points) allowed
    # before a step that goes the "wrong way" is treated as a real reversal
    # rather than ordinary sampling noise
    MONOTONICITY_TOLERANCE = 0.02

    # a level-to-level jump larger than this multiple of the mean jump size
    # is treated as an "abrupt" shift rather than a gradual decline
    ABRUPT_JUMP_FACTOR = 3.0

    # minimum R^2 of (performance drop) vs (noise fraction) for the decline
    # to be judged "proportionate" to the injected noise magnitude
    MIN_R2_PROPORTIONALITY = 0.5

    # ********************************************************
    def __init__(self):
        pass

    # ********************************************************
    def parse_dataset_name(self, dataset_name):
        """
        "user" -> (0.0, None) (the unperturbed baseline, no repeats).
        "P2_noise_{pct}pct_rep{rep}" -> (pct/100, rep), e.g.
        "P2_noise_0.5pct_rep3" -> (0.005, 3).
        Raises ValueError for anything else.
        """
        if dataset_name == "user":
            return 0.0, None

        match = self.NOISE_NAME_PATTERN.match(dataset_name)
        if not match:
            raise ValueError(
                f"unknown dataset_name '{dataset_name}'; expected 'user' or "
                f"'P2_noise_<pct>pct_rep<n>'"
            )

        fraction = float(match.group(1)) / 100
        rep = int(match.group(2))
        return fraction, rep

    # ********************************************************
    def load_input_test(self, payload):
        """
        payload: {tool_id: {dataset_id: {tool_name, dataset_name, metrics,
                                          prediction_eval}}}
        as produced by the tool-based path in test_executor.py
        (packaged_eval in TestExecutor.run_tests_group).

        Groups per-repeat results by noise fraction and, for each recorded
        measure, averages across the repeats found at that fraction (mean +
        sample stddev, N-1; None when only 1 repeat is available since
        sample stddev is undefined for a single observation). Returns the
        resulting per-level series (one point per fraction, including the
        0.0 baseline) alongside the raw per-repeat values for reporting.
        """
        print("start load_input_test function test 2 ...", flush=True)

        if not payload:
            raise ValueError(
                "test2 requires tool-based results (tool_run=True on this "
                "test's registration), got an empty payload. Check that "
                "test.csv / test_tool.csv wire this test to the 'ml' tool."
            )

        if len(payload) != 1:
            print(
                f"[WARN] test2 expects results for exactly one tool, got "
                f"{len(payload)}; using the first one.",
                flush=True
            )

        tool_id = next(iter(payload))
        datasets_for_tool = payload[tool_id]

        # fraction -> [(rep, metrics), ...] for every repeat seen at that level
        by_fraction = {}
        for dataset_id, item in datasets_for_tool.items():
            dataset_name = item["dataset_name"]
            metrics = item["metrics"]

            fraction, rep = self.parse_dataset_name(dataset_name)
            by_fraction.setdefault(fraction, []).append((rep, metrics))

        if not by_fraction:
            raise ValueError("no datasets found for test2")

        if 0.0 not in by_fraction:
            raise ValueError(
                "no baseline ('user', fraction=0.0) dataset found among "
                "test2 results; cannot measure degradation without it"
            )

        all_measures = (self.PRIMARY_MEASURE,) + self.SECONDARY_MEASURES

        # sort by increasing noise fraction so index 0 is always the baseline
        fractions = sorted(by_fraction)
        series = {measure: [] for measure in all_measures}
        series_std = {measure: [] for measure in all_measures}
        raw_by_fraction = {}

        for fraction in fractions:
            reps = by_fraction[fraction]
            n = len(reps)
            if fraction != 0.0 and n != self.EXPECTED_REPEATS:
                print(
                    f"[WARN] noise level {fraction} has {n} result(s), "
                    f"expected {self.EXPECTED_REPEATS} (P2_N_REPEATS); "
                    f"averaging over what's available instead of failing.",
                    flush=True
                )

            raw_by_fraction[fraction] = {
                "reps": [r for r, _ in reps],
                "metrics": [m for _, m in reps],
            }

            for measure in all_measures:
                values = [m.get(measure) for _, m in reps if m.get(measure) is not None]
                if values:
                    series[measure].append(mean(values))
                    # sample stdev (N-1) is undefined for a single observation --
                    # None (not 0.0) signals "not computable", not "zero variance"
                    series_std[measure].append(stdev(values) if len(values) > 1 else None)
                else:
                    series[measure].append(None)
                    series_std[measure].append(None)

        print("end load_input_test function test 2 ***********", flush=True)

        return {
            "fractions": fractions,
            "series": series,
            "series_std": series_std,
            "raw_by_fraction": raw_by_fraction,
        }

    # ********************************************************
    def compute_deltas(self, values, baseline):
        """Performance drop relative to baseline at each noise level."""
        return [baseline - v for v in values]

    # ********************************************************
    def check_monotonic(self, deltas):
        """
        True if the performance drop is non-decreasing as noise increases
        (allowing MONOTONICITY_TOLERANCE of slack for ordinary noise).
        """
        for prev, curr in zip(deltas, deltas[1:]):
            if curr < prev - self.MONOTONICITY_TOLERANCE:
                return False
        return True

    # ********************************************************
    def check_abrupt_jump(self, deltas):
        """
        True if some single step between adjacent noise levels increases far
        more than the average step, i.e. an abrupt shift rather than a
        gradual decline.
        """
        steps = [b - a for a, b in zip(deltas, deltas[1:])]
        if not steps:
            return False

        mean_step = mean(steps)
        if mean_step <= 0:
            abs_steps = sorted(abs(s) for s in steps)
            mean_step = mean(abs_steps[:-1]) if len(abs_steps) > 1 else abs_steps[0]
            mean_step = mean_step or 1e-9
        return any(step > self.ABRUPT_JUMP_FACTOR * mean_step for step in steps)

    # ********************************************************
    def r_squared(self, x, y):
        """R^2 of the best-fit line through (x, y); used to judge whether
        the performance drop scales roughly linearly with noise fraction."""
        n = len(x)
        if n < 2:
            return 1.0

        x_mean = mean(x)
        y_mean = mean(y)

        ss_xx = sum((xi - x_mean) ** 2 for xi in x)
        if ss_xx == 0:
            return 0.0

        ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        slope = ss_xy / ss_xx
        intercept = y_mean - slope * x_mean

        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        if ss_tot == 0:
            return 1.0

        ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
        return 1 - ss_res / ss_tot

    # ********************************************************
    def compare(self, input_test):
        print("start compare function test 2 ...", flush=True)

        fractions = input_test["fractions"]
        series = input_test["series"]
        series_std = input_test.get("series_std", {})
        raw_by_fraction = input_test.get("raw_by_fraction", {})

        if fractions[0] != 0.0:
            raise ValueError(
                "expected the first (sorted-by-fraction) point to be the "
                "0.0 baseline"
            )

        per_measure_result = {}

        for measure, values in series.items():
            if any(v is None for v in values):
                print(
                    f"[WARN] measure '{measure}' missing for some noise "
                    f"levels, skipping it in the assessment",
                    flush=True
                )
                continue

            baseline = values[0]
            deltas = self.compute_deltas(values, baseline)

            monotonic_ok = self.check_monotonic(deltas)
            abrupt = self.check_abrupt_jump(deltas)
            r2 = self.r_squared(fractions, deltas)
            proportionate_ok = r2 >= self.MIN_R2_PROPORTIONALITY

            per_measure_result[measure] = {
                "values": values,
                "std": series_std.get(measure),
                "deltas": deltas,
                "monotonic": monotonic_ok,
                "abrupt_jump": abrupt,
                "r_squared": round(r2, 4),
                "proportionate": proportionate_ok,
            }

            print(
                f"  [{measure}] values={values} std={series_std.get(measure)} "
                f"deltas={deltas} monotonic={monotonic_ok} abrupt={abrupt} "
                f"r2={r2:.3f}",
                flush=True
            )

        print("end compare function test 2 ***********", flush=True)

        return {
            "fractions": fractions,
            "per_measure": per_measure_result,
            # raw per-repeat values per noise level (fraction -> {reps, metrics}),
            # kept for the thesis so both mean and spread can be reported per level
            "raw_by_fraction": raw_by_fraction,
        }

    # ********************************************************
    def run(self, context):
        print("start run function test 2 ...", flush=True)

        result = self.compare(self.load_input_test(context["payload"]))

        primary = result["per_measure"].get(self.PRIMARY_MEASURE)

        if primary is None:
            assessment = "FAIL"
        else:
            primary_ok = (
                primary["monotonic"]
                and primary["proportionate"]
                and not primary["abrupt_jump"]
            )

            secondary_checks = [
                r["monotonic"] and r["proportionate"] and not r["abrupt_jump"]
                for name, r in result["per_measure"].items()
                if name != self.PRIMARY_MEASURE
            ]
            # don't let one noisy secondary measure sink an otherwise stable
            # result -- require a majority of the secondary measures to agree
            secondary_ok = (
                sum(secondary_checks) >= len(secondary_checks) / 2
                if secondary_checks else True
            )

            assessment = "PASS" if (primary_ok and secondary_ok) else "FAIL"

        print("result", result, flush=True)
        print("assessment", assessment, flush=True)
        print("end run function test 2 ***********", flush=True)

        return {
            "test_result": result,
            "test_assessment": assessment
        }