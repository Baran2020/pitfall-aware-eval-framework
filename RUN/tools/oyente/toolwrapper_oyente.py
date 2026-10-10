#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile

if sys.version_info[0] == 2:
    os.execvp("python3", ["python3"] + sys.argv)

TIMEOUT = int(os.environ.get("TOOL_TIMEOUT", "250"))


def is_separator(s):
    # Any line of 10+ consecutive dashes is a block separator -- same
    # tolerant match toolwrapper_mythril.py and metadataregistrar.
    # parse_manifest_txt already use. This used to be a literal 40-dash
    # substring check, which only matches manifests produced by
    # FolderdatasetTOtext.generate_txt (the P2/P3/P4/P8 variants). The raw
    # TL1/TL31 "user.txt" manifest uses a 33-dash separator, so that check
    # never fired and load_flat_file() silently returned the whole file as
    # one merged "record" instead of ~393 separate contracts.
    return len(s) >= 10 and set(s) == {"-"}

OYENTE_CANDIDATES = [
    "/home/oyente/oyente/oyente.py",
]

KEYWORDS = [
    "reentrancy bug exists: true",
    "re-entrancy bug exists: true",
    "reentrancy bug: true",
    "re-entrancy bug: true",
]


def log(msg):
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def find_oyente():
    for p in OYENTE_CANDIDATES:
        if os.path.exists(p):
            return p
    log("[ERROR] oyente.py not found in container")
    sys.exit(1)


def load_flat_file(path):
    records = []
    state = {"lines": [], "name": None}

    def flush():
        if not state["lines"]:
            return
        lines = [l for l in state["lines"] if l.strip()]
        label = None
        if lines and lines[-1].strip() in ("0", "1"):
            label = int(lines[-1].strip())
            lines = lines[:-1]
        records.append({
            "id": state["name"] or ("fragment_%05d" % len(records)),
            "label": label,
            "source": "\n".join(lines),
        })
        state["lines"] = []
        state["name"] = None

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            bare = line.strip()
            if not bare:
                continue
            if is_separator(bare):
                flush()
                continue
            if bare.endswith(".sol"):
                state["name"] = bare
                continue
            state["lines"].append(bare)
    flush()
    return records


def analyze(oyente_path, source, rid):
    tmp = tempfile.NamedTemporaryFile(suffix=".sol", delete=False, mode="w", encoding="utf-8")
    tmp_path = tmp.name
    try:
        tmp.write(source)
        tmp.close()
        proc = subprocess.Popen(
            ["python2", oyente_path, tmp_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=os.path.dirname(oyente_path) or "/",
        )
        try:
            out, err = proc.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return None, True, "timeout"

        text = (out.decode("utf-8", "ignore") + "\n" +
                err.decode("utf-8", "ignore")).lower()

        if "reentrancy bug exists" in text:
            pred = 1 if "reentrancy bug exists: true" in text else 0
            return pred, False, None

        log("[debug] %s raw output (first 600 chars):\n%s" % (rid, text[:600]))
        return None, False, "analysis_failed"
    except Exception as exc:
        return None, False, str(exc)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(getattr(sys.stdout, "buffer", sys.stdout), errors="replace")
        sys.stderr = codecs.getwriter("utf-8")(getattr(sys.stderr, "buffer", sys.stderr), errors="replace")

    if len(sys.argv) < 2:
        log("usage: toolwrapper_oyente.py <dataset_file>")
        sys.exit(1)

    dataset = sys.argv[1]
    oyente_path = find_oyente()
    log("[oyente] using %s" % oyente_path)

    records = load_flat_file(dataset)
    total = len(records)
    log("[oyente] loaded %d contracts" % total)

    results = []
    for i, rec in enumerate(records):
        pred, timed_out, error = analyze(oyente_path, rec["source"], rec["id"])
        log("[oyente] [%d/%d] %s predicted=%s label=%s%s" % (
            i + 1, total, rec["id"], pred, rec["label"],
            " (TIMEOUT)" if timed_out else (" (ERROR: %s)" % error if error else "")
        ))
        results.append({
            "id": rec["id"],
            "label": rec["label"],
            "predicted": pred,
            "timed_out": timed_out,
            "error": error,
            "split": "test",
        })

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()