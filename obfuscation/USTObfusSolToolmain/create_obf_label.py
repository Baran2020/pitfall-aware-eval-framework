from pathlib import Path

INPUT_LABELS = Path("/mnt/f/LISTTOOL/TL1/AWDNNmain/dataset/labels.txt")
OUTPUT_LABELS = Path("/mnt/f/LISTTOOL/TL1/AWDNNmain/dataset/obf_labels.txt")

PREFIX = "obf_"

def main():
    output_lines = []

    for line in INPUT_LABELS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue

        fname, label = line.split()

        new_fname = PREFIX + fname

        output_lines.append(f"{new_fname} {label}")

    OUTPUT_LABELS.write_text("\n".join(output_lines), encoding="utf-8")

    print("Done!")
    print(f"Saved to: {OUTPUT_LABELS}")

if __name__ == "__main__":
    main()