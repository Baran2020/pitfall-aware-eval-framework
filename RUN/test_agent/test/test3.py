from test_base import TestBase
from tool_evaluation import ToolEvaluation

class Test3(TestBase):

    def __init__(self):
    
        self.tool_evaluation=ToolEvaluation()

    
    #************************************************************************************************************
    def load_input_test(self, context):
        payload = context["payload"]
        grouped = {}
        for tool_id, datasets in payload.items():
            for dataset_id, value in datasets.items():
                grouped.setdefault(dataset_id, {})[tool_id] = value["metrics"]
        return grouped

 #************************************************************************************************************
    def _build_input_pair(self, grouped, user_key, p3_key):
        input_test = {}
        for tool_id in grouped[user_key].keys():
            user = grouped[user_key][tool_id]
            p3   = grouped[p3_key][tool_id]
            input_test[tool_id] = {
                "metrics_user_TP": user["tp"],   "metrics_P3_TP": p3["tp"],
                "metrics_user_FP": user["fp"],   "metrics_P3_FP": p3["fp"],
                "metrics_user_TN": user["tn"],   "metrics_P3_TN": p3["tn"],
                "metrics_user_FN": user["fn"],   "metrics_P3_FN": p3["fn"],

                "metrics_user_accuracy":  user["accuracy"],  "metrics_P3_accuracy":  p3["accuracy"],
                "metrics_user_precision": user["precision"], "metrics_P3_precision": p3["precision"],
                "metrics_user_recall":    user["recall"],    "metrics_P3_recall":    p3["recall"],
                "metrics_user_f1":        user["f1"],        "metrics_P3_f1":        p3["f1"],
            }
        return input_test

