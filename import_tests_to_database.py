from pathlib import Path
from datetime import datetime
import uuid
import os
import pandas as pd

def main():
    
    return "test_group_1"
    
#****************************************************************************************
def generate_test_dataset_id(testgroup) -> str:
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:6]  
    test_dataset_id = f"dataset_{testgroup.lower()}_{today}_{uid}"
    return test_dataset_id

#****************************************************************************************
def generate_test_tool_id(testgroup) -> str:
    
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:6]  
    test_tool_id = f"tool_{testgroup.lower()}_{today}_{uid}"
    return test_tool_id
      
#****************************************************************************************
def generate_test_id(testgroup) -> str:
    today = datetime.now().strftime("%Y%m%d")
    uid = uuid.uuid4().hex[:6]  
    test_id = f"test_{testgroup.lower()}_{today}_{uid}"
    return test_id
#****************************************************************************************
'''
def generate_test_id(conn, testgroup: str) -> str:
    
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM test WHERE testgroup = %s", (testgroup))
    count = cur.fetchone()[0] + 1
    test_id = f"test{count}"
    cur.close()
    return test_id
'''    
#**************************************************************************************
def generate_exec_id(test_number: int) -> int:
    """Return integer exec_id based on test number grouping."""
    if 1 <= test_number <= 3:
        return 1
    elif 4 == test_number :
        return 2
    elif 5 == test_number :
        return 3
    elif 6 == test_number :
        return 4           
    elif 7 == test_number :
        return 5
    elif 8 ==test_number :
        return 6
    else:
        return (test_number - 1) // 3 + 1

#**************************************************************************************
def generate_tool_run(test_number: int) -> bool:
    if test_number ==1:
        tool_run="False"
        return tool_run
    elif 2 <= test_number <= 6:
        tool_run="True"
        return tool_run
    elif 6 <= test_number :
        tool_run="True"
        return tool_run
    else:
        return tool_run

#**************************************************************
def generate_dataset_name(test_number: int) -> bool:
   
    if test_number ==1:
        dataset_name=["user_excel","ethereum"]
        return dataset_name
    elif  test_number == 2:
        #dataset_name=["user","P2_D1","P2_D2","P2_D3","P2_D4"]
        #dataset_name=["user","P2_noise_0.5pct","P2_noise_1pct","P2_noise_1.5pct","P2_noise_2pct","P2_noise_2.5pct"]
        # 5 noise levels x 10 repeats each, matching P2_N_REPEATS in
        # Dispatcher.inject_label_engine_p2 (datapreprocessor.py) -- kept
        # equal to the ReChecker baseline's repeat count so results are
        # directly comparable in the thesis.
        dataset_name = ["user"]
        for pct in ["0.5", "1", "1.5", "2", "2.5"]:
            for rep in range(1, 11):
                dataset_name.append(f"P2_noise_{pct}pct_rep{rep}")
        return dataset_name
    elif  test_number == 3:
        dataset_name=["user","P3_updated_version_min","P3_updated_version_max"]
        return dataset_name
    elif  test_number == 4:
        dataset_name=["user","P4_obfuscated"]
        return dataset_name
    elif  test_number == 5:
        dataset_name=["user"]
        return dataset_name
    elif  test_number == 6:
        dataset_name=["user"]
        return dataset_name
    elif  test_number == 7:
        dataset_name = ["user"]
        for pct in ["0.5", "1", "1.5", "2", "2.5"]:
            for rep in range(1, 11):
                dataset_name.append(f"P2_noise_{pct}pct_rep{rep}")
        #dataset_name=["user","P8_base_rate_minus5pct","P8_base_rate_minus2.5pct","P8_base_rate_plus2.5pct", "P8_base_rate_plus5pct",]
        #dataset_name=[ "user" ]
        #dataset_name=["user","P3_updated_version_min","P3_updated_version_max"] 
        #dataset_name=["user","P4_obfuscated"] 
        return dataset_name
    elif  test_number == 8:
        #dataset_name=["P8_low_imbalance_rate","P8_balance","P8_high_imbalance_rate"]
        dataset_name=[
            "user",
            "P8_base_rate_minus5pct",
            "P8_base_rate_minus2.5pct",
            "P8_base_rate_plus2.5pct",
            "P8_base_rate_plus5pct",
        ]
        return dataset_name
    else:
        return dataset_name
