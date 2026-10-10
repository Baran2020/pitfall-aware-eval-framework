from test_base import TestBase
from tool_evaluation import ToolEvaluation


class Test7(TestBase):
    def __init__(self):
        self.tool_evaluation = ToolEvaluation()

    # ************************************************************************************************************
    def load_input_test(self, context):

        payload = context["payload"]  # {tool_id: {dataset_id: {dataset_name, metrics, prediction_eval}}}
        input_test = {}
        for tool_id, datasets in payload.items():
            input_test[tool_id] = {}
            for dataset_id, value in datasets.items():
                input_test[tool_id][dataset_id] = {
                    "dataset_name": value.get("dataset_name"),
                    "metrics": value["metrics"]
                }
        if not input_test:
            raise ValueError("Need at least 1 tool for evaluation")
        return input_test

    # ************************************************************************************************************
    def compare(self, input_test):
        result = {}
        metric_keys = [
            "tp", "fp", "tn", "fn",
            "tpr", "tnr", "fnr", "fpr",
            "accuracy", "precision", "recall", "f1", "specificity",
            "csi", "ssi", "faith", "pdif", "gs", "mcc", "gm", "kappa"
        ]
        for tool_id, datasets in input_test.items():
            result[tool_id] = {}
            for dataset_id, value in datasets.items():
                metrics = value["metrics"]
                result[tool_id][dataset_id] = {
                    "dataset_name": value.get("dataset_name"),
                    **{k: round(metrics.get(k, 0), 4) for k in metric_keys}
                }
        return result

    # ***************************************************************************************
    def is_pass(self, metrics):
        accuracy  = metrics.get("accuracy",  0)
        precision = metrics.get("precision", 0)
        recall    = metrics.get("recall",    0)
        f1        = metrics.get("f1",        0)

        csi   = metrics.get("csi",   0)
        ssi   = metrics.get("ssi",   0)
        faith = metrics.get("faith", 0)
        pdif  = metrics.get("pdif",  0)
        gs    = metrics.get("gs",    0)
        mcc   = metrics.get("mcc",   0)
        gm    = metrics.get("gm",    0)
        kappa = metrics.get("kappa", 0)

        passed = (
            accuracy  >= 0.7  and
            precision >= 0.5  and
            recall    >= 0.5  and
            f1        >= 0.5  and
            csi   >= 0.2  and
            ssi   >= 0.15 and
            faith >= 0.5  and
            pdif  <= 0.3  and
            gs    >= 0.1  and
            mcc   >= 0.25 and
            gm    >= 0.3  and
            kappa >= 0.2
        )
        return passed

    # ************************************************************************************************************
    def run(self, context):
        print("start test 7 ...", flush=True)
        input_test  = self.load_input_test(context)
        test_result = self.compare(input_test)

        assessment = "PASS"
        for tool_id, datasets in test_result.items():
            for dataset_id, metrics in datasets.items():
                ds_name = metrics.get("dataset_name", dataset_id)
                passed = self.is_pass(metrics)
                print(f"    tool={tool_id}  dataset={ds_name}  ->  {'PASS' if passed else 'FAIL'}", flush=True)
                print(f"      accuracy={metrics.get('accuracy')}  precision={metrics.get('precision')}  recall={metrics.get('recall')}  f1={metrics.get('f1')}", flush=True)
                print(f"      mcc={metrics.get('mcc')}  kappa={metrics.get('kappa')}  gm={metrics.get('gm')}  csi={metrics.get('csi')}", flush=True)
                if not passed:
                    assessment = "FAIL"

        print(f"\n  -- Test 7 assessment: {assessment} --\n", flush=True)

        return {
            "test_result":     test_result,
            "test_assessment": assessment
        }
    # ************************************************************************************************************