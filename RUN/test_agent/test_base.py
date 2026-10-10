class TestBase:
    '''
    def __init__(self, test_id: str, project_id: str, dataset_id: str, metadata: dict = None):
        self.test_id = test_id
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.metadata = metadata or {}
    
    def run(self, tool_result=None):
        
        raise NotImplementedError("Each test must implement its own run() method")
    '''
    
    def __init__(self):
        pass
    
    def run(self, context):
        raise NotImplementedError("Each test must implement its own run() method")