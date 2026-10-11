import os
import sys

_REAL_STDOUT = sys.stdout
sys.stdout = sys.stderr  # everything printed from here on is diagnostic -> stderr,
                         # matching TL31's convention so the framework's
                         # _parse_last_line(proc.stdout, ...) sees only JSON.

import logging
from config.fragment_vectorizer import FragmentVectorizer
from config.models.widennet_att import WIDENNET_Attention
import pandas as pd
from config.arg_parser import parameter_parser
import warnings
import numpy as np
import json


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logging (1 = INFO, 2 = WARNING, 3 = ERROR)
logging.getLogger('tensorflow').setLevel(logging.ERROR)  # Suppress TensorFlow logging
warnings.filterwarnings("ignore")

# Set print options to display the entire array
np.set_printoptions(threshold=np.inf)

warnings.filterwarnings("ignore")

# Must match make_user_manifest.py's SEPARATOR and TL31's SEPARATOR (33 dashes).
SEPARATOR = "-" * 33


class ToolWrapper:

    def __init__(self, tool_id: str, tool_path: str):
        self.tool_id = tool_id
        self.tool_path = tool_path

    # ---------------------------
    def _normalize(self, item: dict):
        return {
            "id": item.get("id") or item.get("sample_name") or item.get("file") or "",
            "label": item.get("label"),
            "predicted": item.get("predicted") or item.get("predict"),
            "split": item.get("split")
        }

    # ---------------------------
    def parse_file(self, filename):
        print('parsing file... (', filename, ')')
        with open(filename, "r", encoding="utf8") as file:
            fragment = []
            fragment_val = 0
            # Tracks whether a real record (".sol" header and/or label
            # digit line) was seen since the last separator. Previously
            # the yield was gated on `if fragment:` alone, so a record
            # with a valid label but ZERO code lines between the header
            # and the label (a genuinely empty/corrupt .sol file) had an
            # empty fragment and was silently dropped -- no log, it just
            # never reached results, making this dataset's sample count
            # quietly diverge from the raw folder/labels.txt count.
            # Gating on record_seen yields whenever a record was actually
            # crossed regardless of whether any code ended up in
            # fragment -- an empty fragment still vectorizes fine (all-
            # zero vector), it just isn't dropped anymore.
            record_seen = False
            for line in file:
                stripped = line.strip()
                if not stripped:
                    continue
                if SEPARATOR in line:
                    if record_seen:
                        yield fragment, fragment_val
                    fragment = []
                    fragment_val = 0
                    record_seen = False
                    continue
                if stripped.endswith(".sol"):
                    # manifest id line (e.g. "3211.sol") -- not part of the source
                    record_seen = True
                    continue
                if stripped.isdigit():
                    fragment_val = int(stripped)
                    record_seen = True
                    continue
                fragment.append(stripped)
                record_seen = True
            if record_seen:
                yield fragment, fragment_val

    # ---------------------------
    def get_vectors_df(self, filename, vec_len):
        fragments = []
        count = 0
        vectorizer = FragmentVectorizer(vec_len)

        for fragment, val in self.parse_file(filename):
            count += 1
            print("Collecting fragments...", count, end="\r")
            vectorizer.add_fragment(fragment)

            row = {"fragment": fragment, "val": val}
            fragments.append(row)
        print('Found {} forward slices and {} backward slices'.format(vectorizer.forward_slices, vectorizer.backward_slices))

        print("Training models...", end="\r")
        vectorizer.train_model()
        print()
        vectors = []
        count = 0

        for fragment in fragments:
            count += 1
            print("Processing fragments...", count, end="\r")
            vector = vectorizer.vectorize(fragment["fragment"])
            row = {"vector": vector, "val": fragment["val"]}

            vectors.append(row)

        # convert vectors to dataframe
        df = pd.DataFrame(vectors)
        return df

    # ---------------------------
    def run(self,
            dataset_path,
            dataset_id,
            dataset_name,
            dataset_file,
            input_format,
            input_type,
            mode,
            args):

        print("START TOOL RUN")

        filename = args.filename        # smart contract source file
        vtype = args.vt                 # vulnerability type (re, ts, io)

        mode = getattr(args, "mode", "both")

        base = os.path.splitext(os.path.basename(filename))[0]
        vector_filename = base + "_fragment_vectors.pkl"
        dataset = "config/train_data/" + vector_filename
        print(dataset, '\n')
        vector_length = args.vec_length
        if os.path.exists(dataset):
            df = pd.read_pickle(dataset)
        else:
            print('generating vector dataframe')
            df = self.get_vectors_df(filename, vector_length)
            # convert dataframe to pickle
            df.to_pickle(dataset)

        model = WIDENNET_Attention(df, args)

        do_train = mode in ["train", "both"]
        do_test = mode in ["test", "both"]

        if do_train:
            model.train()

        # model.test() already returns records shaped like TL31's output:
        # [{"id": int, "label": int, "predicted": int, "split": "test"}, ...]
        results = []
        if do_test:
            results = model.test()
            print("END TOOL RUN")

        # This is the one line the framework's tool_executor._parse_last_line()
        # actually reads: the *entire* captured stdout must be exactly this
        # JSON array, same contract TL31's wrapper follows.
        _REAL_STDOUT.write(json.dumps(results))
        _REAL_STDOUT.flush()

        return results


# ---------------------------
if __name__ == "__main__":
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    args = parameter_parser()
    for arg in vars(args):
        print(arg, getattr(args, arg))

    wrapper = ToolWrapper(
            tool_id="awdnn_tool",
            tool_path="/mnt/f/LISTTOOL/TL1/AWDNNmain/"
        )

    wrapper.run(
            None, None, None, None, None, None,
            getattr(args, "mode", "both"),
            args
        )
