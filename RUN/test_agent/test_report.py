import metadataregistrar


class ReportService:

    #***********************************************************

    def creat_report_inputs(self, project_id, test_results):

        input_test_report = []
        input_tool_overall_report = []
        input_tool_result_report = []
        input_sample_prediction_report = []
        input_final_report = []

        final_summary = {
            "project_id": project_id
        }

        test_index = 1

                    
       
        for test in test_results:    
            
            # =========================
            # TEST REPORT
            # =========================
            input_test_report.append({
                "project_id": project_id,
                "test_name": test.get("test_name"),
                "tool_used": [t.get("tool_name") for t in test.get("tools", [])],
                "dataset_used": [d.get("dataset_name") for d in test.get("datasets", [])],
                "test_id": test.get("test_id"),
                "status": test.get("test_status"),
                "test_result": test.get("test_result"),
                "test_assessment": test.get("test_assessment")
            })

            # =========================
            # TOOL OVERALL
            # =========================
            for tool in test.get("tools", []):
                for dataset in test.get("datasets", []):

                    execution_id = metadataregistrar.generate_execution_id(
                        project_id,
                        tool.get("tool_id"),
                        dataset.get("dataset_id")
                    )

                    input_tool_overall_report.append({
                        "project_id": project_id,
                        "execution_id": execution_id,
                        "test_name": test.get("test_name"),
                        "tool_name": tool.get("tool_name"),
                        "dataset_name": dataset.get("dataset_name"),
                        "test_id": test.get("test_id"),
                        "tool_id": tool.get("tool_id"),
                        "dataset_id": dataset.get("dataset_id")
                    })

            # =========================
            # TOOL RESULT
            # =========================
            for tr in test.get("tool_results", []):

                input_tool_result_report.append({
                    "project_id": project_id,
                    "execution_id": tr.get("execution_id"),
                    "tool_id": tr.get("tool_id"),
                    "tool_name": tr.get("tool_name"),
                    "dataset_id": tr.get("dataset_id"),
                    "dataset_name": tr.get("dataset_name"),
                    "total_samples": tr.get("total_samples"),

                    "metric_tp": tr.get("tp"),
                    "metric_fp": tr.get("fp"),
                    "metric_tn": tr.get("tn"),
                    "metric_fn": tr.get("fn"),

                    "metric_accuracy": tr.get("accuracy"),
                    "metric_precision": tr.get("precision"),
                    "metric_recall": tr.get("recall"),
                    "metric_f1": tr.get("f1")
                })

            # =========================
            # SAMPLE PREDICTION
            # =========================
            for i, sp in enumerate(test.get("sample_predictions", [])):

                sample_id = metadataregistrar.generate_sample_id(
                    project_id,
                    sp.get("dataset_id"),
                    sp.get("id")
                )

                input_sample_prediction_report.append({
                    "sample_id": sample_id,
                    "project_id": project_id,
                    "sample_name": sp.get("id"), 
                    "execution_sample_id": sp.get("execution_id"),
                    "split": sp.get("split"),
                    "predicted": sp.get("predicted"),
                    "label": sp.get("label"),
                    "status": sp.get("status")
                })

            # =========================
            # FINAL REPORT (aggregate)
            # =========================
            final_summary[test.get("test_name", f"test{test_index}")] = test.get("test_assessment")
            test_index += 1

        final_summary["final_result"] = "PASS" if all(
                t.get("test_assessment") == "PASS" for t in test_results
            ) else "FAIL"


            

        input_final_report.append(final_summary)
        input_result = {
                    "input_test_report": input_test_report,
                    "input_tool_overall_report": input_tool_overall_report,
                    "input_tool_result_report": input_tool_result_report,
                    "input_sample_prediction_report": input_sample_prediction_report,
                    "input_final_report": input_final_report
                }


        return input_result

    #*******************************************************************
 
    def report(self, project_id, test_results):
         
        metadataregistrar.clear_all_reports()

        inputs = self.creat_report_inputs(project_id, test_results)

        metadata_test_report= metadataregistrar.create_metadata_test_report( inputs["input_test_report"])

        metadata_tool_overall_report= metadataregistrar.create_metadata_tool_overall_report( inputs["input_tool_overall_report"])

        metadata_tool_result_report= metadataregistrar.create_metadata_tool_result_report(inputs["input_tool_result_report"] )

        metadata_sample_prediction_report= metadataregistrar.create_metadata_sample_prediction_report( inputs["input_sample_prediction_report"])


        metadata_final_report= metadataregistrar.create_metadata_final_report(inputs["input_final_report"] )   
        print(metadata_final_report)     

           #  ....................................................................................................................  

        for record in metadata_test_report:
            metadataregistrar.save_metadata_test_report(record)

        for record in metadata_tool_overall_report:
            metadataregistrar.save_metadata_tool_overall_report(record)

        for record in metadata_tool_result_report:
            metadataregistrar.save_metadata_tool_result_report(record)

        for record in metadata_sample_prediction_report:
            metadataregistrar.save_metadata_sample_prediction_report(record)
        print("end save_metadata_sample_prediction_report  ...")    

        for record in metadata_final_report:
            metadataregistrar.save_metadata_final_report(record)   
        '''      
        metadataregistrar.save_metadata_test_report(metadata_test_report)
        metadataregistrar.save_metadata_tool_overall_report(metadata_tool_result_report)
        metadataregistrar.save_metadata_tool_result_report(metadata_tool_result_report)
        metadataregistrar.save_metadata_sample_prediction_report(metadata_sample_prediction_report)
        metadataregistrar.save_metadata_final_report(metadata_final_report) 
        '''
        
        return {
    "report_id": metadata_test_report[0].get("test_id") if metadata_test_report else None,
    "status": "success"
}


        







