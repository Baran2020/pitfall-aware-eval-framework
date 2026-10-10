from test_base import TestBase
from tool_evaluation import ToolEvaluation

class Test4(TestBase):

    def __init__(self):
        self.tool_evaluation = ToolEvaluation()

    # ************************************************************************************************************
    def _find_tool_dataset_by_name(self, payload, target_name):
        """
        payload structure: {tool_id: {dataset_id: {dataset_name, metrics, ...}}}
        Returns (tool_id, dataset_id, value) where value["dataset_name"] == target_name
        """
        for tool_id, datasets in payload.items():
            for dataset_id, value in datasets.items():
                if value.get("dataset_name") == target_name:
                    return tool_id, dataset_id, value
        available = [
            v.get("dataset_name")
            for datasets in payload.values()
            for v in datasets.values()
        ]
        raise ValueError(f"No dataset with name '{target_name}' found. Available: {available}")

    # ************************************************************************************************************
    def load_input_test(self, context):

        payload = context["payload"]  # ← {tool_id: {dataset_id: {dataset_name, metrics, prediction_eval}}}

        tool_id_user, dataset_id_user, value_user = self._find_tool_dataset_by_name(payload, "user")
        tool_id_p4,   dataset_id_p4,   value_p4   = self._find_tool_dataset_by_name(payload, "P4_obfuscated")

        user = value_user["metrics"]
        p4   = value_p4["metrics"]

        tool_metrics_pair = {
            "metrics_user_TP": user["tp"],
            "metrics_user_FP": user["fp"],
            "metrics_user_TN": user["tn"],
            "metrics_user_FN": user["fn"],

            "metrics_P4_TP": p4["tp"],
            "metrics_P4_FP": p4["fp"],
            "metrics_P4_TN": p4["tn"],
            "metrics_P4_FN": p4["fn"],

            "metrics_user_accuracy":  user["accuracy"],
            "metrics_user_precision": user["precision"],
            "metrics_user_recall":    user["recall"],
            "metrics_user_f1":        user["f1"],

            "metrics_P4_accuracy":  p4["accuracy"],
            "metrics_P4_precision": p4["precision"],
            "metrics_P4_recall":    p4["recall"],
            "metrics_P4_f1":        p4["f1"]
        }

        print(f"\n  ── Comparing for test 4: USER={dataset_id_user}  vs  P4={dataset_id_p4} ──", flush=True)
        print(f"    tool: {tool_id_user}", flush=True)
        m = tool_metrics_pair
        print(f"      TP:        user={m['metrics_user_TP']}  p4={m['metrics_P4_TP']}  delta={m['metrics_user_TP'] - m['metrics_P4_TP']}", flush=True)
        print(f"      FP:        user={m['metrics_user_FP']}  p4={m['metrics_P4_FP']}  delta={m['metrics_user_FP'] - m['metrics_P4_FP']}", flush=True)
        print(f"      TN:        user={m['metrics_user_TN']}  p4={m['metrics_P4_TN']}  delta={m['metrics_user_TN'] - m['metrics_P4_TN']}", flush=True)
        print(f"      FN:        user={m['metrics_user_FN']}  p4={m['metrics_P4_FN']}  delta={m['metrics_user_FN'] - m['metrics_P4_FN']}", flush=True)
        print(f"      accuracy:  user={m['metrics_user_accuracy']}  p4={m['metrics_P4_accuracy']}  delta={round(m['metrics_user_accuracy']  - m['metrics_P4_accuracy'],  4)}", flush=True)
        print(f"      precision: user={m['metrics_user_precision']}  p4={m['metrics_P4_precision']}  delta={round(m['metrics_user_precision'] - m['metrics_P4_precision'], 4)}", flush=True)
        print(f"      recall:    user={m['metrics_user_recall']}  p4={m['metrics_P4_recall']}  delta={round(m['metrics_user_recall']    - m['metrics_P4_recall'],    4)}", flush=True)
        print(f"      f1:        user={m['metrics_user_f1']}  p4={m['metrics_P4_f1']}  delta={round(m['metrics_user_f1']        - m['metrics_P4_f1'],        4)}", flush=True)

        return tool_metrics_pair

    # ************************************************************************************************************
    def compare(self, tool_metrics_pair):

        m = tool_metrics_pair

        delta_TP        = m["metrics_user_TP"]        - m["metrics_P4_TP"]
        delta_FP        = m["metrics_user_FP"]        - m["metrics_P4_FP"]
        delta_TN        = m["metrics_user_TN"]        - m["metrics_P4_TN"]
        delta_FN        = m["metrics_user_FN"]        - m["metrics_P4_FN"]
        delta_accuracy  = m["metrics_user_accuracy"]  - m["metrics_P4_accuracy"]
        delta_precision = m["metrics_user_precision"] - m["metrics_P4_precision"]
        delta_recall    = m["metrics_user_recall"]    - m["metrics_P4_recall"]
        delta_f1        = m["metrics_user_f1"]        - m["metrics_P4_f1"]

        print(f"\n  ── Delta results ──", flush=True)
        print(f"      delta_TP:        {delta_TP}", flush=True)
        print(f"      delta_FP:        {delta_FP}", flush=True)
        print(f"      delta_TN:        {delta_TN}", flush=True)
        print(f"      delta_FN:        {delta_FN}", flush=True)
        print(f"      delta_accuracy:  {round(delta_accuracy,  4)}", flush=True)
        print(f"      delta_precision: {round(delta_precision, 4)}", flush=True)
        print(f"      delta_recall:    {round(delta_recall,    4)}", flush=True)
        print(f"      delta_f1:        {round(delta_f1,        4)}", flush=True)

        return {
            "delta_tp":        delta_TP,
            "delta_fp":        delta_FP,
            "delta_tn":        delta_TN,
            "delta_fn":        delta_FN,
            "delta_accuracy":  delta_accuracy,
            "delta_precision": delta_precision,
            "delta_recall":    delta_recall,
            "delta_f1":        delta_f1,
        }

    # ************************************************************************************************************
    def run(self, context):

        print("start test 4 ...", flush=True)

        metrics        = self.load_input_test(context)
        test_result_p4 = self.compare(metrics)

        result = test_result_p4

        if (
            result["delta_tp"] < 0 or
            result["delta_fp"] > 0 or
            #result["delta_tn"] < 0 or
            result["delta_accuracy"]  < 0 or
            result["delta_precision"] < 0 or
            result["delta_recall"]    < 0 or
            result["delta_f1"]        < 0
        ):
            assessment = "FAIL"
        else:
            assessment = "PASS"

        print(f"\n  ── Test 4 assessment: {assessment} ──\n", flush=True)

        return {
            "test_result":     result,
            "test_assessment": assessment
        }
    # ************************************************************************************************************