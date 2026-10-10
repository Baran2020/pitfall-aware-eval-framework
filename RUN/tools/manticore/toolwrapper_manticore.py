import os
import re
import sys
import json
import shutil
import tempfile
import subprocess

TIMEOUT = 150
results = []

# Manticore only registers ANY of its vulnerability detectors (reentrancy,
# overflow, etc.) when --thorough-mode is passed. Without it,
# ethereum_main() forces args.exclude_all = True before choose_detectors()
# runs, so choose_detectors() returns an empty list -- every previous run
# (including with the old, invalid --quick-mode flag) explored states and
# generated testcases but NEVER ran a single detector, so global.findings
# was always empty regardless of the actual contract.
#
# Findings are matched by title substring rather than a bare "reentrancy"
# grep on the whole log, since --thorough-mode also runs unrelated
# detectors (integer overflow, uninitialized storage, etc.) whose output
# must not be mistaken for a reentrancy verdict.
REENTRANCY_FINDING_MARKERS = (
    "potential reentrancy vulnerability",
    "reentrancy multi-million ether bug",
)

dataset_file = sys.argv[1]

with open(dataset_file, "r", encoding="utf-8") as f:
    content = f.read()

# Any line of 10+ consecutive dashes is a block separator -- same tolerant
# match toolwrapper_mythril.py and metadataregistrar.parse_manifest_txt
# already use. The old code split on a literal 40-dash string, which only
# matches manifests produced by FolderdatasetTOtext.generate_txt (the
# P2/P3/P4/P8 variants). The raw TL1/TL31 "user.txt" manifest uses a
# 33-dash separator, so content.split() found zero matches and silently
# treated the entire ~393-contract file as one block -- one bogus
# "contract" analyzed instead of 393.
SEPARATOR_RE = re.compile(r"^-{10,}\s*$", re.MULTILINE)

entries = []
for block in SEPARATOR_RE.split(content):
    block = block.strip()
    if not block:
        continue
    lines = block.splitlines()
    if len(lines) < 3:
        continue

    header = lines[0].strip()
    if not header.endswith(".sol"):
        continue

    last = lines[-1].strip()
    if last not in ("0", "1"):
        continue

    entries.append({
        "rid": header,
        "label": int(last),
        "source": "\n".join(lines[1:-1]).strip(),
    })

total = len(entries)
print(f"manticore: {total} contracts to analyze (timeout={TIMEOUT}s each)", flush=True)

for i, entry in enumerate(entries, start=1):
    rid = entry["rid"]
    label = entry["label"]
    source = entry["source"]

    print(f"[{i}/{total}] running manticore on {rid} ...", flush=True)

    workdir = tempfile.mkdtemp()
    solfile = os.path.join(workdir, f"{rid}.sol")
    with open(solfile, "w", encoding="utf-8") as f:
        f.write(source)
    workspace = os.path.join(workdir, "mcore_ws")

    pred = 0
    status = "ok"
    try:
        mcore_proc = subprocess.run(
            ["manticore", "--thorough-mode", "--workspace", workspace, solfile],
            capture_output=True, text=True, timeout=TIMEOUT
        )
        # DIAGNOSTIC: status=="ok" alone does NOT mean manticore actually
        # found the file / matched a marker -- it only means no exception
        # was raised. Print the real ground truth every time so a run of
        # all predicted=0 can be told apart from "genuinely nothing found"
        # vs "findings file never appeared" vs "manticore itself errored
        # with a nonzero returncode we were silently swallowing before".
        print(f"[{rid}] manticore returncode={mcore_proc.returncode}", flush=True)
        if mcore_proc.returncode != 0:
            tail = (mcore_proc.stderr or "")[-500:]
            print(f"[{rid}] manticore stderr tail:\n{tail}", flush=True)

        findings_path = os.path.join(workspace, "global.findings")
        if os.path.exists(findings_path):
            with open(findings_path, "r", encoding="utf-8", errors="ignore") as f:
                findings_text = f.read().lower()
            print(f"[{rid}] global.findings ({len(findings_text)} chars): "
                  f"{findings_text[:300]!r}", flush=True)
            if any(marker in findings_text for marker in REENTRANCY_FINDING_MARKERS):
                pred = 1
        else:
            print(f"[{rid}] global.findings NOT FOUND at {findings_path} "
                  f"(workspace dir exists: {os.path.isdir(workspace)}, "
                  f"contents: {os.listdir(workspace) if os.path.isdir(workspace) else 'N/A'})",
                  flush=True)
    except subprocess.TimeoutExpired:
        pred = 0
        status = "timeout"
    except Exception as e:
        pred = 0
        status = f"error: {e}"

    print(f"[{i}/{total}] {rid} -> predicted={pred} label={label} ({status})", flush=True)

    shutil.rmtree(workdir, ignore_errors=True)
    results.append({
        "id": rid,
        "label": label,
        "predicted": pred,
        "split": "test",
    })

print(json.dumps(results, indent=4))