#************************************************************************************************************
    
    def compare(self, input_test: dict) -> dict:
        
        n = len(input_test)
        
        delta_TP = 0
        delta_FP = 0
        delta_TN = 0
        delta_FN = 0

        delta_accuracy = 0
        delta_precision = 0
        delta_recall = 0
        delta_f1 = 0

        
        for _, m in input_test.items():

            delta_TP += m["metrics_user_TP"] - m["metrics_P3_TP"]
            delta_FP += m["metrics_user_FP"] - m["metrics_P3_FP"]
            delta_TN += m["metrics_user_TN"] - m["metrics_P3_TN"]
            delta_FN += m["metrics_user_FN"] - m["metrics_P3_FN"]

            delta_accuracy += m["metrics_user_accuracy"] - m["metrics_P3_accuracy"]
            delta_precision += m["metrics_user_precision"] - m["metrics_P3_precision"]
            delta_recall += m["metrics_user_recall"] - m["metrics_P3_recall"]
            delta_f1 += m["metrics_user_f1"] - m["metrics_P3_f1"]

        if n > 0:
            return {
                "delta_tp": delta_TP / n,
                "delta_fp": delta_FP / n,
                "delta_tn": delta_TN / n,
                "delta_fn": delta_FN / n,
                "delta_accuracy": round(delta_accuracy / n,4),
                "delta_precision": round(delta_precision / n,4),
                "delta_recall":round( delta_recall / n,4),
                "delta_f1": round(delta_f1 / n ,4)
            }

        return {
            "delta_tp": 0,
            "delta_fp": 0,
            "delta_tn": 0,
            "delta_fn": 0,
            "delta_accuracy": 0,
            "delta_precision": 0,
            "delta_recall": 0,
            "delta_f1": 0
        }
    #************************************************************************************************************
    @staticmethod
    def _assess(result: dict) -> str:
        if (
            result["delta_tp"]        < 0 or
            result["delta_fp"]        > 0 or
            result["delta_accuracy"]  < 0 or
            result["delta_precision"] < 0 or
            result["delta_recall"]    < 0 or
            result["delta_f1"]        < 0
        ):
            return "FAIL"
        return "PASS"    
    #************************************************************************************************************
    '''def run_pair(self, grouped, user_key, p3_key):
        metrics = self._build_input_pair(grouped, user_key, p3_key)
        result  = self.compare(metrics)
        return {
            "test_result":     result,
            "test_assessment": self._assess(result),
        }
    '''

    def run_pair(self, grouped, user_key, p3_key):
        metrics = self._build_input_pair(grouped, user_key, p3_key)
        
        print(f"\n  ── Comparing: USER={user_key}  vs  P3={p3_key} ──", flush=True)
        for tool_id, m in metrics.items():
            print(f"    tool: {tool_id}", flush=True)
            print(f"      TP:        user={m['metrics_user_TP']}  p3={m['metrics_P3_TP']}  delta={m['metrics_user_TP'] - m['metrics_P3_TP']}", flush=True)
            print(f"      FP:        user={m['metrics_user_FP']}  p3={m['metrics_P3_FP']}  delta={m['metrics_user_FP'] - m['metrics_P3_FP']}", flush=True)
            print(f"      TN:        user={m['metrics_user_TN']}  p3={m['metrics_P3_TN']}  delta={m['metrics_user_TN'] - m['metrics_P3_TN']}", flush=True)
            print(f"      FN:        user={m['metrics_user_FN']}  p3={m['metrics_P3_FN']}  delta={m['metrics_user_FN'] - m['metrics_P3_FN']}", flush=True)
            print(f"      accuracy:  user={m['metrics_user_accuracy']}  p3={m['metrics_P3_accuracy']}  delta={round(m['metrics_user_accuracy'] - m['metrics_P3_accuracy'], 4)}", flush=True)
            print(f"      precision: user={m['metrics_user_precision']}  p3={m['metrics_P3_precision']}  delta={round(m['metrics_user_precision'] - m['metrics_P3_precision'], 4)}", flush=True)
            print(f"      recall:    user={m['metrics_user_recall']}  p3={m['metrics_P3_recall']}  delta={round(m['metrics_user_recall'] - m['metrics_P3_recall'], 4)}", flush=True)
            print(f"      f1:        user={m['metrics_user_f1']}  p3={m['metrics_P3_f1']}  delta={round(m['metrics_user_f1'] - m['metrics_P3_f1'], 4)}", flush=True)

        result = self.compare(metrics)

        print(f"\n  ── Average deltas ({user_key} vs {p3_key}) ──", flush=True)
        for k, v in result.items():
            print(f"      {k}: {round(v, 4)}", flush=True)

        assessment = self._assess(result)
        print(f"  ── Assessment: {assessment} ──\n", flush=True)

        return {
            "test_result":     result,
            "test_assessment": assessment,
        }    
        
    #************************************************************************************************************
    def run(self, context):

        print("start test 3 ...", flush=True)
        grouped = self.load_input_test(context)
        dataset_keys = list(grouped.keys())

        print(f"  dataset keys: {dataset_keys}", flush=True)

    
        if len(dataset_keys) < 3:
            raise ValueError(
                f"Test3 needs exactly 3 datasets [user, p3_min, p3_max], "
                f"got {len(dataset_keys)}: {dataset_keys}")

        USER_KEY   = dataset_keys[0]
        P3_MIN_KEY = dataset_keys[1]
        P3_MAX_KEY = dataset_keys[2]

        print(f"  USER_KEY:   {USER_KEY}", flush=True)
        print(f"  P3_MIN_KEY: {P3_MIN_KEY}", flush=True)
        print(f"  P3_MAX_KEY: {P3_MAX_KEY}", flush=True)

        result_vs_min = self.run_pair(grouped, USER_KEY, P3_MIN_KEY)
        result_vs_max = self.run_pair(grouped, USER_KEY, P3_MAX_KEY)



        print(f"  vs_min → {result_vs_min['test_assessment']}", flush=True)
        print(f"  vs_max → {result_vs_max['test_assessment']}", flush=True)

        overall_assessment = (
            "FAIL"
            if result_vs_min["test_assessment"] == "FAIL" or result_vs_max["test_assessment"] == "FAIL"
            else "PASS"
            )

        return {
            "test_result": {
                "vs_min": result_vs_min["test_result"],
                "vs_max": result_vs_max["test_result"]
            },
            "test_assessment": overall_assessment
        }


        #************************************************************************************************************
    
