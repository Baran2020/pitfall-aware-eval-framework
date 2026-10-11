from collections import Counter

PATH = "train_data/user.txt"
SEPARATOR_MIN_LEN = 10


def is_separator(line):
    s = line.strip()
    return len(s) >= SEPARATOR_MIN_LEN and set(s) == {"-"}


def main():
    total = 0
    labels = Counter()
    fragment = []

    def flush(frag):
        nonlocal total
        if not frag:
            return
        label_line = frag[-1].strip()
        if label_line in ("0", "1"):
            labels[int(label_line)] += 1
            total += 1

    with open(PATH, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            stripped = raw.strip()
            if is_separator(stripped):
                flush(fragment)
                fragment = []
                continue
            if not stripped:
                continue
            fragment.append(raw)
        flush(fragment)

    print(f"File: {PATH}")
    print(f"Total samples: {total}")
    print(f"Label 0: {labels.get(0, 0)}")
    print(f"Label 1: {labels.get(1, 0)}")


if __name__ == "__main__":
    main()
