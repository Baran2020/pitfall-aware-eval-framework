import os
import sys
import json
import subprocess
from datetime import datetime


TOOL_IMAGE_MAP = {
    "mythril":   "mythril_image",
    "oyente":    "oyente_image",
    "manticore": "manticore_image",
}

TOOL_WRAPPER_MAP = {
    "mythril":   "toolwrapper_mythril.py",
    "oyente":    "toolwrapper_oyente.py",
    "manticore": "toolwrapper_manticore.py"
}

TOOL_IMAGE_BUILD_MAP = {
    "manticore": "/mnt/f/LISTTOOL/Framework/RUN/tools/manticore",
    "mythril":   "/mnt/f/LISTTOOL/Framework/RUN/tools/mythril",
    "oyente":    "/mnt/f/LISTTOOL/Framework/RUN/tools/oyente",
}

STATIC_TOOLS = list(TOOL_WRAPPER_MAP.keys())


# --- split-alignment helpers -----------------------------------------------
# Static tools (mythril/manticore/oyente) have no train/test concept of
# their own -- they just analyze whatever manifest file they're given. The
# ml tool's train_test_split (mode="both") writes "<dataset_name>_split.json"
# into its own tool_path root (bind-mounted at /app, so it lands directly on
# the host at {ml_tool_path}/{dataset_name}_split.json). Without this,
# mythril/manticore/oyente run on the FULL manifest (e.g. 1671 records for
# TL31's "user" dataset) while ml only reports on its 20% held-out test
# split (e.g. 335 records) -- not apples-to-apples. This filters the static
# tool's input down to the same held-out indices before it runs.
def _is_manifest_separator(line):
    s = line.strip()
    return len(s) >= 10 and set(s) == {"-"}


def _parse_manifest_records(path):
    """Yield (header, body_lines, label) in file order. Index i of the
    i-th yielded record is exactly the key used in <base>_split.json --
    matches how the ml pipeline's own parse_file()/build_vectors() assigns
    frag_id in file order when it built that split map."""
    header = None
    lines = []
    seen = False
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            stripped = raw.strip()
            if not stripped:
                continue
            if _is_manifest_separator(stripped):
                if seen:
                    body = lines
                    label = None
                    if body and body[-1] in ("0", "1"):
                        label = int(body[-1])
                        body = body[:-1]
                    yield header, body, label
                header, lines, seen = None, [], False
                continue
            if stripped.endswith(".sol") and header is None:
                header = stripped
                seen = True
                continue
            lines.append(stripped)
            seen = True
    if seen:
        body = lines
        label = None
        if body and body[-1] in ("0", "1"):
            label = int(body[-1])
            body = body[:-1]
        yield header, body, label


def _write_test_split_manifest(manifest_path, split_json_path, out_path, keep="test"):
    with open(split_json_path, "r", encoding="utf-8") as f:
        split_map = {int(k): v for k, v in json.load(f).items()}
    kept = 0
    total = 0
    with open(out_path, "w", encoding="utf-8", newline="\n") as out:
        for idx, (header, body, label) in enumerate(_parse_manifest_records(manifest_path)):
            total += 1
            if split_map.get(idx) != keep or header is None or label is None:
                continue
            out.write(header + "\n")
            out.write("\n".join(body) + "\n")
            out.write(str(label) + "\n")
            out.write("-" * 33 + "\n")
            kept += 1
    if total != len(split_map):
        print(f"[SplitAlign] WARNING: manifest has {total} records but split.json "
              f"has {len(split_map)} entries -- index alignment is unreliable, "
              f"result may not actually match ml's held-out set")
    return kept, total

