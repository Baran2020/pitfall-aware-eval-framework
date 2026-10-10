from test_executor import TestExecutor
from test_report import ReportService
import metadataregistrar

class TestManager:
    #*********************************************************************************************
    def __init__(self):

        self.executor = TestExecutor()
        self.report_service = ReportService()
  
    #*********************************************************************************************
    def run(self, project_id, dataset_id_user):

        print("start  run function in test_manager.py ........................")  
        
        tests = metadataregistrar.fetch_tests_for_project(project_id)
        
        # 2. Execute all tests
        all_results = self.executor.run_all_tests(tests, dataset_id_user)
        results = [t for group in all_results for t in group["tests"]]

        # 3. Generate report (build + save metadata)
        result_report = self.report_service.report(project_id, results)

       
        print("end  run function in test_manager.py ***************************") 
        return result_report #result_test_agent

    #*********************************************************************************************


