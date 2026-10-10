class ToolEvaluation:

    # *********************************************************************************************
    def __init__(self, positive_label=1):

        self.positive_label = positive_label
    # *********************************************************************************************

    def create_baseline_result(self, payload, static_tool_names=("manticore", "mythril", "oyente")):
        """
        Build a baseline result per dataset by aggregating predictions
        from static tools (e.g. manticore, mythril, oyente) via majority vote.

        payload: {tool_id: {dataset_id: {tool_name, metrics, prediction_eval}}}

        Returns: {dataset_id: {"metrics": ..., "prediction_eval": ...}}
                 Only includes datasets where at least 2 static tools have results.
        """
        static_by_dataset = {}  # dataset_id -> {"preds": [...], "names": [...]}

        for tool_id, datasets in payload.items():
            for dataset_id, value in datasets.items():
                tool_name = value.get("tool_name")
                if tool_name in static_tool_names:
                    static_by_dataset.setdefault(dataset_id, {"preds": [], "names": []})
                    static_by_dataset[dataset_id]["preds"].append(value["prediction_eval"])
                    static_by_dataset[dataset_id]["names"].append(tool_name)

        baseline_by_dataset = {}

        for dataset_id, data in static_by_dataset.items():
            if len(data["preds"]) < 2:
                # Less than 2 static tools -> no meaningful baseline can be built
                continue

            baseline_preds = self.aggregate_baseline(
                data["preds"], tool_names=data["names"]
            )
            baseline_eval = self.run(baseline_preds)

            baseline_by_dataset[dataset_id] = {
                "metrics": baseline_eval["metrics"],
                "prediction_eval": baseline_eval["tool_prediction"]
            }

        return baseline_by_dataset

    #********************************************************************************************

    def aggregate_baseline(self, tool_results_list, tool_names=None):
        from collections import defaultdict
        votes    = defaultdict(list)
        labels   = {}
        per_tool = defaultdict(dict)

        for i, tool_result in enumerate(tool_results_list):
            label = tool_names[i] if tool_names and i < len(tool_names) else f"tool_{i}"

            for item in tool_result:
                sample_id = item["id"]
                pred = item["predicted"]
                per_tool[sample_id][label] = pred
                if pred is not None:
                    votes[sample_id].append(pred)
                if sample_id not in labels:
                    labels[sample_id] = item.get("label")

        print(f"    tools: {' | '.join(tool_names or [])}", flush=True)

        baseline = []
        for sample_id, preds in votes.items():
            if len(preds) < 2:
                continue
            agreed = 1 if sum(preds) > len(preds) / 2 else 0

            tool_preds_str = "  ".join(
                f"{tname}={pred}"
                for tname, pred in per_tool[sample_id].items()
            )
            print(
                f"    sample {sample_id}: {tool_preds_str}  ->  baseline={agreed}  label={labels[sample_id]}",
                flush=True
            )

            baseline.append({
                "id":        sample_id,
                "predicted": agreed,
                "label":     labels[sample_id],
                "split":     "test"
            })

        return baseline

    # *********************************************************************************************
    def compute_confusion_matrix(self, sample_predictions):

        tp = fp = tn = fn = 0

        for item in sample_predictions:

            label = item.get("label")
            predicted = item.get("predicted")

            if (
                label == self.positive_label and
                predicted == self.positive_label
            ):
                tp += 1

            elif (
                label != self.positive_label and
                predicted == self.positive_label
            ):
                fp += 1

            elif (
                label != self.positive_label and
                predicted != self.positive_label
            ):
                tn += 1

            elif (
                label == self.positive_label and
                predicted != self.positive_label
            ):
                fn += 1

        return {
            "tp": round(tp,   4),
            "fp": round(fp,   4),
            "tn": round(tn,   4),
            "fn": round(fn,   4),
        }

    # *********************************************************************************************
    def compute_rate_metrics(self, tp, fp, tn, fn):

        tpr = tp / (tp + fn) if (tp + fn) else 0
        tnr = tn / (tn + fp) if (tn + fp) else 0
        fnr = fn / (fn + tp) if (fn + tp) else 0
        fpr = fp / (fp + tn) if (fp + tn) else 0

        return {
            "tpr": round(tpr, 4),
            "tnr": round(tnr, 4),
            "fnr": round(fnr, 4),
            "fpr": round(fpr, 4)
        }

    # *********************************************************************************************
    def compute_classification_metrics(self, tp, fp, tn, fn):

        total = tp + fp + tn + fn

        accuracy = (tp + tn) / total if total else 0
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0
        )
        specificity = tn / (tn + fp) if (tn + fp) else 0

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "specificity": round(specificity, 4)
        }

    # *********************************************************************************************
    def compute_extended_metrics(self, tp, fp, tn, fn):

        total = tp + fp + tn + fn

        csi = tp / (tp + fp + fn) if (tp + fp + fn) else 0
        ssi = tp / (tp + 2*fp + 2*fn) if (tp + 2*fp + 2*fn) else 0
        faith = (tp + 0.5*tn) / total if total else 0
        pdif = (4 * fp * fn) / (total ** 2) if total else 0

        gs_denom = (fn + fp)*(tp + fp + fn + tn) + (tp*tn - fp*fn)
        gs = (tp*tn - fp*fn) / gs_denom if gs_denom else 0

        mcc_denom = ((fp + tp) * (fn + tp) * (tn + fp) * (tn + fn)) ** 0.5
        mcc = (tp*tn - fp*fn) / mcc_denom if mcc_denom else 0

        tpr = tp / (tp + fn) if (tp + fn) else 0
        tnr = tn / (tn + fp) if (tn + fp) else 0
        gm  = (tpr * tnr) ** 0.5

        numerator = 2 * (tp*tn - fp*fn)
        denominator = ((tp + fp) * (fp + tn)) + ((tp + fn) * (fn + tn))
        kappa = numerator / denominator if denominator else 0

        return {
            "csi":   round(csi,   4),
            "ssi":   round(ssi,   4),
            "faith": round(faith, 4),
            "pdif":  round(pdif,  4),
            "gs":    round(gs,    4),
            "mcc":   round(mcc,   4),
            "gm":    round(gm,    4),
            "kappa": round(kappa, 4),
        }

    # *********************************************************************************************
    def run(self, tool_result_prediction):

        print("start run function in tool_evaluation.py ***************************")

        sample_predictions = tool_result_prediction if isinstance(tool_result_prediction, list) else tool_result_prediction.get("sample_predictions", [])

        # ------------------------------------------------------------------
        confusion_metrics = self.compute_confusion_matrix(
            sample_predictions
        )

        # ------------------------------------------------------------------
        rate_metrics = self.compute_rate_metrics(
            confusion_metrics["tp"],
            confusion_metrics["fp"],
            confusion_metrics["tn"],
            confusion_metrics["fn"]
        )

        # ------------------------------------------------------------------
        classification_metrics = (
            self.compute_classification_metrics(
                confusion_metrics["tp"],
                confusion_metrics["fp"],
                confusion_metrics["tn"],
                confusion_metrics["fn"]
            )
        )

        # ------------------------------------------------------------------
        extended_metrics = self.compute_extended_metrics(
            confusion_metrics["tp"],
            confusion_metrics["fp"],
            confusion_metrics["tn"],
            confusion_metrics["fn"]
        )

        # ------------------------------------------------------------------
        metrics = {
            **confusion_metrics,
            **rate_metrics,
            **classification_metrics,
            **extended_metrics,
        }

        # ------------------------------------------------------------------
        tool_prediction = []

        for item in sample_predictions:
            tool_prediction.append({
                "id": item["id"],
                "label": item["label"],
                "predicted": item["predicted"],
                "split": item.get("split"),
                "status": item["label"] == item["predicted"]
            })

        evaluation_result = {
            "metrics": metrics,
            "tool_prediction": tool_prediction
        }

        print("end run function in tool_evaluation.py ***************************")

        return evaluation_result