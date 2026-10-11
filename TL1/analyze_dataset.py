import os
from collections import Counter

SEPARATOR_MIN_LEN = 10


def analyze_flat_label_file(path):
    """"<name>.sol <label>" one pair per line -- label.txt / labels.txt."""
    total = 0
    labels = Counter()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                label = int(parts[1])
            except ValueError:
                continue
            total += 1
            labels[label] += 1
    return total, labels


def _is_separator(line):
    s = line.strip()
    return len(s) >= SEPARATOR_MIN_LEN and set(s) == {"-"}


def analyze_manifest_file(path):
    """user.txt: blocks of
        <id>.sol
        <solidity source lines...>
        <label: 0 or 1>
        ---------------------------------
    The original script's line.split() logic is wrong for this file --
    almost every line is solidity source, not a "<name> <label>" pair, and
    int(parts[1]) crashes as soon as a code line happens to tokenize into
    exactly two pieces. This reads it block-by-block instead (same
    separator/label logic as toolwrapper.py's parse_manifest())."""
    total = 0
    labels = Counter()
    fragment = []

    def flush(frag):
        if not frag:
            return 0
        label_line = frag[-1].strip()
        if label_line in ("0", "1"):
            labels[int(label_line)] += 1
            return 1
        return 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            stripped = raw.strip()
            if _is_separator(stripped):
                total += flush(fragment)
                fragment = []
                continue
            if not stripped:
                continue
            fragment.append(raw)
    total += flush(fragment)
    return total, labels


def count_sol_files(folder):
    if not os.path.isdir(folder):
        return None
    return sum(1 for f in os.listdir(folder) if f.endswith(".sol"))


def main():
    files = {
        "label":  ("dataset/label.txt",  analyze_flat_label_file),
        "labels": ("dataset/labels.txt", analyze_flat_label_file),
        "user":   ("dataset/user.txt",   analyze_manifest_file),
    }

    for name, (path, parser) in files.items():
        if not os.path.exists(path):
            print(f"{path} not found")
            continue
        total, labels = parser(path)
        print("=" * 40)
        print(name, f"({path})")
        print("Total contracts:", total)
        for label, count in sorted(labels.items()):
            print(f"Label {label}: {count}")

    print("=" * 40)
    folder = "dataset/user"
    n_sol = count_sol_files(folder)
    if n_sol is None:
        print(f"{folder} not found")
    else:
        print(f"folder ({folder})")
        print(".sol files:", n_sol)


if __name__ == "__main__":
    main()
