import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_file")
    parser.add_argument("-vt", dest="vt", required=True)
    parser.add_argument("--mode", dest="mode", default="both")
    parser.add_argument("--tool-id", dest="tool_id", default="")
    parser.add_argument("--dataset-id", dest="dataset_id", default="")
    args = parser.parse_args()

    started = time.time()

    cmd = [
        sys.executable,
        "AWDNNA.py",
        args.dataset_file,
        "-vt",
        args.vt,
        "--mode",
        args.mode
    ]

    print("start adapter execution .....................")

    proc = subprocess.run(cmd, capture_output=True, text=True)

    stdout = proc.stdout or ""

    outputs = []

    for line in stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            obj = json.loads(line)

            print("DEBUG parsed:", obj)

        except:
            continue

        items = obj if isinstance(obj, list) else [obj]
        for item in items:
            outputs.append({
                "id": item.get("id") or item.get("sample_name") or item.get("file"),
                "label": item.get("label"),
                "predicted": item.get("predicted") or item.get("predicted"),
                "split": item.get("split", None)
            })

    if len(outputs) == 0:
        print("[WARNING] No valid outputs found")

        outputs = [{
            "id": "unknown",
            "predicted": None,
            "split": None
        }]

    result = {
        "status": "success" if proc.returncode == 0 else "error",
        "tool_id": args.tool_id,
        "dataset_id": args.dataset_id,
        "outputs": outputs,
        "error": None if proc.returncode == 0 else "Tool execution failed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_sec": round(time.time() - started, 3),
        "raw": {
            "returncode": proc.returncode
        }
    }

    print("final result ready .....................")
    print(json.dumps(outputs, ensure_ascii=False))
    sys.stdout.flush()
    print("adapter finished .....................", file=sys.stderr)

    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())