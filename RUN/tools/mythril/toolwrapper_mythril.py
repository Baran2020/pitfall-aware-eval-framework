import os
import sys
import json
import subprocess
import tempfile

TIMEOUT = int(os.environ.get("TOOL_TIMEOUT", "120"))
SOLC_VERSION = os.environ.get("SOLC_VERSION", "0.4.24")


def log(msg):
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def is_separator(line):
    s = line.strip()
    return len(s) >= 10 and set(s) == {"-"}


def split_label(lines):
    if lines and lines[-1] in ("0", "1"):
        return lines[:-1], int(lines[-1])
    return lines, None


def parse_file(filename):
    fragment = []
    contract_name = None

    with open(filename, "r", encoding="utf8", errors="ignore") as f:
        for raw in f:
            line = raw.replace("\r", "").replace("\n", "")
            stripped = line.strip()

            if is_separator(stripped):
                if fragment:
                    code, label = split_label(fragment)
                    yield code, label, contract_name
                fragment = []
                contract_name = None
                continue

            if not stripped:
                continue

            if stripped.endswith(".sol") and len(stripped.split()) == 1:
                contract_name = stripped
                continue

            fragment.append(stripped)

    if fragment:
        code, label = split_label(fragment)
        yield code, label, contract_name


def run_mythril(fragment, rid):
    tmp = tempfile.NamedTemporaryFile(suffix=".sol", delete=False, mode="w")
    tmp_path = tmp.name
    try:
        tmp.write("\n".join(fragment))
        tmp.close()

        cmd = [
            "myth", "analyze", tmp_path,
            "-o", "json",
            "--execution-timeout", str(max(TIMEOUT - 30, 30)),
            "--no-onchain-data",
        ]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            out, err = proc.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return None, True, "timeout"

        out_text = out.decode("utf-8", "ignore")

        try:
            report = json.loads(out_text.strip().split("\n")[-1])
        except ValueError:
            return None, False, "myth output not JSON: " + out_text[:200]

        if report.get("success") is False and report.get("error"):
            return None, False, "mythril failed: " + str(report["error"])[:200]

        issues = report.get("issues", [])
        for issue in issues:
            swc = str(issue.get("swc-id", ""))
            title = str(issue.get("title", "")).lower()
            if swc == "107" or "reentran" in title:
                return 1, False, None
        return 0, False, None

    except Exception as exc:
        return None, False, str(exc)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main(filename):
    records = list(parse_file(filename))
    total = len(records)
    log("[mythril] loaded %d contracts" % total)
    log("[mythril] timeout=%d s | solc=%s" % (TIMEOUT, SOLC_VERSION))

    results = []
    for i, (fragment, label, contract_name) in enumerate(records):
        rid = contract_name or ("frag_%d" % (i + 1))
        predicted, timed_out, error = run_mythril(fragment, rid)
        log("[mythril] [%d/%d] %s predicted=%s label=%s%s" % (
            i + 1, total, rid, predicted, label,
            " (TIMEOUT)" if timed_out else
            (" (ERROR: %s)" % error if error else "")
        ))
        results.append({
            "id": rid,
            "label": label,
            "predicted": predicted,
            "split": "test",
            "timed_out": timed_out,
            "error": error,
        })

    ok     = sum(1 for r in results if r["predicted"] is not None)
    pos    = sum(1 for r in results if r["predicted"] == 1)
    failed = total - ok
    log("[mythril] done: analyzed=%d failed=%d predicted_vulnerable=%d" % (ok, failed, pos))

    return results


if __name__ == "__main__":
    filename = sys.argv[1]
    result = main(filename)
    print(json.dumps(result, ensure_ascii=False))