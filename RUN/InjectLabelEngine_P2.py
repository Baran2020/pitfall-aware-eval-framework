import random
import os



class InjectLabelEngine:
    """
    P2 - Inaccurate Labels engine.

    Performs symmetric random label-swap noise injection: swaps
    `fraction` of positive (reentrant) labels to negative (safe)
    AND `fraction` of negative labels to positive, independently
    per noise level (each level samples from the ORIGINAL clean
    label set, never from a previously-noised version, so levels
    don't accumulate on top of each other).
    """

    def __init__(self, positive_label=1, negative_label=0):
        self.positive_label = positive_label
        self.negative_label = negative_label

    # ------------------------------------------------------------------
    def load_labels(self, labels_path):
        """
        Reads the original labels.txt file.

        # ASSUMPTION: one line per file, format "filename label"
        # (space or comma separated). Confirm this matches your
        # actual labels.txt format before running — if it's a
        # different format (e.g. one label per line with no
        # filename, positionally matched to a separate file list),
        # this parser needs to change.
        """
        labels = {}
        with open(labels_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.replace(",", " ").split()
                if len(parts) < 2:
                    print(f"[InjectLabelEngine][WARN] malformed line, skipping: {line}")
                    continue
                filename, label = parts[0], parts[-1]
                try:
                    labels[filename] = int(label)
                except ValueError:
                    print(f"[InjectLabelEngine][WARN] non-integer label, skipping: {line}")
        return labels

    # ------------------------------------------------------------------
    def inject_label(self, labels, fraction, seed):
        """
        labels: dict {filename: original_label} — always the CLEAN,
                unmodified mapping (caller must pass the original
                dict each time, not a previously-noised one).
        fraction: portion swapped FROM EACH class independently
                  (e.g. 0.005 -> 0.5% of positives -> negative AND
                  0.5% of negatives -> positive => 1% total swapped)
        seed: must differ per noise level so swaps are independent
              and reproducible.

        Returns: (noisy_labels dict, swap_info dict)
        """
        rng = random.Random(seed)
        noisy_labels = dict(labels)

        positive_files = [fn for fn, lbl in labels.items() if lbl == self.positive_label]
        negative_files = [fn for fn, lbl in labels.items() if lbl == self.negative_label]

        n_pos_swap = round(len(positive_files) * fraction)
        n_neg_swap = round(len(negative_files) * fraction)

        swap_pos = rng.sample(positive_files, min(n_pos_swap, len(positive_files)))
        swap_neg = rng.sample(negative_files, min(n_neg_swap, len(negative_files)))

        for fn in swap_pos:
            noisy_labels[fn] = self.negative_label
        for fn in swap_neg:
            noisy_labels[fn] = self.positive_label

        swap_info = {
            "fraction_per_class": fraction,
            "n_positive_swapped": len(swap_pos),
            "n_negative_swapped": len(swap_neg),
            "swapped_files": swap_pos + swap_neg,
        }

        print(f"[InjectLabelEngine] fraction={fraction} "
              f"pos_swapped={len(swap_pos)} neg_swapped={len(swap_neg)}")

        return noisy_labels, swap_info

    # ------------------------------------------------------------------
    def save_labels(self, noisy_labels, output_path):
        """Writes noisy_labels back out in the same format load_labels reads."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for filename, label in noisy_labels.items():
                f.write(f"{filename} {label}\n")
        return output_path