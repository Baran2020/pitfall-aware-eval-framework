# run.py
from .test_executor import TestExecutor

class TestAgentRunner:
    def __init__(self):
        self.executor = TestExecutor()

    def run_all(self, tests):
        results = []
        
        tests = sorted(tests, key=lambda t: t["exec_id"])

        for test in tests:
            result = self.executor.run_test(test)
            results.append(result)

        return results
