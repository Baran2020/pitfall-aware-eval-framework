import os
import subprocess

INPUT_DIR = "/mnt/f/LISTTOOL/TL31/ReCheckermaster/train_data/user/"
OUTPUT_DIR = "/mnt/f/LISTTOOL/TL31/ReCheckermaster/train_data/P4_obfuscated"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".sol"):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, f"obf_{filename}")

        print(f"Processing {filename} ...")

        try:
            subprocess.run(
                ["python3", "main.py", input_path, output_path, "--all"],
                check=True
            )
        except subprocess.CalledProcessError:
            print(f"Error processing {filename}")

print("Done!")