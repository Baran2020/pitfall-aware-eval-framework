import importlib.util
import sys
import os
from test_base import TestBase
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from tool_executor import ToolExecutor, STATIC_TOOLS
from tool_evaluation import ToolEvaluation
from dataset_evaluation import DatasetEvaluation



class TestExecutor:

    def __init__(self):
        self.dataset_evaluation = DatasetEvaluation()
        self.tool_evaluation = ToolEvaluation()
        self.tool_executor = ToolExecutor()
        self.cache = {}
    #**********************************************************************************************
    def execute_test(self, test, evaluation_result=None):
        print("start  execute_test function in test_executor.py ........................")  


        test_module_path = test["test_path"]
        if not os.path.exists(test_module_path):
            raise FileNotFoundError(f"{test_module_path} not found")

        module_name = os.path.splitext(os.path.basename(test_module_path))[0]

        spec = importlib.util.spec_from_file_location(module_name, test_module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)


        test_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and attr.__name__.startswith("Test"):
                test_class = attr
                break


        if not test_class:
            raise ValueError(f"No test class found in {test_module_path}")


        print(f" About to run: {test['test_name']}", flush=True)
        test_instance = test_class()

        if not hasattr(test_instance, "run"):
            raise NotImplementedError("Each test class must implement run() method")



        try:
            context_type = evaluation_result["type"]
            context_data = evaluation_result["data"]

            context = {
                    "type": context_type,
                    "payload": context_data
                }

            result = test_instance.run(context)
            print("TEST RAW OUTPUT:")


            test_output = {
                "test_id": test["test_id"],
                "test_name": test.get("test_name"),
                "test_type": "tool_based" if test.get("tool_run") else "dataset_based",
                "test_status": "success",
                "test_result": result["test_result"],          # dict (metrics)          
                "test_assessment": result["test_assessment"]     # PASS / FAIL
            }

        except Exception as e:
                print(f"[ERROR] execute_test failed: {e}")
                import traceback
                traceback.print_exc()
                test_output = {
                    "test_id": test["test_id"],
                    "test_name": test.get("test_name"),
                    "test_type": "tool_based" if test.get("tool_run") else "dataset_based",
                    "test_status": "error",
                    "test_result": {"error": str(e)},
                    "test_assessment": "FAIL",
                    "error": str(e)
                }
        print("end  execute_test function in test_executor.py ************************************")   
        return test_output

#**********************************************************************************************
    def invoke_tool_executor(self,test):
        print("start  invoke_tool_executor  function in test_executor.py ........................")


        # Find the ml tool's own tool_path in this test (if any) so static
        # tools (mythril/manticore/oyente) can be aligned to the exact same
        # held-out test split ml's train_test_split(mode="both") carved out,
        # instead of running on the full manifest.
        ml_tool_path = None
        for t in test["tools"]:
            if t.get("tool_name") not in STATIC_TOOLS:
                ml_tool_path = t.get("tool_path")
                break

        # ml must run first so its split.json exists on disk before any
        # static tool tries to read it.
        ordered_tools = sorted(
            test["tools"],
            key=lambda t: 1 if t.get("tool_name") in STATIC_TOOLS else 0
        )

        all_tool_results = []
        for tool in ordered_tools:
            for dataset in test["datasets"]:
                cache_key = (tool["tool_id"], dataset["dataset_id"])

                if cache_key in self.cache:
                    print(f"[CACHE] Using cached result for tool {tool['tool_id']} on dataset {dataset['dataset_id']}")
                    tool_result = self.cache[cache_key]

                else:
                    split_json_path = None
                    if tool.get("tool_name") in STATIC_TOOLS and ml_tool_path:
                        split_json_path = os.path.join(
                            ml_tool_path, f"{dataset['dataset_name']}_split.json"
                        )

                    tool_result  = self.tool_executor.run(
                        dataset_path = dataset["dataset_path"],
                        tool_path= tool["tool_path"],
                        dataset_id= dataset["dataset_id"],
                        tool_id= tool["tool_id"],
                        dataset_name=dataset["dataset_name"],
                        dataset_file=dataset["dataset_file"],
                        input_format=tool["input_format"],
                        input_type=dataset["input_type"],
                        tool_name=tool.get("tool_name"),
                        split_json_path=split_json_path
)


                    print(f"[ToolWrapper] executed tool {tool['tool_id']} on dataset {dataset['dataset_id']} for test {test['test_id']}")
                    self.cache[cache_key] = tool_result 
                all_tool_results.append({
                    "tool_id": tool["tool_id"],
                    "tool_name": tool.get("tool_name"),
                    "dataset_id": dataset["dataset_id"],
                    "dataset_name": dataset.get("dataset_name"),
                    "sample_predictions": tool_result
                })


        print("end  invoke_tool_executor  function in test_executor.py ***************************")

        return all_tool_results
    #**********************************************************************************************
    def run_tool(self, test):
        print("start  run_tool  function in test_executor.py ........................")  

        tool_run = test['tool_run']

        if tool_run  == True:
            print(f" tool_run detected as True -> invoking tool for {test.get('test_id')}")

            all_tool_result = self.invoke_tool_executor(test)


        else:
            print(f" tool_run is False -> skipping tool for {test.get('test_id')}")
            all_tool_result = []

        print("end run_tool  function in test_executor.py *************************")     
        return  all_tool_result 



