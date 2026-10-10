import os
from datetime import datetime
import shutil
import uuid
import pandas as pd
import hashlib
from collections import defaultdict 
import sys
import re
from config.report_names import ReportNames
sys.path.append(r"/mnt/f/LISTTOOL/Framework/RUN/test_agent") 



DATA_DIR = "/mnt/f/LISTTOOL/Framework/RUN/metadata_csv"
REPORT_DIR = "/mnt/f/LISTTOOL/Framework/RUN/metadata_csv/Report"
#************************************************
def append_row(df, row):
    """Append a row (dict / Series / single-row DataFrame) to df safely."""
    if isinstance(row, pd.DataFrame):
        rows = row.to_dict("records")
    elif isinstance(row, pd.Series):
        rows = [row.to_dict()]
    else:
        rows = [row]

    if df.empty and len(df.columns) == 0:
        return pd.DataFrame(rows)

    for r in rows:
        df.loc[len(df)] = r
    return df

#*************************************************************************************************************
def clear_all_reports():
    for report_name in [ReportNames.TEST, ReportNames.TOOL_OVERALL,
                        ReportNames.TOOL_RESULT, ReportNames.SAMPLE, ReportNames.FINAL]:
        path = os.path.join(REPORT_DIR, report_name)
        if os.path.exists(path):
            os.remove(path)
    print("[CLEARED] All reports")

#*****************************************************************************************************************
def save_report_csv(df, file_name):
    path = os.path.join(REPORT_DIR, file_name)
    os.makedirs(REPORT_DIR, exist_ok=True)
    df.to_csv(path, index=False)
#***************************************************************************************************************
def load_report_csv(file_name):
    path = os.path.join(REPORT_DIR, file_name)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)
#***************************************************************************************************************
def load_csv(file_name):
    path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(path):
        return pd.DataFrame()  # empty df if not exist
    return pd.read_csv(path)
