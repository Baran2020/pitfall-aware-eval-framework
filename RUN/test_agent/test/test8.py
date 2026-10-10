from test_base import TestBase
from tool_evaluation import ToolEvaluation


class Test8(TestBase):
    """
    P8 - Base Rate Fallacy Assessment (thesis Section 5.5.7 / Table 13).

    Re-evaluates the ML detection tool across the four skewed base-rate
    variants built by skew_synthesis_engine() in datapreprocessor.py
    (offsets of -5, -2.5, +2.5, +5 percentage points from the dataset's
    natural base rate, each built by oversampling-with-replacement existing
    contracts of one class only -- no contract's own label or content is
    ever altered) plus the "user" dataset itself as the zero-offset,
    natural-rate point: the natural rate is exactly what "user" already is,
    so there is no need for skew_synthesis_engine to duplicate it under a
    new name -- "user" is already registered and already evaluated by the
    other tests (P2/P4/P6/P7), so this test reuses that same tool result.

    A detector that has genuinely learned the reentrancy vulnerability
    should keep its prevalence-*robust* measures (MCC, geometric mean,
    Cohen's kappa, CSI -- the same battery test7/P7 reports) roughly stable
    across the whole spectrum. A detector subject to the base-rate fallacy
    will instead look fine on prevalence-*sensitive* measures (accuracy,
    precision, recall, f1) at the dataset's natural/default rate, while its
    robust measures collapse toward chance/zero at the low-prevalence end
    of the spectrum, where class imbalance is most severe -- meaning its
    reported reliability at the default rate is not representative of its
    behaviour in the realistic, highly imbalanced deployment setting.
    """

    # Ordered from the most severe imbalance (lowest base rate, positive
    # class rarest) to the least severe (highest base rate). "user" is the
    # unmodified dataset (zero offset) -- not something skew_synthesis_engine
    # generates. Keep the four skewed names in sync with what
    # skew_synthesis_engine() registers in datapreprocessor.py /
    # generate_dataset_name(8) in import_tests_to_database.py.
    SPECTRUM_ORDER = [
        "P8_base_rate_minus5pct",
        "P8_base_rate_minus2.5pct",
        "user",
        "P8_base_rate_plus2.5pct",
        "P8_base_rate_plus5pct",
    ]

    # The dataset's own, unperturbed base rate -- the "default base rate"
    # the thesis text compares the severe end of the spectrum against. This
    # is the "user" dataset itself, not a generated variant.
    BASELINE_VARIANT = "user"

    # The lowest-base-rate variant -- "the lower end of the tested
    # spectrum, where class imbalance is most severe" (thesis 5.5.7).
    SEVERE_VARIANT = "P8_base_rate_minus5pct"

    # Inflated by class prevalence on their own; reported for context but
    # not, by themselves, grounds to pass the test -- they are exactly the
    # measures the base-rate fallacy makes look better than they are.
    PREVALENCE_SENSITIVE = ("accuracy", "precision", "recall", "f1")

    # Designed to stay meaningful under class imbalance. Table 13's
    # "Generalisation Gap" is measured over these.
    PREVALENCE_ROBUST = ("mcc", "gm", "kappa", "csi")

    # Per-measure floor a robust measure must stay above at the severe end
    # of the spectrum. Mirrors the thresholds test7/P7 already uses for the
    # same measures, so a tool judged reliable here is held to the same bar
    # it is held to there.
    ROBUST_FLOOR = {"mcc": 0.25, "gm": 0.30, "kappa": 0.20, "csi": 0.20}

    # A robust measure is considered unstable if it drops by more than this
    # many points from the balanced end to the severe end of the spectrum.
    MAX_ALLOWED_DROP = 0.25

    # ************************************************************************************************************
    def __init__(self):
        self.tool_evaluation = ToolEvaluation()

    # ************************************************************************************************************
    def load_input_test(self, context):
        print("start load_input_test function test 8 ...", flush=True)

        payload = context["payload"]  # {tool_id: {dataset_id: {dataset_name, metrics, prediction_eval}}}

        if not payload:
            raise ValueError(
                "test8 requires tool-based results (tool_run=True on this "
                "test's registration), got an empty payload."
            )

        if len(payload) != 1:
            print(
                f"[WARN] test8 expects results for exactly one tool (ml), "
                f"got {len(payload)}; using the first one.",
                flush=True
            )

        tool_id = next(iter(payload))
        datasets_for_tool = payload[tool_id]

        by_name = {}
        for dataset_id, value in datasets_for_tool.items():
            dataset_name = value.get("dataset_name")
            if dataset_name not in self.SPECTRUM_ORDER:
                raise ValueError(
                    f"unknown dataset_name '{dataset_name}' for dataset_id "
                    f"'{dataset_id}'. expected one of: {self.SPECTRUM_ORDER}"
                )
            by_name[dataset_name] = value["metrics"]

        missing = [name for name in self.SPECTRUM_ORDER if name not in by_name]
        if missing:
            raise ValueError(f"test8: missing base-rate variant(s) in payload: {missing}")

        print("end load_input_test function test 8 ***********", flush=True)

        return {
            "tool_id": tool_id,
            "spectrum": self.SPECTRUM_ORDER,
            "metrics_by_variant": by_name,
        }

    # ************************************************************************************************************
    def compare(self, input_test):
        print("start compare function test 8 ...", flush=True)

        spectrum = input_test["spectrum"]
        metrics_by_variant = input_test["metrics_by_variant"]

        baseline_name = self.BASELINE_VARIANT   # dataset's natural/default rate
        severe_name = self.SEVERE_VARIANT       # lowest base rate in the spectrum

        per_measure = {}
        for measure in self.PREVALENCE_SENSITIVE + self.PREVALENCE_ROBUST:
            series = [metrics_by_variant[name].get(measure, 0) for name in spectrum]

            # Generalisation Gap (Table 13): default/natural rate -> most
            # severe (lowest) rate in the tested spectrum.
            baseline_value = metrics_by_variant[baseline_name].get(measure, 0)
            severe_value = metrics_by_variant[severe_name].get(measure, 0)
            gap = baseline_value - severe_value

            per_measure[measure] = {
                "series": series,
                "baseline_value": baseline_value,
                "severe_value": severe_value,
                "generalisation_gap": round(gap, 4),
            }

            print(f"  [{measure}] {dict(zip(spectrum, series))}  gap={round(gap, 4)}", flush=True)

        print("end compare function test 8 ***********", flush=True)

        return {
            "spectrum": spectrum,
            "baseline_variant": baseline_name,
            "severe_variant": severe_name,
            "per_measure": per_measure,
        }

    # ************************************************************************************************************
    def is_pass(self, per_measure):
        """
        The base-rate fallacy is judged absent (PASS) only if every
        prevalence-robust measure (a) stays above its floor at every point
        in the tested spectrum -- not just at the natural rate -- and
        (b) does not drop by more than MAX_ALLOWED_DROP between the
        dataset's default rate and the most severe (lowest) rate tested.
        A tool that fails either check has reported performance that is an
        artefact of the base rate it happened to be evaluated at, rather
        than genuine detection capability.
        """
        for measure in self.PREVALENCE_ROBUST:
            floor = self.ROBUST_FLOOR[measure]

            if any(value <= floor for value in per_measure[measure]["series"]):
                return False
            if per_measure[measure]["generalisation_gap"] > self.MAX_ALLOWED_DROP:
                return False

        return True

    # ************************************************************************************************************
    def run(self, context):
        print("start test 8 ...", flush=True)

        input_test = self.load_input_test(context)
        test_result = self.compare(input_test)

        passed = self.is_pass(test_result["per_measure"])
        assessment = "PASS" if passed else "FAIL"

        print(f"\n  -- Base-rate spectrum: {' -> '.join(test_result['spectrum'])} --", flush=True)
        for measure, r in test_result["per_measure"].items():
            tag = "robust" if measure in self.PREVALENCE_ROBUST else "sensitive"
            print(
                f"      [{tag:9s}] {measure:9s} series={r['series']}  "
                f"generalisation_gap={r['generalisation_gap']}",
                flush=True
            )

        print(f"\n  -- Test 8 assessment: {assessment} --\n", flush=True)

        return {
            "test_result": test_result,
            "test_assessment": assessment
        }
    # ************************************************************************************************************
