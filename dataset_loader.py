# dataset_loader.py

import os
import pandas as pd
import json

class DatasetLoader:

    def load(self, dataset_path, dataset_name, dataset_type, input_type, dataset_file=""):
        """
        dataset_type : "SourceCode" | "Bytecode"
        input_type   : "text" | "folder" | "excel" | "json"
        """
        input_type   = input_type.strip().lower()
        dataset_type = dataset_type.strip()

        # Step 1 — load raw samples by file format
        if input_type == "text":
            samples = self._load_text(dataset_path, dataset_file)

        elif input_type == "folder":
            samples = self._load_folder(dataset_path)

        elif input_type == "excel":
            samples = self._load_excel(dataset_path, dataset_file)

        elif input_type == "json":
            samples = self._load_json(dataset_path, dataset_file)

        elif input_type == "csv":
            samples = self._load_csv(dataset_path, dataset_file)

        else:
            raise ValueError(f"Unsupported input_type: '{input_type}'")

        # Step 2 — tag every sample with its dataset_type
        for s in samples:
            s["dataset_type"] = dataset_type   # "SourceCode" or "Bytecode"

        return samples

    # ----------------------------------------------------------------
    def _load_text(self, dataset_path, dataset_file):
        """Single .txt — each line = one sample."""
        file_path = os.path.join(dataset_path, dataset_file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]
        return [{"filename": dataset_file, "content": line} for line in lines]

    # ----------------------------------------------------------------
    def _load_folder(self, dataset_path):
        """Folder of files — each file = one sample."""
        if not os.path.isdir(dataset_path):
            raise NotADirectoryError(f"Folder not found: {dataset_path}")
        samples = []
        for root, _, files in os.walk(dataset_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                samples.append({"filename": filename, "content": content})
        return samples

    # ----------------------------------------------------------------
    def _load_excel(self, dataset_path, dataset_file):
        """Excel — each row = one sample."""
        file_path = os.path.join(dataset_path, dataset_file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        df = pd.read_excel(file_path)
        return df.to_dict(orient="records")

    # ----------------------------------------------------------------
    def _load_csv(self, dataset_path, dataset_file):
        """CSV — each row = one sample. Unlike Excel, has no per-cell
        character limit, so long Bytecode strings aren't truncated."""
        file_path = os.path.join(dataset_path, dataset_file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")

    # ----------------------------------------------------------------
    def _load_json(self, dataset_path, dataset_file):
        """JSON list of dicts."""
        file_path = os.path.join(dataset_path, dataset_file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON dataset must be a list of records.")
        return data