#***************************************************************************************************************
def save_csv(df, file_name):
    path = os.path.join(DATA_DIR, file_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(path, index=False)
#****************************************************************************************************************
def generate_execution_id(project_id,tool_id,dataset_id) -> str:
    print("start generate_execution_id function in metadataregistrar.py ........................")  

    execution_id=f"{project_id}|{tool_id}|{dataset_id}"

    #print("end generate_execution_id  function in metadataregistrar.py ************************************ ")
    return execution_id
   
 #******************************************************************************************************************
def generate_sample_id(project_id,dataset_id, index) -> str:
    #print("start generate_sample_id function in metadataregistrar.py ........................")  

    sample_id=f"{project_id}|{dataset_id}|S{index}"

    #print("end generate_sample_id  function in metadataregistrar.py ************************************ ")
    return sample_id

#****************************************************************************************************************
def create_metadata_test_report( input_test_report):
    print("start create_metadata_test_report function in metadataregistrar.py ........................")  


    metadata_test_report = []

    for r in input_test_report:

        metadata_test_report.append({
            "project_id": r.get("project_id"),
            "test_name": r.get("test_name"),
            "tool_used": r.get("tool_used"),
            "dataset_used": r.get("dataset_used"),
            "test_id": r.get("test_id"),
            "status": r.get("status"),
            "test_assessment": r.get("test_assessment"),
            "test_result": r.get("test_result")



            #"tool_id": r.get("tool_id"),
            #"dataset_id": r.get("dataset_id"),

        })
    

    print("end create_metadata_test_report function in metadataregistrar.py  ************************************ ")
    return metadata_test_report

#****************************************************************************************************************
def create_metadata_tool_overall_report( input_tool_overall_report):
    print("start create_metadata_tool_overall_report function in metadataregistrar.py ........................")  


    metadata_tool_overall_report = []

    for r in input_tool_overall_report:

        metadata_tool_overall_report.append({
            "project_id": r.get("project_id"),
            "execution_id": r.get("execution_id"),
            "test_name": r.get("test_name"),
            "tool_name": r.get("tool_name"),
            "dataset_name": r.get("dataset_name"),
            "test_id": r.get("test_id"),
            "tool_id": r.get("tool_id"),
            "dataset_id": r.get("dataset_id")

        })
    

    print("end create_metadata_tool_overall_report function in metadataregistrar.py  ************************************ ")
    return metadata_tool_overall_report


#****************************************************************************************************************
def create_metadata_tool_result_report( input_tool_result_report):
    print("start create_metadata_tool_result_report function in metadataregistrar.py ........................")  


    metadata_tool_result_report = []

    for r in input_tool_result_report:

        metadata_tool_result_report.append({

            "project_id": r.get("project_id"),
            "execution_id": r.get("execution_id"),

            "tool_id": r.get("tool_id"),
            "tool_name": r.get("tool_name"),

            "dataset_id": r.get("dataset_id"),
            "dataset_name": r.get("dataset_name"),

            "total_samples": r.get("total_samples"),

            "metric_tp": r.get("metric_tp"),
            "metric_fp": r.get("metric_fp"),
            "metric_tn": r.get("metric_tn"),
            "metric_fn": r.get("metric_fn"),

            "metric_accuracy": r.get("metric_accuracy"),
            "metric_precision": r.get("metric_precision"),
            "metric_recall": r.get("metric_recall"),
            "metric_f1": r.get("metric_f1")
        })

    print("end create_metadata_tool_result_report function in metadataregistrar.py  ************************************ ")
    return metadata_tool_result_report
#****************************************************************************************************************
def create_metadata_sample_prediction_report( input_sample_prediction_report):
    print("start create_metadata_sample_prediction_report function in metadataregistrar.py ........................")  


    metadata_sample_prediction_report = []

    for r in input_sample_prediction_report:

        metadata_sample_prediction_report.append({
           
            "sample_id": r.get("sample_id"),
            "project_id": r.get("project_id"),
            "sample_name": r.get("sample_name"),
            "execution_sample_id": r.get("execution_sample_id"),
            "split": r.get("split"),
            "predicted": r.get("predicted"),
            "label": r.get("label"),
            "status": r.get("status")
        })

    

    print("end create_metadata_sample_prediction_report function in metadataregistrar.py  ************************************ ")
    return metadata_sample_prediction_report

#****************************************************************************************************************
def create_metadata_final_report( input_final_report):
    print("start create_metadata_finall_report function in metadataregistrar.py ........................")  


    metadata_final_report = []

    for r in input_final_report:

        metadata_final_report.append({
           
            "project_id": r.get("project_id"),

            "test1": r.get("test1"),
            "test2": r.get("test2"),
            "test3": r.get("test3"),
            "test4": r.get("test4"),
            "test5": r.get("test5"),
            "test6": r.get("test6"),
            "test7": r.get("test7"),
            "test8": r.get("test8"),
            "final_result":r.get("final_result")
                                             })

    

    print("end create_metadata_final_report function in metadataregistrar.py  ************************************ ")
    return metadata_final_report
#****************************************************************************************************************
def save_metadata_test_report(metadata: dict):
    print("start save_metadata_test_report function in metadataregistrar.py ........................")
       
    project_id = metadata["project_id"]
    test_name = metadata["test_name"]
    tool_used = metadata["tool_used"]
    dataset_used = metadata["dataset_used"]
    test_id = metadata["test_id"]
    status = metadata["status"]
    test_result = metadata["test_result"]
    test_assessment=metadata["test_assessment"]


    # tool_id = metadata["tool_id"]
    #dataset_id = metadata["dataset_id"]
    
    df = load_report_csv(ReportNames.TEST)

    '''if not df.empty and "project_id" in df.columns:
        duplicate = df[
        (df["project_id"] == project_id) &
        (df["test_id"] == test_id)
              ]
    #    if not duplicate.empty:
    '''
    
    #if not df.empty and test_id in df["test_id"].values:
      # raise ValueError(f"test_id {test_id} already exists in test_report!")
    if not df.empty and test_id in df["test_id"].values:
       df = df[df["test_id"] != test_id]  

    new_row = pd.DataFrame([{
        "project_id": project_id,
        "test_name":test_name,
        "tool_used": tool_used,
        "dataset_used": dataset_used,
        "test_id":test_id,
        "status":status,
        "test_assessment": test_assessment,
        "test_result":test_result

        #"tool_id":tool_id,
        #"dataset_id":dataset_id,
        }])

    df = append_row(df, new_row)
    save_report_csv(df, ReportNames.TEST)
    print("end save_metadata_test_report function in metadataregistrar.py ************************************")


#*****************************************************************************

def save_metadata_tool_overall_report(metadata: dict):
    print("start save_metadata_tool_overall_report function in metadataregistrar.py ........................")

       
    project_id = metadata["project_id"]
    execution_id = metadata["execution_id"]
    test_name = metadata["test_name"]
    tool_name = metadata["tool_name"]
    dataset_name = metadata["dataset_name"]
    test_id = metadata["test_id"]
    tool_id = metadata["tool_id"]
    dataset_id = metadata["dataset_id"]
    
    
    
    df = load_report_csv(ReportNames.TOOL_OVERALL)

    
    #if not df.empty and execution_id in df["execution_id"].values:
        #raise ValueError(f"execution_id {execution_id} already exists in tool_overall_report!")
    if not df.empty and execution_id in df["execution_id"].values:
       df = df[df["execution_id"] != execution_id]

    new_row = pd.DataFrame([{
        "project_id": project_id,
        "execution_id":execution_id,
        "test_name":test_name,
        "tool_name": tool_name,
        "dataset_name": dataset_name,
        "test_id":test_id,
        "tool_id":tool_id,
        "dataset_id":dataset_id
        
        }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_report_csv(df, ReportNames.TOOL_OVERALL)
    print("end save_metadata_tool_overall_report function in metadataregistrar.py ************************************")


#****************************************************************************************************************
def save_metadata_tool_result_report(metadata: dict):
    print("start save_metadata_tool_result_report function in metadataregistrar.py ........................")

    project_id = metadata["project_id"]
    execution_id = metadata["execution_id"]

    tool_id = metadata["tool_id"]
    tool_name = metadata["tool_name"]

    dataset_id = metadata["dataset_id"]
    dataset_name = metadata["dataset_name"]

    total_samples = metadata["total_samples"]

    metric_tp = metadata["metric_tp"]
    metric_fp = metadata["metric_fp"]
    metric_tn = metadata["metric_tn"]
    metric_fn = metadata["metric_fn"]

    metric_accuracy = metadata["metric_accuracy"]
    metric_precision = metadata["metric_precision"]
    metric_recall = metadata["metric_recall"]
    metric_f1 = metadata["metric_f1"]

    df = load_report_csv( ReportNames.TOOL_RESULT)

    
    #if not df.empty and execution_id in df["execution_id"].values:
        #raise ValueError(f"Execution ID {execution_id} already exists in tool_result_report!")
    if not df.empty and execution_id in df["execution_id"].values:
       df = df[df["execution_id"] != execution_id]

    new_row = pd.DataFrame([{
        "project_id": project_id,
        "execution_id": execution_id,

        "tool_id": tool_id,
        "tool_name": tool_name,

        "dataset_id": dataset_id,
        "dataset_name": dataset_name,

        "total_samples": total_samples,

        "metric_tp": metric_tp,
        "metric_fp": metric_fp,
        "metric_tn": metric_tn,
        "metric_fn": metric_fn,

        "metric_accuracy": metric_accuracy,
        "metric_precision": metric_precision,
        "metric_recall": metric_recall,
        "metric_f1": metric_f1
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_report_csv(df, ReportNames.TOOL_RESULT)

    print("end save_metadata_tool_result_report function in metadataregistrar.py ************************************")


#****************************************************************************************************************

def save_metadata_sample_prediction_report(metadata: dict):
    #print("start save_metadata_sample_prediction_report function ...")

    sample_id = metadata["sample_id"]
    project_id =  metadata["project_id"]
    sample_name=metadata["sample_name"]
    execution_sample_id= metadata["execution_sample_id"]
    split = metadata["split"]
    predicted=metadata["predicted"]
    label = metadata["label"]
    status = metadata["status"]

    df = load_report_csv(ReportNames.SAMPLE)

    # check duplicate 
    if not df.empty and "sample_id" in df.columns:
        duplicate = df[
        (df["sample_id"] == sample_id) &
        (df["execution_sample_id"] == execution_sample_id)
    ]

        if not duplicate.empty:
            df = df[~((df["sample_id"] == sample_id) & (df["execution_sample_id"] == execution_sample_id))]
         
        #if not duplicate.empty:
            #raise ValueError(f"Sample {sample_id} with execution {execution_id} already exists in sample_prediction_report!")

    new_row = pd.DataFrame([{
        "sample_id": sample_id,
        "project_id": metadata["project_id"],
        "sample_name": metadata.get("sample_name"), 
        "execution_sample_id":metadata["execution_sample_id"], 
        "split": metadata["split"],
        "predicted": metadata["predicted"],
        "label": metadata["label"],
        "status": metadata["status"]
    }])

    df = append_row(df, new_row) 
    save_report_csv(df, ReportNames.SAMPLE)

    #print("end save_metadata_sample_prediction_report function ...")

#****************************************************************************************************************
def save_metadata_final_report(metadata: dict):
    print("start save_metadata_final_report function ...")

    project_id = metadata["project_id"]

    df = load_report_csv(ReportNames.FINAL)

    # duplicate check (unique per project)
    #if not df.empty and project_id in df["project_id"].values:
        #raise ValueError(f"Project {project_id} already exists in final_report!")
    if not df.empty and project_id in df["project_id"].values:
        df = df[df["project_id"] != project_id]

    new_row = pd.DataFrame([{
        "project_id": project_id,

        "test1": metadata.get("test1"),
        "test2": metadata.get("test2"),
        "test3": metadata.get("test3"),
        "test4": metadata.get("test4"),
        "test5": metadata.get("test5"),
        "test6": metadata.get("test6"),
        "test7": metadata.get("test7"),
        "test8": metadata.get("test8"),

        "final_result": metadata.get("final_result")
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_report_csv(df, ReportNames.FINAL)

    print("end save_metadata_final_report function ...")

#****************************************************************************************************************
'''def save_metadata_entropy_report(metadata: dict):
    project_id   = metadata["project_id"]
    dataset_id   = metadata["dataset_id"]
    dataset_name = metadata["dataset_name"]
    avg_entropy  = metadata["average_entropy"]
    avg_merged   = metadata["average_merged_entropy"]

    df = load_report_csv("entropy_report.csv")

    if not df.empty and dataset_id in df["dataset_id"].values:
        df = df[df["dataset_id"] != dataset_id]

    new_row = pd.DataFrame([{
        "project_id":          project_id,
        "dataset_id":          dataset_id,
        "dataset_name":        dataset_name,
        "average_entropy":     avg_entropy,
        "average_merged_entropy": avg_merged
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_report_csv(df, "entropy_report.csv")
'''
#****************************************************************************************************************

def create_metadata_project(user_id):
    print("start create_metadata_project function in metadataregistrar.py ........................")  

    project_id = generate_project_id(user_id)

    metadata_project= {
        
        
        "project_id": project_id,
        "user_id": user_id,
        
    }

    print("end create_metadata_project function in metadataregistrar.py  ************************************ ")
    return metadata_project
#****************************************************************************************************************
def create_metadata_dataset( dataset_path, project_id,dataset_type,dataset_name="ML",dataset_file="",input_type=""):
    print("start create_metadata_dataset function in metadataregistrar.py ........................")  


    dataset_id = generate_dataset_id(project_id,dataset_name)

    metadata_dataset = {
        
        
        "project_id": project_id,
        "dataset_id": dataset_id,
        "dataset_path": dataset_path,
        "dataset_type": dataset_type, 
        "dataset_name":dataset_name,
        "dataset_file":dataset_file, #name of folder 
        "input_type": input_type #text is defualt -folder-json
        

    }

    print("end create_metadata_dataset function in metadataregistrar.py  ************************************ ")
    return metadata_dataset
    #******************************************************************************************************************

def create_metadata_tool( tool_path, project_id, tool_name,input_format):
    print("start create_metadata_tool function in metadataregistrar.py ........................")  


    tool_id = generate_tool_id(project_id,tool_name)

    metadata_tool = {
        
        
        "project_id": project_id,
        "tool_id": tool_id,
        "tool_path": tool_path,
        "tool_name":tool_name,
        "input_format":input_format,
        #"dataset_type_convertor":dataset_type_convertor #none for text / folder_to_text /Json_to_text

    }

    print("end create_metadata_tool function in metadataregistrar.py  ************************************ ")
    return metadata_tool
   #******************************************************************************************************************

def generate_tool_id(project_id: str,tool_name:str) -> str:
    print("start generate_tool_id function in metadataregistrar.py ........................")  
    
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:6]  
    
    tool_id = f"tool_{tool_name}_{project_id.lower()}_{today}_{uid}"

    print("end generate_tool_id function in metadataregistrar.py  ************************************ ")
    return tool_id

    #******************************************************************************************************************

def generate_dataset_id(project_id: str,dataset_name:str) -> str:
    print("start generate_dataset_id function in metadataregistrar.py ........................")  
   
    today =datetime.now().strftime("%Y%m%d")
    
    uid  = uuid.uuid4().hex[:6]  # short UUID fragment
    
    dataset_id = f"ds_{dataset_name}_{project_id}_{today}_{uid }"

    print("end generate_dataset_id function in metadataregistrar.py  ************************************ ")
    return dataset_id

#******************************************************************************************************************

def generate_user_id(username: str) -> str:
    print("start generate_user_id function in metadataregistrar.py ........................")   

    username_str = str(username)
    
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:6]  
    
    user_id = f"user_{username_str .lower()}_{today}_{uid}"

    print("end generate_user_id function in metadataregistrar.py  ************************************ ")
    return user_id


#******************************************************************************************************************
def generate_project_id(user_id: str) -> str:
    print("start generate_project_id function in metadataregistrar.py ........................")  

    user_id_str = str(user_id)
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:6]  
    
    project_id = f"prj_{user_id_str.lower()}_{today}_{uid}"


    print("end generate_project_id function in metadataregistrar.py ************************************ ")
    return project_id


#******************************************************************************************************************

def register_user(username: str, password: str):
    print("start register_user function in metadataregistrar.py ........................")  
  
    if not username or not password:
        raise ValueError("Username and password must be provided!")

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    df = load_csv("users.csv")

   
    if not df.empty and username in df["username"].values:
        raise ValueError("Username already exists!")

    
    user_id = f"user_{username.lower()}_{uuid.uuid4().hex[:6]}"

    
    new_row = pd.DataFrame([{
        "user_id" :user_id,
        "username": username,
        "password": password_hash
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_csv(df, "users.csv")
    print("end register_user function in metadataregistrar.py ************************************ ")

    return user_id
        
        #******************************************************************************************************************

def login_user(username: str, password: str):
    print("start login_user function in metadataregistrar.py ........................")  
  

    if not username or not password:
        raise ValueError("Username and password must be provided!")

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    df = load_csv("users.csv")

    
    if df.empty:
        raise ValueError("No registered users found!")

    
    user_row = df[
        (df["username"] == username) & 
        (df["password"] == password_hash)
    ]

    if not user_row.empty:
        
        user_id = f"USER_{username.upper()}_{uuid.uuid4().hex[:6]}"
        print("end login_user function (CSV version)************************************")
        return user_id
     
    print("end login_user function in metadataregistrar.py  ************************************ ")

#******************************************************************************************************************

def save_metadata_project(metadata: dict):
    print("start save_metadata_project function in metadataregistrar.py ........................")

       
    project_id = metadata["project_id"]
    user_id = metadata["user_id"]

    df = load_csv("project.csv")

    
    if not df.empty and project_id in df["project_id"].values:
        raise ValueError(f"Project ID {project_id} already exists!")

    new_row = pd.DataFrame([{
        "project_id": project_id,
        "user_id": user_id
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_csv(df, "project.csv")
    print("end save_metadata_project function in metadataregistrar.py ************************************")
#******************************************************************************************************************
def save_metadata_dataset(metadata: dict):
    print("start save_metadata_dataset function in metadataregistrar.py ........................")
    

       
    project_id = metadata["project_id"]
    dataset_id = metadata["dataset_id"]
    dataset_path = metadata["dataset_path"]
    dataset_type = metadata["dataset_type"] 
    dataset_name = metadata["dataset_name"]
    dataset_file = metadata["dataset_file"]
    input_type =metadata["input_type"] #text is defualt -folder-json
    


    df = load_csv("dataset.csv")

    
    if not df.empty and dataset_id in df["dataset_id"].values:
        raise ValueError(f"Dataset ID {dataset_id} already exists!")

    new_row = pd.DataFrame([{
        "dataset_id": dataset_id,
        "project_id": project_id,
        "dataset_path": dataset_path,
        "dataset_type": dataset_type,
        "dataset_name": dataset_name,
        "dataset_file": dataset_file,
        "input_type"  : input_type #text is defualt -folder-json
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_csv(df, "dataset.csv")
    print("end save_metadata_dataset function in metadataregistrar.py ************************************")

#*****************************************************************************************************************
def save_metadata_tool(metadata: dict):
    print("start save_metadata_tool function in metadataregistrar.py ........................")

       
    project_id = metadata["project_id"]
    tool_id = metadata["tool_id"]
    tool_path = metadata["tool_path"]
    tool_name = metadata["tool_name"]
    #input_type_convertor=["input_type_convertor"]    #none for text / folder_to_text /Json_to_text
    
    df = load_csv("tool.csv")

    if not df.empty and tool_id in df["tool_id"].values:
        raise ValueError(f"Tool ID {tool_id} already exists!")
    
    new_row=pd.DataFrame([{

           "tool_id":tool_id,
           "project_id":project_id,
           "tool_path":tool_path,
           "tool_name":tool_name


            }])

   

    df = pd.concat([df, new_row], ignore_index=True)
    save_csv(df, "tool.csv")

    print("end save_metadata_tool function in metadataregistrar.py ************************************")
#******************************************************************************************************************
def get_dataset_path(dataset_id: str) -> str:
    print("start get_dataset_path  function  in metadataregistrar.py .......................... ")

    df = load_csv("dataset.csv")

    if df.empty:
        raise ValueError("No datasets found!")

    row = df[df["dataset_id"] == dataset_id] 
    if not row.empty:
        dataset_path = row.iloc[0]["dataset_path"]
        print("end get_dataset_path  function  in metadataregistrar.py ******************************************")
        return dataset_path
    else:
        raise ValueError(f"No dataset found with id {dataset_id}")
        print("error in get_dataset_path  function  in metadataregistrar.py ")

#**************************************************************************************************
def get_tool_path(project_id: str) -> str:
    print("start get_tool_path  function  in metadataregistrar.py .......................... ")

    df=load_csv("tool.csv")
    if df.empty:
        raise ValueError("No tools found!")
    
    row = df[df["project_id"]==project_id]
    if not row.empty:
        tool_path=row.iloc[0]["tool_path"]
        print("end get_tool_path  function  in metadataregistrar.py  ******************************************")
        return tool_path

    else:
        raise ValueError(f"No tool found for project {project_id}")
    print("error in get_tool_path  function  in metadataregistrar.py  ******************************************") 

#***********************************************************************************************************************************


def to_wsl_path(p: str) -> str:
    if not isinstance(p, str):
        return p
    s = p.strip()
    if re.match(r"^[A-Za-z]:[\\/]", s):
        drive = s[0].lower()
        rest = s[2:].replace("\\", "/")
        return f"/mnt/{drive}/{rest.lstrip('/')}"
    return s

_MANIFEST_SEPARATOR_RE = re.compile(r"^[-=]{10,}$")

# header: either the old numbered convention ("12 mycontract.sol") or the
# current bare-filename convention Peculiar's own manifests actually use
# ("train_1455.sol", no leading number).
_MANIFEST_HEADER_RE = re.compile(r"^\s*(?:\d+\s+)?(\S+\.sol)\s*$", re.IGNORECASE)

# label line: a bare 0/1, "label: 0", or "<name>.sol 0" all on one line.
_MANIFEST_LABEL_BARE_RE     = re.compile(r"^\s*([01])\s*$")
_MANIFEST_LABEL_KEYED_RE    = re.compile(r"^\s*label\s*:\s*([01])\s*$", re.IGNORECASE)
_MANIFEST_LABEL_FILENAME_RE = re.compile(r"^\s*\S+\.sol\s+([01])\s*$", re.IGNORECASE)


def _extract_manifest_label(line: str):
    for pattern in (_MANIFEST_LABEL_BARE_RE, _MANIFEST_LABEL_KEYED_RE, _MANIFEST_LABEL_FILENAME_RE):
        m = pattern.match(line.strip())
        if m:
            return int(m.group(1))
    return None


def parse_manifest_txt(txt_path: str):
    """
    Tolerant manifest parser.

    Previously this split on the literal substring "-"*40 (exactly 40
    dashes) and required each block's header line to start with a digit
    ("^\\s*\\d+\\s+(\\S+\\.sol)\\s*$"). Neither holds for the manifests this
    framework actually produces today -- e.g. dataset/user.txt (Peculiar)
    uses a 33-dash separator line (203713 of them, one per sample) and
    bare "<split>_<id>.sol" header lines with no leading number. Since a
    33-dash run never contains a 40-dash run as a substring, the old code
    silently never split the file at all and returned zero samples every
    time -- no exception, no warning of its own, just an empty dataset
    that looked like a successful parse to every caller.

    This version splits on any line that is purely 10+ repeats of the
    same '-' or '=' character (covers both the 33-dash and any older
    40-dash/other-length convention), and accepts header lines with or
    without a leading number, and labels written as a bare 0/1, "label: 0",
    or "<name>.sol 0" on one line -- so manifests from any of TL1/TL31/
    TL104's wrappers, old or new, parse the same way instead of each
    needing its own parser.
    """
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = f.read().splitlines()

    blocks = []
    current = []
    for line in raw_lines:
        if _MANIFEST_SEPARATOR_RE.match(line.strip()):
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)

    out = []
    skipped_no_header = 0
    skipped_no_label = 0

    for block in blocks:
        lines = [ln for ln in block if ln.strip() != ""]
        if len(lines) < 2:
            continue

        m = _MANIFEST_HEADER_RE.match(lines[0])
        if not m:
            skipped_no_header += 1
            continue
        filename = m.group(1)

        label_i = _extract_manifest_label(lines[-1])
        if label_i is None:
            skipped_no_label += 1
            continue

        content = "\n".join(lines[1:-1])
        out.append({"filename": filename, "content": content, "label": label_i})

    if skipped_no_header or skipped_no_label:
        print(f"[parse_manifest_txt] {txt_path}: parsed {len(out)} samples, "
              f"skipped {skipped_no_header} block(s) with no recognizable header, "
              f"{skipped_no_label} block(s) with no recognizable label")

    return out


#*********************************************************************************************************************************
def load_dataset(dataset_id: str):
    print("start load_dataset function in metadataregistrar.py .......................... ")

    # --- read metadata from CSV ---
    df = load_csv("dataset.csv")
    if df.empty:
        raise ValueError("No datasets found!")

    row = df[df["dataset_id"] == dataset_id]
    if row.empty:
        raise ValueError(f"No dataset found with id: {dataset_id}")

    r            = row.iloc[0]
    dataset_path = to_wsl_path(r["dataset_path"])
    dataset_type = r.get("dataset_type", "SourceCode")   # "SourceCode" | "Bytecode"
    input_type   = str(r.get("input_type", "folder")).strip().lower()
    dataset_file = str(r.get("dataset_file", "")).strip()
    dataset_name = str(r.get("dataset_name", "")).strip()

    if not os.path.exists(dataset_path):
        raise ValueError(f"Path does not exist: {dataset_path}")

    # --- dispatch by input_type ---
    if input_type == "folder":
        dataset_file = ""
        samples = []
        for root, _, files in os.walk(dataset_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                samples.append({"filename": filename, "content": content})

    elif input_type == "text":
        file_path = os.path.join(dataset_path, dataset_file) if dataset_file else dataset_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")
        # reuse existing parser for manifest .txt, else read lines
        if file_path.lower().endswith(".txt"):
            samples = parse_manifest_txt(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if l.strip()]
            samples = [{"filename": dataset_file, "content": line} for line in lines]

    elif input_type == "excel":
        file_path = os.path.join(dataset_path, dataset_file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        import pandas as pd
        df_data = pd.read_excel(file_path)
        samples = df_data.to_dict(orient="records")

    elif input_type == "json":
        file_path = os.path.join(dataset_path, dataset_file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            samples = json.load(f)
        if not isinstance(samples, list):
            raise ValueError("JSON dataset must be a list of records.")

    else:
        raise ValueError(f"Unsupported input_type: '{input_type}'. Use: folder | text | excel | json")

    # --- tag every sample with type info ---
   

    print(f"end load_dataset ")
    return samples

#*********************************************************************************************************************************

'''
def load_dataset(dataset_id: str):
    print("start load_dataset function  in metadataregistrar.py .......................... ")

    dataset_path = get_dataset_path(dataset_id)
    dataset_path = to_wsl_path(dataset_path)

    if not os.path.exists(dataset_path):
        raise ValueError(f"Path does not exist: {dataset_path}")

    if os.path.isfile(dataset_path) and dataset_path.lower().endswith(".txt"):
        data = parse_manifest_txt(dataset_path)
        print("end load_dataset function  in metadataregistrar.py  ******************************************")
        return data

    if os.path.isdir(dataset_path):
        dataset_files = []
        for root, _, files in os.walk(dataset_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if os.path.isfile(file_path):
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    dataset_files.append({"filename": filename, "content": content})
        print("end load_dataset function  in metadataregistrar.py  ******************************************")
        return dataset_files

    raise ValueError(f"Unsupported dataset path: {dataset_path}")
    '''

#*********************************************************************************************************************************
'''
def load_dataset(dataset_id: str):
    print("start load_dataset function  in metadataregistrar.py .......................... ")
   
    folder_path = get_dataset_path(dataset_id)

    if not os.path.exists(folder_path):
        raise ValueError(f"Folder does not exist: {folder_path}")

    dataset_files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                dataset_files.append({"filename": filename, "content": content})

    print("end load_dataset function  in metadataregistrar.py  ******************************************")           

    return dataset_files
'''
#***************************************************************************************************
def save_dataset(dataset_path, dataset,project_id, folder_name):
    print("start save_dataset function in metadataregistrar.py ........................................")

    # Example: input = F:\TA\dataset\orig  →  base_path = F:\TA\dataset
    base_path = os.path.abspath(dataset_path)

    # --- Create a unique folder for the new dataset ---
    #timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    #short_uuid = uuid.uuid4().hex[:6]
    #new_folder = f"{folder_name}_{timestamp}_{short_uuid}"
    new_folder = f"{folder_name}"
    #new_folder = f"{folder_name}_{project_id}"

    target_path = os.path.join(base_path, new_folder)
    tmp_path = target_path + "_tmp"
    # --- Prepare temp directory ---
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    os.makedirs(tmp_path, exist_ok=True)
        


    # --- Write dataset files ---
    for idx, item in enumerate(dataset):
        if isinstance(item, dict):
            filename = item.get("filename") or f"contract_{idx}.sol"
            content = item.get("content", "")
        else:
            filename = f"contract_{idx}.sol"
            content = item

        file_path = os.path.join(tmp_path, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    # --- Move temp folder to final location ---
    if os.path.exists(target_path):
        shutil.rmtree(target_path)
    os.rename(tmp_path, target_path)

    print(f"Dataset saved at: {target_path}")
    print("end save_dataset function in metadataregistrar.py ******************************************")

    return target_path

#***************************************************************************************************
def fetch_tests_for_project(project_id: str):
    print("start fetch_tests_for_project function in metadataregistrar.py ........................................")


    # Load all CSVs
    base_path = r"/mnt/f/LISTTOOL/Framework/RUN/metadata_csv"

    df_test = pd.read_csv(f"{base_path}/test.csv")
    df_dataset = pd.read_csv(f"{base_path}/dataset.csv")
    df_tool = pd.read_csv(f"{base_path}/tool.csv")
    df_test_dataset = pd.read_csv(f"{base_path}/test_dataset.csv")
    df_test_tool = pd.read_csv(f"{base_path}/test_tool.csv")
    # Merge datasets with tests using left join to keep all tests

    df_test_tool["tool_name"] = df_test_tool["tool_name"].fillna('').astype(str)
    df_right = df_tool[df_tool["project_id"] == project_id].copy()
    df_right["tool_name"] = df_right["tool_name"].astype(str)

    merged = (
        df_test
        .merge(df_test_dataset, on="test_id", how="left")
        .merge(df_dataset[df_dataset["project_id"] == project_id], on="dataset_name", how="left")
        .merge(df_test_tool, on="test_id", how="left")
        .merge(df_right, on="tool_name", how="left")
    )

    print(f" Total tests in df_test: {len(df_test)}")
    print(f"After merge total rows: {len(merged)}")
    print(f" Unique test_ids after merge: {merged['test_id'].nunique()}")
    print(" Columns in merged DataFrame:")

    print(merged.columns.tolist())
    print(f" Total rows after merge: {len(merged)}")

    # DEBUG: inspect rows where test_id is NaN (helps trace which merge introduced them)
    nan_rows = merged[merged["test_id"].isna()]
    if not nan_rows.empty:
        print(f"[DEBUG] rows with NaN test_id: {len(nan_rows)}")
        print(nan_rows.to_dict(orient="records"))

    tests = defaultdict(lambda: {"test_name": None, "exec_id": None, "datasets": [], "tools": [], "test_path": None})

    for _, row in merged.iterrows():
        test_id = row.get("test_id")

        # Skip rows with no valid test_id (avoids creating a bogus "nan" entry)
        if pd.isna(test_id):
            continue

        test_name = row.get("test_name")
        exec_id = row.get("exec_id")
        test_path = row.get("test_path")
        dataset_id = row.get("dataset_id")
        dataset_name = row.get("dataset_name")
        dataset_file = row.get("dataset_file")
        dataset_path = row.get("dataset_path")
        tool_id = row.get("tool_id")
        tool_name = row.get("tool_name")
        tool_path = row.get("tool_path")
        tool_run = row.get("tool_run")
        input_format = row.get("input_format")
        input_type = row.get("input_type")

        if tests[test_id]["test_name"] is None and pd.notna(test_name):
           tests[test_id]["test_name"] = str(test_name)

        if tests[test_id]["exec_id"] is None:
            tests[test_id]["exec_id"] = exec_id
        if tests[test_id]["test_path"] is None:
            tests[test_id]["test_path"] = test_path

        if pd.notna(tool_run):
            if isinstance(tool_run, str):
                tests[test_id]["tool_run"] = tool_run.strip().lower() == "true"
            else:
                tests[test_id]["tool_run"] = bool(tool_run)

        if pd.notna(dataset_id):
            dataset_entry = {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "dataset_path": dataset_path,
                "dataset_file": dataset_file,
                "input_type": input_type
            }
            if dataset_entry not in tests[test_id]["datasets"]:
                tests[test_id]["datasets"].append(dataset_entry)
        else:
            print(f"MISSING ****dataset**** for test_id: {test_id}")

        if pd.notna(tool_id):
            tool_entry = {
                "tool_id": tool_id,
                "tool_name": tool_name,
                "tool_path": tool_path,
                "input_format": input_format
            }
            existing_tool_ids = [t["tool_id"] for t in tests[test_id]["tools"]]
            if tool_id not in existing_tool_ids:
                tests[test_id]["tools"].append(tool_entry)
        else:
            print(f" No need tool for test_id: {test_id}")

    print("\n========== TESTS SUMMARY =========================================================================================================")

    for tid, t in tests.items():
       ds = [(d.get("dataset_name"), d.get("dataset_file")) for d in t["datasets"]]
       tl = [x.get("tool_name") for x in t["tools"]]
       print(f"{tid} | name={t.get('test_name')} | exec={t['exec_id']} | tool_run={t.get('tool_run')} | datasets={ds} | tools={tl}")
       print("------------------------------------------------------------------------------------------------------------------------------------")

    print("======================================================================================================================================")

    for tid, t in tests.items():
        print(f"\n{tid} | name={t.get('test_name')}| exec={t['exec_id']} | tool_run={t.get('tool_run')}")

        print("  DATASETS:")
        for d in t["datasets"]:
            print(f"    - {d.get('dataset_name')} ({d.get('dataset_file')})")
            print(f"      path: {d.get('dataset_path')}")

        print("  TOOLS:")
        for x in t["tools"]:
            print(f"    - {x.get('tool_name')}")
            print(f"      path: {x.get('tool_path')}")

        print("======================================================================================================================")
    print("====================================================================================================================================\n")

    print(f"end fetch_tests_for_project function in metadataregistrar.py ****************************************** {len(tests)} tests found")
    return dict(tests)
#***************************************************************************************************

def invoke_data_preprocessor(dataset_path, project_id: str, dataset_id: str, dataset_type: str = "SourceCode"):

    from datapreprocessor import Dispatcher

    dispatcher = Dispatcher(

        dataset_path=dataset_path,

        project_id=project_id,

        dataset_id=dataset_id,

        dataset_type=dataset_type

    )
    print("start invoke_data_preprocessor function  in metadataregistrar.py ........................................")

    print("Invoke Data Preprocessor  is started...............")
    #dispatcher = Dispatcher(dataset_path,project_id, dataset_id_user,dataset_type)

    result = dispatcher.run(dataset_id)

    # Dispatcher.run() loads the dataset into self.dataset as its very
    # first step -- reuse that count instead of loading the (possibly
    # huge) file a second time here. Previously this function always
    # returned {"status": "success"} no matter what dispatcher.run()
    # actually did, so a dataset that failed to parse (0 records --
    # see parse_manifest_txt) and a dataset that genuinely processed
    # were indistinguishable to Mainframework.py's all_preprocessed_ok
    # gate: the [WARN] Dataset is empty print and the "success" status
    # were two different, disconnected code paths.
    records_loaded = len(dispatcher.dataset) if dispatcher.dataset else 0

    df_ds = load_csv("dataset.csv")
    row = df_ds[df_ds["dataset_id"] == dataset_id]
    ds_name = row.iloc[0]["dataset_name"] if not row.empty else dataset_id
    ds_file = row.iloc[0]["dataset_file"] if not row.empty else ""

    print(f"Dataset:\n  name={ds_name}\n  path={dataset_path}\n  file={ds_file}\n"
          f"Records loaded: {records_loaded}")

    if records_loaded == 0:
        print(f"[ERROR] 0 records loaded for dataset '{ds_name}' ({dataset_id}) -- "
              f"refusing to mark preprocessing successful for this dataset.")
        status = "failed"
    else:
        status = "success"

    result_data_preprocessor = {
        "datasets_return ": result,
        "status": status,
        "records_loaded": records_loaded
    }


    print("end invoke_data_preprocessor function  in metadataregistrar.py ******************************************")

    return result_data_preprocessor

#*****************************************************************************************************

def invoke_test_agent(project_id: str, dataset_id: str):
    print("start invoke_test_agent function  in metadataregistrar.py ........................................")
    from test_manager import TestManager
    manager = TestManager()
    result_test_agent= manager.run(project_id, dataset_id)
    print("end invoke_test_agent function  in metadataregistrar.py ******************************************")
    return result_test_agent