#**************************************************************
def generate_tool_name(test_number: int) -> bool:
    if 1 <= test_number <2:
        tool_name=[""]
        return tool_name
    elif  test_number == 2:
        tool_name=["ml"]
        return tool_name    
    elif  test_number == 3:
        tool_name=["ml"]
        return tool_name
    elif  test_number == 4:
        tool_name=["ml"]
        return tool_name
    elif  test_number == 5:
        tool_name=[""]
        return tool_name
    elif  test_number == 6:
       
       tool_name=["ml", "manticore", "mythril", "oyente"]
       return tool_name
       
    elif  test_number == 7:
        #tool_name=["ml"]
        tool_name=["ml", "manticore", "mythril", "oyente"]
        return tool_name
    elif  test_number == 8:
        tool_name=["ml"]
        return tool_name
    else:
        return tool_name

#*****************************************************************************************
def generate_test_tool_mode(test_number: int) -> bool:
    if test_number ==1:
        mode=None
        return mode
    elif test_number ==2:
        mode=None
        return "both"
    elif test_number ==3:
        mode="both"
        return mode
    elif test_number ==4:
        mode="both"
        return mode
    elif test_number ==5:
        mode="test"
        return mode
    elif test_number ==6:
        mode="both"
        return mode
    elif test_number ==7:
        mode= "both"
        return mode
    elif test_number ==8:
        mode="both"
        return mode  
    else:
        return mode                  


#*****************************************************************************************
def insert_tests(testgroup: str, num_tests: int = 8):
    os.makedirs("metadata_csv", exist_ok=True)

    df_test = pd.DataFrame(columns=["test_id", "exec_id", "test_name", "test_path", "tool_run","mode"])
    df_test_dataset = pd.DataFrame(columns=["test_dataset_id", "test_id", "dataset_name"])
    df_test_tool = pd.DataFrame(columns=["test_tool_id", "test_id", "tool_name"])

    for i in range(1, num_tests + 1):
        test_id = generate_test_id(testgroup)
        exec_id = generate_exec_id(i)
        tool_run = generate_tool_run(i)
        dataset_names = generate_dataset_name(i)
        tool_names = generate_tool_name(i)
        mode=generate_test_tool_mode(i)
        
        test_dir = f"/mnt/f/LISTTOOL/Framework/RUN/test_agent/test" 

        df_test.loc[len(df_test)] = [
            test_id,
            exec_id,
            f"test{i}",
            str((Path(test_dir) / f"test{i}.py").as_posix()),
            #os.path.join(test_dir, "test{i}.py"), 
            tool_run,
            mode
        ]

        for ds in dataset_names:
            df_test_dataset.loc[len(df_test_dataset)] = [
                generate_test_dataset_id(testgroup),
                test_id,
                ds
            ]

        for tl in tool_names:
            df_test_tool.loc[len(df_test_tool)] = [
                generate_test_tool_id(testgroup),
                test_id,
                tl
            ]

    
    df_test.to_csv("metadata_csv/test.csv", index=False)
    df_test_dataset.to_csv("metadata_csv/test_dataset.csv", index=False)
    df_test_tool.to_csv("metadata_csv/test_tool.csv", index=False)

    print(f"[INFO] Saved {num_tests} tests for group '{testgroup}' into CSV files inside 'metadata_csv/' folder.")
    return df_test, df_test_dataset, df_test_tool,num_tests


# ======================================================================================
if __name__ == "__main__":
    testgroup = "test_group_1"
    df_test, df_test_dataset, df_test_tool,num_tests = insert_tests(testgroup)
    print(df_test.head())
    print(df_test_dataset.head())
    print(df_test_tool.head())
    print(f"[INFO] Inserted {num_tests} tests into project {testgroup}")
#*****************************************************************************************  