# --- ML-based tools -------------------------------------------------------
# This used to be a single hardcoded "ml" slot: one image name
# ("my_tool_image"), one build path (ReCheckermaster, with AWDNN's path
# left commented out right above it), and one fixed docker command
# (`conda run -n tf31 python /app/tempruntoolwrappertext.py ...`) baked
# into _run_ml_docker. That meant only ONE ml-category tool could ever be
# registered at a time, and even that one only worked if its image had a
# conda env literally named "tf31" and a file literally named
# tempruntoolwrappertext.py -- which isn't true for AWDNN (conda env is
# "tf29", see AWDNNmain/Dockerfile) or Peculiar (no conda at all, plain
# venv + pip, see peculiar/Dockerfile).
#
# Each ml tool now gets its own entry, the same way mythril/oyente/
# manticore already do via TOOL_WRAPPER_MAP/TOOL_IMAGE_BUILD_MAP above.
ML_TOOL_CONFIG = {
    #"recheck": {
    "ml": {
        "image":       "recheck_image",
        "wrapper":     "tempruntoolwrappertext.py",
        "interpreter": ["conda", "run", "-n", "tf31", "python"],
        "build_path":  "/mnt/f/LISTTOOL/TL31/ReCheckermaster",
        "input_type":  "re",
    },
    "awdnn": {
    #"ml": {
    
        "image":       "awdnn_image",
        "wrapper":     "toolwrapper.py",
        "interpreter": ["conda", "run", "-n", "tf29", "python"],
        "build_path":  "/mnt/f/LISTTOOL/TL1/AWDNNmain",
        "input_type":  "re",
    },
    "peculiar": {
    #"ml": {  
    
        "image":       "peculiar_image",
        "wrapper":     "toolwrapper.py",
        # No conda in peculiar's image (ubuntu:18.04 + plain venv on PATH),
        # so it's invoked directly, same as its own Dockerfile's
        # `CMD ["python3", "detect.py", "dev"]`.
        "interpreter": ["python3"],
        "build_path":  "/mnt/f/LISTTOOL/TL104/peculiar",
        "input_type":  "re",
    },

    "cbgru": {
    

        "image":       "cbgru_image",
        "wrapper":     "toolwrapper.py",
        "interpreter": ["python3"],
        "build_path":  "/mnt/f/LISTTOOL/TL3/CBGRU",
        "input_type":  "re",
     },

    "widennet": {
    
        "image":       "widennet_image",
        "wrapper":     "toolwrapper.py",
        # No conda in widennet's image either (plain python:3.7-slim + pip),
        # same interpreter convention as peculiar/cbgru.
        "interpreter": ["python3"],
        "build_path":  "/mnt/f/LISTTOOL/TL4/WIDENNET",
        "input_type":  "re",
    },
}


