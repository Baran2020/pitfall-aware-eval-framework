from test_base import TestBase
from tool_evaluation import ToolEvaluation

STATIC_TOOLS = ("manticore", "mythril", "oyente")


class Test6(TestBase):

    def __init__(self):
        self.tool_evaluation = ToolEvaluation()

    #************************************************************************************************************
    def load_input_test(self, context, baseline_result):
        payload = context["payload"]
        grouped = {}
        for tool_id, datasets in payload.items():
            for dataset_id, value in datasets.items():
                if value.get("tool_name") in STATIC_TOOLS:
                    continue
                grouped.setdefault(dataset_id, {})[tool_id] = value

        dataset_keys = list(grouped.keys())
        if len(dataset_keys) < 1:
            raise ValueError("Test6: no dataset found in payload")

        dataset_id = dataset_keys[0]
        tools = grouped[dataset_id]

        if dataset_id not in baseline_result:
            raise KeyError(f"Test6: baseline not available for dataset {dataset_id} (need >=2 static tools)")

        baseline = baseline_result[dataset_id]

        ml_tool_ids = list(tools.keys())
        if not ml_tool_ids:
            raise KeyError("Test6: no ML tool found")

        ml_tool_id = ml_tool_ids[0]
        ml = tools[ml_tool_id]["metrics"]
        bl = baseline["metrics"]

        input_test = {
            "ml_tool_id": ml_tool_id,
            "ml_TP": ml["tp"],                 "baseline_TP": bl["tp"],
            "ml_FP": ml["fp"],                 "baseline_FP": bl["fp"],
            "ml_TN": ml["tn"],                 "baseline_TN": bl["tn"],
            "ml_FN": ml["fn"],                 "baseline_FN": bl["fn"],

            "ml_accuracy":  ml["accuracy"],    "baseline_accuracy":  bl["accuracy"],
            "ml_precision": ml["precision"],   "baseline_precision": bl["precision"],
            "ml_recall":    ml["recall"],      "baseline_recall":    bl["recall"],
            "ml_f1":        ml["f1"],          "baseline_f1":        bl["f1"],
        }

        sample_predictions = baseline["prediction_eval"]
        label_re   = sum(1 for sp in sample_predictions if sp.get("label") == 1)
        label_safe = sum(1 for sp in sample_predictions if sp.get("label") == 0)
        label_total = len(sample_predictions)

        return input_test, {
            "re_count":   label_re,
            "safe_count": label_safe,
            "total":      label_total,
            "re_pct":     round(label_re   / label_total * 100, 2) if label_total else 0,
            "safe_pct":   round(label_safe / label_total * 100, 2) if label_total else 0,
        }
    #************************************************************************************************************
    @staticmethod
    def _assess(result):
        if (
            result["tp"]        < 0 or
            result["fp"]        > 0 or
            result["accuracy"]  < 0 or
            result["precision"] < 0 or
            result["recall"]    < 0 or
            result["f1"]        < 0
        ):
            return "FAIL"
        return "PASS"

    #************************************************************************************************************
    def compare(self, m):
        delta_TP        = m["ml_TP"]        - m["baseline_TP"]
        delta_FP        = m["ml_FP"]        - m["baseline_FP"]
        delta_TN        = m["ml_TN"]        - m["baseline_TN"]
        delta_FN        = m["ml_FN"]        - m["baseline_FN"]
        delta_accuracy  = m["ml_accuracy"]  - m["baseline_accuracy"]
        delta_precision = m["ml_precision"] - m["baseline_precision"]
        delta_recall    = m["ml_recall"]    - m["baseline_recall"]
        delta_f1        = m["ml_f1"]        - m["baseline_f1"]

        ml_total = m["ml_TP"] + m["ml_FP"] + m["ml_TN"] + m["ml_FN"]
        bl_total = m["baseline_TP"] + m["baseline_FP"] + m["baseline_TN"] + m["baseline_FN"]

        sum_ml_pred_re   = (m["ml_TP"] + m["ml_FP"]) / ml_total * 100 if ml_total else 0
        sum_ml_pred_safe = (m["ml_TN"] + m["ml_FN"]) / ml_total * 100 if ml_total else 0

        sum_bl_pred_re   = (m["baseline_TP"] + m["baseline_FP"]) / bl_total * 100 if bl_total else 0
        sum_bl_pred_safe = (m["baseline_TN"] + m["baseline_FN"]) / bl_total * 100 if bl_total else 0

        return {
            "delta": {
                "tp":        delta_TP,
                "fp":        delta_FP,
                "tn":        delta_TN,
                "fn":        delta_FN,
                "accuracy":  delta_accuracy,
                "precision": delta_precision,
                "recall":    delta_recall,
                "f1":        delta_f1,
            },
            "confusion_matrix": {
                "ml": {
                        "tp": m["ml_TP"],
                        "fp": m["ml_FP"],
                        "tn": m["ml_TN"],
                        "fn": m["ml_FN"],
                    },
                "baseline": {
                        "tp": m["baseline_TP"],
                        "fp": m["baseline_FP"],
                        "tn": m["baseline_TN"],
                        "fn": m["baseline_FN"],
                    }
            },
            "prediction_distribution": {
                "baseline": {
                    "re_pct":   round(sum_bl_pred_re, 2),
                    "safe_pct": round(sum_bl_pred_safe, 2),
                },
                "ml": {
                    "re_pct":   round(sum_ml_pred_re, 2),
                    "safe_pct": round(sum_ml_pred_safe, 2),
                }
            }
        }
    #************************************************************************************************************
    def run(self, context):
        print("start test 6 ...", flush=True)

        baseline_result = self.tool_evaluation.create_baseline_result(context["payload"])

        m, label_distribution = self.load_input_test(context, baseline_result)

        print(f"\n  ── ML tool vs Baseline ──", flush=True)
        print(f"    tool: {m['ml_tool_id']}", flush=True)
        print(f"      TP:        ml={m['ml_TP']}  baseline={m['baseline_TP']}  delta={m['ml_TP'] - m['baseline_TP']}", flush=True)
        print(f"      FP:        ml={m['ml_FP']}  baseline={m['baseline_FP']}  delta={m['ml_FP'] - m['baseline_FP']}", flush=True)
        print(f"      TN:        ml={m['ml_TN']}  baseline={m['baseline_TN']}  delta={m['ml_TN'] - m['baseline_TN']}", flush=True)
        print(f"      FN:        ml={m['ml_FN']}  baseline={m['baseline_FN']}  delta={m['ml_FN'] - m['baseline_FN']}", flush=True)
        print(f"      accuracy:  ml={m['ml_accuracy']}  baseline={m['baseline_accuracy']}  delta={round(m['ml_accuracy']  - m['baseline_accuracy'],  4)}", flush=True)
        print(f"      precision: ml={m['ml_precision']}  baseline={m['baseline_precision']}  delta={round(m['ml_precision'] - m['baseline_precision'], 4)}", flush=True)
        print(f"      recall:    ml={m['ml_recall']}  baseline={m['baseline_recall']}  delta={round(m['ml_recall']    - m['baseline_recall'],    4)}", flush=True)
        print(f"      f1:        ml={m['ml_f1']}  baseline={m['baseline_f1']}  delta={round(m['ml_f1'] - m['baseline_f1'], 4)}", flush=True)

        result = self.compare(m)
        result["label_distribution"] = label_distribution

        assessment = self._assess(result["delta"])

        print(f"\n  ── Deltas ──", flush=True)
        for k, v in result["delta"].items():
            print(f"      delta_{k}: {round(v, 4)}", flush=True)

        print(f"\n  ── Confusion Matrix  ──", flush=True)
        print(f"      ML:       tp={result['confusion_matrix']['ml']['tp']}  fp={result['confusion_matrix']['ml']['fp']}  tn={result['confusion_matrix']['ml']['tn']}  fn={result['confusion_matrix']['ml']['fn']}", flush=True)
        print(f"      Baseline: tp={result['confusion_matrix']['baseline']['tp']}  fp={result['confusion_matrix']['baseline']['fp']}  tn={result['confusion_matrix']['baseline']['tn']}  fn={result['confusion_matrix']['baseline']['fn']}", flush=True)

        pd = result["prediction_distribution"]
        print(f"\n  ── Prediction Distribution (%) ──", flush=True)
        print(f"      {'':10s} {'RE':>8s} {'Safe':>8s}", flush=True)
        print(f"      {'ml':10s} {pd['ml']['re_pct']:>7.2f}% {pd['ml']['safe_pct']:>7.2f}%", flush=True)
        print(f"      {'baseline':10s} {pd['baseline']['re_pct']:>7.2f}% {pd['baseline']['safe_pct']:>7.2f}%", flush=True)
       

        ld = result["label_distribution"]
        print(f"\n  ── Label Distribution (ground truth) ──", flush=True)
        print(f"      {'':10s} {'count':>8s} {'%':>8s}", flush=True)
        print(f"      {'RE':10s} {ld['re_count']:>8d} {ld['re_pct']:>7.2f}%", flush=True)
        print(f"      {'Safe':10s} {ld['safe_count']:>8d} {ld['safe_pct']:>7.2f}%", flush=True)
        print(f"      {'total':10s} {ld['total']:>8d}", flush=True)

        print(f"\n  ── Assessment: {assessment} ──\n", flush=True)

        return {
            "test_result":     result,
            "test_assessment": assessment
        }