#**********************************************************************************************
    def run_tests_group(self, tests_group):

        print("start  run_tests_group  function in test_executor.py ........................") 

        test_group_results = {
            "exec_id": tests_group[0]["exec_id"] if tests_group else None,
            "tests": []
        }

        dataset_based_tests = [t for t in tests_group if t.get("tool_run") == False]
        tool_based_tests    = [t for t in tests_group if t.get("tool_run") != False]

        # --------------------------------------------------
        # DATASET-BASED TESTS
        # --------------------------------------------------
        for test in dataset_based_tests:

            evaluation_results_list = []

            for dataset in test["datasets"]:
                eval_result = self.dataset_evaluation.run(dataset)
                print(f"result: dataset_id={eval_result.get('dataset_id')}, dataset_name={eval_result.get('dataset_name')}")

                evaluation_results_list.append({
                    "dataset_id": eval_result["dataset_id"],
                    "dataset_name": eval_result["dataset_name"],
                    "metrics": eval_result["metrics"]
                })

            packaged_eval = {}

            for item in evaluation_results_list:
                dataset_id = item["dataset_id"]

                packaged_eval[dataset_id] = {
                    "dataset_name": item["dataset_name"],
                    "metrics": item["metrics"]
                }

            test_result = self.execute_test(test, {
                "type": "dataset",
                "data": packaged_eval
            })

            test_group_results["tests"].append({
                "test_id": test["test_id"],
                "test_name": test.get("test_name"),
                "test_type": "dataset_based",
                "test_status": test_result.get("test_status", "success"),
                "test_result": test_result["test_result"],
                "test_assessment": test_result["test_assessment"],
                "tools": [],
                "tool_results": [],
                "sample_predictions": test_result.get("sample_predictions", []),
                "datasets": [
                    {"dataset_id": d.get("dataset_id"), "dataset_name": d.get("dataset_name")}
                    for d in test.get("datasets", [])
                ]
            })

        # --------------------------------------------------
        # TOOL-BASED TESTS
        # --------------------------------------------------
        if tool_based_tests:

            with ThreadPoolExecutor() as executor:
                tool_results_list = list(executor.map(self.run_tool, tool_based_tests))

            for test, tool_result in zip(tool_based_tests, tool_results_list):

                try:
                    evaluation_results_list = []

                    for item in tool_result:

                        eval_result = self.tool_evaluation.run(
                            item["sample_predictions"]
                        )

                        evaluation_results_list.append({
                            "tool_id": item["tool_id"],
                            "tool_name": item.get("tool_name"),
                            "dataset_id": item["dataset_id"],
                            "dataset_name": item.get("dataset_name"),
                            "metrics": eval_result["metrics"],
                            "prediction_eval": eval_result["tool_prediction"]
                        })

                    packaged_eval = {}

                    for item in evaluation_results_list:
                        tool_id = item["tool_id"]
                        dataset_id = item["dataset_id"]

                        if tool_id not in packaged_eval:
                            packaged_eval[tool_id] = {}

                        packaged_eval[tool_id][dataset_id] = {
                            "tool_name": item.get("tool_name"),
                            "dataset_name": item.get("dataset_name"), 
                            "metrics": item["metrics"],
                            "prediction_eval": item["prediction_eval"]
                        }

                    tool_results_built = []
                    sample_predictions_built = []

                    for item in evaluation_results_list:
                        tool_id = item["tool_id"]
                        dataset_id = item["dataset_id"]
                        m = item["metrics"]

                        tool_results_built.append({
                            "tool_id": tool_id,
                            "tool_name": item.get("tool_name", ""),
                            "dataset_id": dataset_id,
                            "dataset_name": item.get("dataset_name", ""),
                            "total_samples": len(item["prediction_eval"]),
                            "tp": m.get("tp"),
                            "fp": m.get("fp"),
                            "tn": m.get("tn"),
                            "fn": m.get("fn"),
                            "accuracy": m.get("accuracy"),
                            "precision": m.get("precision"),
                            "recall": m.get("recall"),
                            "f1": m.get("f1")
                        })

                        for sp in item["prediction_eval"]:
                            sample_predictions_built.append({
                                "dataset_id": dataset_id,
                                "id": sp.get("id"),
                                "split": sp.get("split"),
                                "predicted": sp.get("predicted"),
                                "label": sp.get("label"),
                                "status": sp.get("status")
                            })

                    # --------------------------------------------------
                    # RUN TEST
                    # --------------------------------------------------
                    test_result = self.execute_test(test, {
                        "type": "tool",
                        "data": packaged_eval
                    })

                    test_group_results["tests"].append({
                        "test_id": test["test_id"],
                        "test_name": test.get("test_name"),
                        "test_type": "tool_based",
                        "test_status": "success",
                        "test_result": test_result["test_result"],
                        "test_assessment": test_result["test_assessment"],
                        "tools": [
                            {
                                "tool_id": t.get("tool_id"),
                                "tool_name": t.get("tool_name")
                            }
                            for t in test.get("tools", [])
                        ],
                        "tool_results": tool_results_built,
                        "sample_predictions": sample_predictions_built,
                        "datasets": [
                            {
                                "dataset_id": d.get("dataset_id"),
                                "dataset_name": d.get("dataset_name")
                            }
                            for d in test.get("datasets", [])
                        ]
                    })

                except Exception as e:
                    test_group_results["tests"].append({
                        "test_id": test["test_id"],
                        "test_name": test.get("test_name"),
                        "test_type": "tool_based",
                        "test_status": "error",
                        "test_result": {"error": str(e)},
                        "test_assessment": "FAIL",
                        "sample_predictions": [],
                        "tool_results": [],
                        "tools": [
                            {"tool_id": t.get("tool_id"), "tool_name": t.get("tool_name")}
                            for t in test.get("tools", [])
                        ],
                        "datasets": test.get("datasets", [])
                    })

            print("Running group:", [t['test_id'] for t in tool_based_tests])

        print("end run_tests_group  function in test_executor.py *********************") 
        return test_group_results


#**********************************************************************************************
    def run_all_tests(self, tests, dataset_id_user=None):
        print("start  run_all_tests  function in test_executor.py ........................")  


        grouped = defaultdict(list)
        for test_id, test_data in tests.items():
            grouped[test_data["exec_id"]].append({
                "test_id": test_id,
                **test_data
            })

        all_results = []
        for exec_id in sorted(grouped.keys()):
            group = grouped[exec_id]

            if not group:
                continue  

            group_results = self.run_tests_group(group)
            all_results.append(group_results)


        print("end  run_all_tests  function in test_executor.py ***************************")  

        return all_results
  #**********************************************************************************************