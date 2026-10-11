import os
import json
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

from config.fragment_vectorizer import FragmentVectorizer
from config.models.widennet_att import WIDENNET_Attention
import pandas as pd
from config.arg_parser import parameter_parser
import warnings
import numpy as np

np.set_printoptions(threshold=np.inf)
warnings.filterwarnings("ignore")

args = parameter_parser()
for arg in vars(args):
    print(arg, getattr(args, arg))

SEPARATOR = "-" * 40

def parse_file(filename):
    print('parsing file... (', filename, ')')
    with open(filename, "r", encoding="utf8") as file:
        fragment = []
        fragment_val = 0
        contract_name = None        # ← اضافه شد
        frag_index = 0

        for line in file:
            stripped = line.strip()
            if not stripped:
                continue

            # separator → yield و reset
            if SEPARATOR in stripped:
                if fragment:
                    yield fragment, fragment_val, contract_name or f"frag_{frag_index}"
                    frag_index += 1
                fragment = []
                fragment_val = 0
                contract_name = None
                continue

            # خط نام contract: "00 3211.sol"
            if stripped.startswith("00 ") and ".sol" in stripped:
                if contract_name is None:
                    contract_name = stripped.split(" ", 1)[1].strip()
                continue   # همیشه skip

            # label
            if stripped in ("0", "1"):
                fragment_val = int(stripped)
                continue

            fragment.append(stripped)

        # آخرین fragment
        if fragment:
            yield fragment, fragment_val, contract_name or f"frag_{frag_index}"


def get_vectors_df(filename, vec_len):
    fragments = []
    count = 0
    vectorizer = FragmentVectorizer(vec_len)

    for fragment, val, contract_name in parse_file(filename):   # ← contract_name
        count += 1
        print("Collecting fragments...", count, end="\r")
        vectorizer.add_fragment(fragment)
        fragments.append({
            "id": contract_name,        # ← اضافه شد
            "fragment": fragment,
            "val": val
        })

    print('Found {} forward slices and {} backward slices'.format(
        vectorizer.forward_slices, vectorizer.backward_slices))

    print("Training models...", end="\r")
    vectorizer.train_model()
    print()

    vectors = []
    count = 0
    for item in fragments:
        count += 1
        print("Processing fragments...", count, end="\r")
        vector = vectorizer.vectorize(item["fragment"])
        vectors.append({
            "id": item["id"],           # ← اضافه شد
            "vector": vector,
            "val": item["val"]
        })

    df = pd.DataFrame(vectors)
    df = df.set_index("id")             # ← index را contract_name کن
    return df


def main(args):
    filename = args.filename
    vtype = args.vt
    mode = getattr(args, "mode", "both")

    base = os.path.splitext(os.path.basename(filename))[0]
    vector_filename = base + "_fragment_vectors.pkl"
    dataset = "config/train_data/" + vector_filename
    print(dataset, '\n')

    vector_length = args.vec_length
    if os.path.exists(dataset):
        df = pd.read_pickle(dataset)
        # اگر pickle قدیمی index عددی دارد، دوباره generate کن
        if not isinstance(df.index[0], str):
            print("old pickle detected (numeric index) — regenerating...")
            os.remove(dataset)
            df = get_vectors_df(filename, vector_length)
            df.to_pickle(dataset)
    else:
        print('generating vector dataframe')
        df = get_vectors_df(filename, vector_length)
        df.to_pickle(dataset)

    model = WIDENNET_Attention(df, args)

    do_train = mode in ["train", "both"]
    do_test  = mode in ["test", "both"]

    if do_train:
        model.train()
    if do_test:
        preds = model.test()
        return [
            {
                "id": r["id"],
                "label": r.get("label", None),
                "predicted": r["predicted"],
                "split": r["split"]
            }
            for r in preds
        ]
    return []


def convert(obj):
    if isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert(i) for i in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parameter_parser()
    result = main(args)
    print(json.dumps(convert(result)))