class ToolExecutor:

    def __init__(self):
        self.cache = {}

    def run(
        self,
        dataset_path,
        tool_path,
        dataset_id,
        tool_id,
        dataset_name,
        dataset_file=None,
        input_format=None,
        input_type="re",
        #mode="test",
        mode="both",
        tool_name=None,
        split_json_path=None
    ):
        print(f"[ToolExecutor] start | tool_name={tool_name} | tool_id={tool_id} | file={dataset_file}")

        if not dataset_file:
            print("[ERROR] dataset_file is None or empty")
            return []

        if tool_name in STATIC_TOOLS:
            return self._run_static_docker(
                tool_path, dataset_path, dataset_file, tool_name, split_json_path
            )

        if tool_name in ML_TOOL_CONFIG:
            effective_input_type = ML_TOOL_CONFIG[tool_name].get("input_type", input_type)
            print(f"[ToolExecutor] effective input_type={effective_input_type} "
                  f"(ml tool={tool_name}, param={input_type})")
            return self._run_ml_docker(
                tool_path, dataset_path, dataset_file,
                tool_id, tool_name, effective_input_type, mode
            )

        print(f"[ERROR] unknown tool_name={tool_name!r} -- not in STATIC_TOOLS or ML_TOOL_CONFIG")
        return []

    def _ensure_image(self, image_name, tool_name):
        if self._image_exists(image_name):
            print(f"[Docker] image '{image_name}' already exists ✓")
            return True

        build_context = TOOL_IMAGE_BUILD_MAP.get(tool_name) or ML_TOOL_CONFIG.get(tool_name, {}).get("build_path")
        if not build_context:
            print(f"[ERROR] image '{image_name}' not found and no build path defined for '{tool_name}'")
            return False

        print(f"[Docker] image '{image_name}' not found — building from: {build_context}")
        proc = subprocess.run(
            ["docker", "build", "-t", image_name, build_context],
            text=True
        )

        if proc.returncode != 0:
            print(f"[ERROR] build failed for image '{image_name}'")
            return False

        print(f"[Docker] build succeeded: '{image_name}' ✓")
        return True

    def _run_static_docker(self, tool_path, dataset_path, dataset_file, tool_name, split_json_path=None):
        image_name   = TOOL_IMAGE_MAP[tool_name]
        wrapper_file = TOOL_WRAPPER_MAP[tool_name]

        print(f"[StaticDocker] tool={tool_name} | image={image_name} | wrapper={wrapper_file}")

        if not self._ensure_image(image_name, tool_name):
            return []

        effective_dataset_path = dataset_path
        effective_dataset_file = dataset_file

        if split_json_path and os.path.exists(split_json_path):
            filtered_dir = f"/tmp/filtered_manifests/{tool_name}"
            os.makedirs(filtered_dir, exist_ok=True)
            filtered_path = os.path.join(filtered_dir, "test_only_" + dataset_file)
            try:
                kept, total = _write_test_split_manifest(
                    os.path.join(dataset_path, dataset_file), split_json_path, filtered_path
                )
                print(f"[StaticDocker] split-aligned: {dataset_file} ({total} records) -> "
                      f"{kept} test-split records via {split_json_path}")
                effective_dataset_path = filtered_dir
                effective_dataset_file = os.path.basename(filtered_path)
            except Exception as e:
                print(f"[StaticDocker] WARNING: split filter failed ({e}) -- "
                      f"falling back to FULL dataset, NOT aligned with ml's held-out test set")
        else:
            print(f"[StaticDocker] no split.json found at {split_json_path!r} -- "
                  f"running on FULL dataset, NOT aligned with ml's held-out test set")

        run_command = [
            "docker", "run", "--rm",#for cpu
            #"docker", "run", "--rm", "--gpus", "all",#For GPU for Peculiar
            "-v", f"{tool_path}:/app",
            "-v", f"{effective_dataset_path}:/dataset:ro",
            image_name,
            "python", f"/app/{wrapper_file}",
            f"/dataset/{effective_dataset_file}",
        ]



        print(f"[StaticDocker] $ {' '.join(run_command)}")
        proc = subprocess.run(run_command, capture_output=True, text=True)

        if proc.stderr.strip():
            lines = proc.stderr.strip().splitlines()
            for line in lines[-30:]:
                print(f"  [{tool_name}] {line}")

        if proc.returncode != 0:
            print(f"[ERROR] {tool_name} exited code={proc.returncode}")
            return []

        return self._parse_last_line(proc.stdout, tool_name)

    def _run_ml_docker(self, tool_path, dataset_path, dataset_file,
                        tool_id, tool_name, input_type, mode):
        cfg = ML_TOOL_CONFIG[tool_name]
        image_name = cfg["image"]
        print(f"[Docker] tool={tool_name} | image={image_name} | input_type={input_type}")

        if not self._ensure_image(image_name, tool_name):
            return []

        output_dir = f"/tmp/tool_outputs/{tool_id}"
        os.makedirs(output_dir, exist_ok=True)

        run_command = [
            "docker", "run", "--rm",
            "-v", f"{tool_path}:/app",
            "-w", "/app",
            "-v", f"{dataset_path}:/dataset:ro",
            image_name,
            *cfg["interpreter"],
            f"/app/{cfg['wrapper']}",
            f"/dataset/{dataset_file}",
            "-vt", input_type,
            "--mode", mode
        ]

        print(f"[Docker] $ {' '.join(run_command)}")
        proc = subprocess.run(run_command, capture_output=True, text=True)

        print(f"[Docker] returncode={proc.returncode}")

        if proc.stderr.strip():
            print(f"[Docker] stderr:\n{proc.stderr[-1000:]}")

        if proc.returncode != 0:
            print(f"[Docker ERROR] tool={tool_name} | stdout:\n{proc.stdout[-500:]}")
            return []

        return self._parse_last_line(proc.stdout, tool_name or tool_id)

    def _image_exists(self, image_name):
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True, text=True
        )
        return result.returncode == 0

    '''def _parse_last_line(self, stdout_text, label="tool"):
        lines = stdout_text.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                results = json.loads(line)
                print(f"[{label}] parsed {len(results)} results")
                return results
            except:
                continue
        print(f"[ERROR] [{label}] no valid JSON line found")
        print(f"  stdout tail:\n{stdout_text[-500:]}")
        return []
        '''
    def _parse_last_line(self, stdout_text, label="tool"):
        text = stdout_text.strip()
       
        try:
            results = json.loads(text)
            print(f"[{label}] parsed {len(results)} results")
            return results
        except json.JSONDecodeError:
            pass

        
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            try:
                results = json.loads(text[start:end+1])
                print(f"[{label}] parsed {len(results)} results")
                return results
            except json.JSONDecodeError:
                pass

        print(f"[ERROR] [{label}] no valid JSON found")
        print(f"  stdout tail:\n{stdout_text[-500:]}")
        return []