import os
import subprocess
from test_base import TestBase
from statistics import mean


class Test1(TestBase):

    def __init__(self):
        pass
    KNOWN_DATASETS = {"user_excel", "ethereum"}
    # ********************************************************
    def load_input_test(self, evaluation_results_list):

        print("start load_input_test function test 1 ...", flush=True)

        user_entropy = []
        user_merged_entropy = []

        eth_entropy = []
        eth_merged_entropy = []

        for dataset_id, item in evaluation_results_list.items():  

            #dataset_id = item["dataset_id"]
            dataset_name=item["dataset_name"]
            metrics = item["metrics"]

            if dataset_name not in self.KNOWN_DATASETS:
                raise ValueError(
                    f"unknown dataset_name '{dataset_name}' "
                    f"for dataset_id '{dataset_id}'. "
                    f"expected one of: {self.KNOWN_DATASETS}"
                )

            if dataset_name == "user_excel":
                user_entropy.extend(metrics["entropy_distribution"])
                user_merged_entropy.extend(metrics["merged_entropy_distribution"])

            elif dataset_name == "ethereum":
                eth_entropy.extend(metrics["entropy_distribution"])
                eth_merged_entropy.extend(metrics["merged_entropy_distribution"])

        print("end load_input_test function test 1 ***********", flush=True)        

        return {
            "avg_user_entropy": user_entropy,
            "avg_user_merged_entropy": user_merged_entropy,
            "avg_ethereum_entropy": eth_entropy,
            "avg_ethereum_merged_entropy": eth_merged_entropy
        }

    # ********************************************************

    def empirical_percentile(self, value, distribution):
        print("start empirical_percentile function test 1 ...", flush=True)
        if not distribution:
            raise ValueError("distribution is empty")

        count_le = sum(1 for y in distribution if y <= value)
        print("end empirical_percentile function test 1 ***********", flush=True)
        return (count_le / len(distribution)) * 100

    # ********************************************************
    def distribution_percentile(self, user_dist, eth_dist):

        print("start distribution_percentile function test 1 .....", flush=True)

        print("end distribution_percentile function test 1 ***********", flush=True)
        return [
            self.empirical_percentile(x, eth_dist)
            for x in user_dist
        ]

    # ********************************************************
    def compare(self, input_test):

        print("start compare function test 1 ...", flush=True)

        user_entropy = input_test["avg_user_entropy"]
        user_merged = input_test["avg_user_merged_entropy"]

        eth_entropy = input_test["avg_ethereum_entropy"]
        eth_merged = input_test["avg_ethereum_merged_entropy"]

        if len(user_entropy) != len(user_merged):
            raise ValueError(
                f"user list length mismatch: "
                f"entropy={len(user_entropy)}, merged={len(user_merged)}"
            )

        if len(eth_entropy) != len(eth_merged):
            raise ValueError(
                f"ethereum list length mismatch: "
                f"entropy={len(eth_entropy)}, merged={len(eth_merged)}"
            )

        user_delta = [
            m - e for m, e in zip(user_merged, user_entropy)
        ]

        eth_delta = [
            m - e for m, e in zip(eth_merged, eth_entropy)
        ]

        entropy_percentiles = self.distribution_percentile(user_entropy, eth_entropy)
        merged_percentiles = self.distribution_percentile(user_merged, eth_merged)
        delta_percentiles = self.distribution_percentile(user_delta, eth_delta)

        mean_entropy_p = mean(entropy_percentiles)
        mean_merged_p = mean(merged_percentiles)
        mean_delta_p = mean(delta_percentiles)
        print("end compare function test 1 ***********", flush=True)

        return {
            "mean_entropy_percentile": mean_entropy_p,
            "mean_merged_percentile": mean_merged_p,
            "mean_delta_percentile": mean_delta_p,

            "entropy_percentiles": entropy_percentiles,
            "merged_percentiles": merged_percentiles,
            "delta_percentiles": delta_percentiles
        }

    # ********************************************************
    def in_iqr(self, p):
        if not isinstance(p, (int, float)):
            raise ValueError(
                f"expected a numeric percentile, got {type(p).__name__}: {p}"
            )

        if not (0 <= p <= 100):
            raise ValueError(
                f"percentile out of valid range [0, 100]: {p}"
            )

        if 25 <= p <= 75:
            return 1
        else:
            return 0

    # ********************************************************
    def run(self, context):

        print("start  run function test 1 ...", flush=True)

        metrics = self.load_input_test(context["payload"])
        print("metrics",metrics, flush=True)

        result = self.compare(metrics)
        print("compare(",result["mean_entropy_percentile"], flush=True)
        print("compare(",result["mean_merged_percentile"], flush=True)
        print("compare(",result["mean_delta_percentile"], flush=True)


        entropy_ok = self.in_iqr(result["mean_entropy_percentile"])
        merged_ok = self.in_iqr(result["mean_merged_percentile"])
        delta_ok = self.in_iqr(result["mean_delta_percentile"])

        assessment = "PASS" if (entropy_ok and merged_ok and delta_ok) else "FAIL"
        print("result",result, flush=True)
        print("assessment",assessment, flush=True)

        print("end run function test 1 ***********", flush=True)
        return {
            "test_result": result,
            "test_assessment": assessment
        }