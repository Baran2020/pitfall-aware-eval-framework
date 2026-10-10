import pandas as pd
import os
import random
import math
from collections import Counter


class DatasetEvaluation:

    # *********************************************************************************************
    def __init__(self):
        pass 
    # *********************************************************************************************
    
    def load_from_excel(self, path):
        print("start load_from_excel function")
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
        if "Bytecode" not in df.columns:
            print("nist")
            raise ValueError(f"Column 'Bytecode' not found. Available columns: {df.columns.tolist()}")
            
        else:
            print("hast")
            contracts = df["Bytecode"].dropna().tolist()
            #print(f"Loaded {len(contracts)} contracts. Sample[5]: {contracts[5] if len(contracts) > 5 else 'N/A'}")

        return {
            "dataset_name": os.path.basename(path),
            "smart_contracts": contracts
        }    

    # *********************************************************************************************
    def normal_dataset(self, dataset, k=100):

        contracts = dataset.get("smart_contracts", [])

        datasets = []

        for i in range(k):

            sampled_contracts = random.sample(
                contracts,
                min(len(contracts), 100)
            )

            datasets.append({
                "dataset_id": f"normal_sample_{i}",
                "contracts": sampled_contracts
            })

        return datasets
    

    # ********************************************************
    def merge_two_contracts(self, c1, c2):

        return str(c1) + str(c2)
    # ********************************************************
    def create_merged_dataset(self, dataset, user_datasets):

        contracts = dataset.get("smart_contracts", [])

        datasets = []

        for i, sample in enumerate(user_datasets):

            merged_contracts = []

            for cj in sample["contracts"]:
                ck = random.choice(contracts)

                merged_contracts.append(
                    self.merge_two_contracts(cj, ck)
                )

            datasets.append({
                "dataset_id": f"merged_sample_{i}",
                "contracts": merged_contracts
            })

        return datasets

    # ********************************************************
    def compute_entropy(self, bytecode):

        if not bytecode:
            return 0.0

        
        if isinstance(bytecode, str):
            bytecode = bytecode.replace("0x", "")
            try:
                data = bytes.fromhex(bytecode)
            except Exception:
                data = bytecode.encode("utf-8")
        else:
            data = bytecode

       
        freq = Counter(data)
        total = len(data)

        Shanon_entropy = 0.0
        for count in freq.values():
            p = count / total
            Shanon_entropy -= p * math.log2(p)

        return Shanon_entropy

    
    # *********************************************************************************************
    def run(self, dataset):

        print("start run function in dataset_evaluation.py ***************************")
        dataset_id = dataset["dataset_id"]
        dataset_name = dataset["dataset_name"]
        file_path = os.path.join(dataset["dataset_path"], dataset["dataset_file"])
        print("file_path:",file_path)
        input_type = dataset.get("input_type", "excel").strip().lower()
        
        if input_type in ("excel", "csv"):
            loaded_dataset = self.load_from_excel(file_path)
        elif input_type == "text":
            loaded_dataset = self.load_from_text(file_path)
        else:
           raise ValueError(f"Unsupported input_type: {input_type}")
        # --------------------------------------------------
        # 1. create 100 user datasets
        # --------------------------------------------------
        user_datasets = self.normal_dataset(loaded_dataset, k=100)

        user_entropy_values = [
                sum(self.compute_entropy(c) for c in d["contracts"]) / len(d["contracts"])
                for d in user_datasets
            ]

        # --------------------------------------------------
        # 2. create 100 merged datasets (pairs each cj from the same
        #    Si used for E1 with a random ck from the full dataset)
        # --------------------------------------------------
        merged_datasets = self.create_merged_dataset(loaded_dataset, user_datasets)

        merged_entropy_values = [
                sum(self.compute_entropy(c) for c in d["contracts"]) / len(d["contracts"])
                for d in merged_datasets
            ]


        
        # --------------------------------------------------
        # 3. metrics
        # --------------------------------------------------
        metrics = {
            "entropy_distribution": user_entropy_values,
            "merged_entropy_distribution": merged_entropy_values,
            "user_datasets": user_datasets,
            "merged_datasets": merged_datasets
        }

        #print("metrics:",metrics["user_datasets"])
        print("end run function in dataset_evaluation.py ***************************")

        return {
            "dataset_name" :dataset_name,
            "dataset_id": dataset_id,
            "metrics": metrics
        }