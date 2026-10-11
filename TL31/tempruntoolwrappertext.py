import os
import sys

_REAL_STDOUT = sys.stdout
sys.stdout = sys.stderr
import json
import logging
import warnings
import argparse

import numpy as np
import pandas as pd

PROJECT_ROOT = "/app"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logging.getLogger('tensorflow').setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


_real_argv = sys.argv
sys.argv = [sys.argv[0]]
try:
    from vectorize_fragment import FragmentVectorizer
    from models.blstm import BLSTM
    from models.blstm_attention import BLSTM_Attention
    from models.lstm import LSTM_Model
    from models.simple_rnn import Simple_RNN
finally:
    sys.argv = _real_argv

SEPARATOR = "-" * 33


def get_args():
    p = argparse.ArgumentParser()
    p.add_argument("dataset", help="path to the fragment dataset file")
    p.add_argument("-vt", "--vuln_type", default="re")
    p.add_argument("--mode", choices=["train", "test", "both"], default="both")
    p.add_argument("--model", default="BLSTM_Attention",
                   choices=["BLSTM", "BLSTM_Attention", "LSTM_Model", "Simple_RNN"])
    p.add_argument("--vector_dim", type=int, default=300)
    p.add_argument("--test_dataset", default=None)
    args, _ = p.parse_known_args()
    if args.test_dataset is None:
        args.test_dataset = args.dataset
    return args


def parse_file(filename):
    log("parsing file...", filename)
    with open(filename, "r", encoding="utf8") as file:
        fragment = []
        fragment_val = None
        # See note below on why this replaces the old `if fragment:`
        # yield gate.
        record_seen = False
        for raw in file:
            stripped = raw.strip()
            if not stripped:
                continue
            if SEPARATOR in raw:
                if record_seen:
                    yield fragment, (fragment_val if fragment_val is not None else 0)
                fragment = []
                fragment_val = None
                record_seen = False
                continue
            if stripped.endswith(".sol"):
                record_seen = True
                continue
            # Previously `if stripped.isdigit() and fragment:` required
            # fragment to already be non-empty before a bare digit line
            # could be treated as the label. For a genuinely empty-content
            # record (valid label, zero code lines between header and
            # label -- e.g. a corrupt 0-byte .sol file), fragment is still
            # [] when the label line is reached, so the guard failed and
            # the label digit fell through to fragment.append(stripped)
            # instead: the label string became the record's "code", and
            # since fragment_val was never set, the record then yielded
            # with label defaulted to 0 -- silently mislabeling any such
            # record (most were actually label=1 in this dataset) as safe,
            # rather than dropping or correctly labeling it. Removing the
            # `and fragment` guard makes label detection unconditional,
            # matching AWDNN's wrapper, so the true label is always
            # captured regardless of whether any code precedes it.
            if stripped.isdigit():
                fragment_val = int(stripped)
                record_seen = True
                continue
            fragment.append(stripped)
            record_seen = True
        if record_seen:
            yield fragment, (fragment_val if fragment_val is not None else 0)


def build_vectors(filename, vector_length, split, vectorizer=None):
    fit_here = vectorizer is None
    if fit_here:
        vectorizer = FragmentVectorizer(vector_length)

    parsed = []
    frag_id = 0
    for fragment, val in parse_file(filename):
        if fit_here:
            vectorizer.add_fragment(fragment)
        parsed.append({"id": "frag_%d" % frag_id, "fragment": fragment,
                       "label": val, "split": split})
        frag_id += 1

    if fit_here:
        log("training vectorizer...")
        vectorizer.train_model()

    results = []
    for item in parsed:
        vec = vectorizer.vectorize(item["fragment"])
        results.append({"id": item["id"], "vector": vec,
                        "label": item["label"], "split": item["split"]})
    return pd.DataFrame(results), vectorizer


def to_model_df(df):
    return pd.DataFrame({"label": df["label"].values,
                         "vector": list(df["vector"].values)})


def build_model(model_name, df, name):
    if model_name == "BLSTM_Attention":
        return BLSTM_Attention(df, name=name)
    elif model_name == "BLSTM":
        return BLSTM(df, name=name)
    elif model_name == "Simple_RNN":
        return Simple_RNN(df, name=name)
    elif model_name == "LSTM_Model":
        return LSTM_Model(df, name=name)
    raise ValueError("Unknown model: %r" % model_name)


def find_weights(base):
    for ext in (".pkl", ".h5"):
        candidate = "/app/" + base + "_model" + ext
        if os.path.exists(candidate):
            return candidate
    return None


def load_split_map(base):
    """Read the sampling split map written by the model during training.
    Keyed by original dataframe index -> 'train'/'test'/'unused'."""
    path = "/app/" + base + "_split.json"
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            raw = json.load(f)
        return {int(k): v for k, v in raw.items()}
    except Exception as e:
        log("warning: could not read split map:", e)
        return None


def predict_all(model, df):
    x_all = np.stack(df["vector"].values)
    probs = model.model.predict(x_all, batch_size=model.batch_size)
    return np.argmax(probs, axis=1)


def main():
    args = get_args()
    mode = args.mode
    vector_length = args.vector_dim
    model_name = args.model

    base = os.path.splitext(os.path.basename(args.dataset))[0]
    cache_path = "/app/" + base + "_fragment_vectors.pkl"

    # Build vectors + vectorizer for the incoming dataset.
    vectorizer = None
    if os.path.exists(cache_path):
        log("loading cached dataset...")
        cached = pd.read_pickle(cache_path)
        if isinstance(cached, dict):
            data_df = cached["df"]
            vectorizer = cached.get("vectorizer")
        else:
            data_df = cached
    else:
        log("generating dataset...")
        data_df, vectorizer = build_vectors(args.dataset, vector_length, "test")
        try:
            pd.to_pickle({"df": data_df, "vectorizer": vectorizer}, cache_path)
        except Exception as e:
            log("warning: could not write cache:", e)

    model = build_model(model_name, to_model_df(data_df), base)

    # ---- mode controls training vs loading, and how split is assigned ----
    if mode in ("train", "both"):
        # Model trains now; it writes the sampling split map during __init__.
        log("training model...")
        model.train()
        split_map = load_split_map(base)
        if split_map is not None:
            data_df = data_df.copy()
            data_df["split"] = [split_map.get(i, "unknown") for i in range(len(data_df))]
        else:
            log("warning: no split map found; defaulting split to 'unknown'")
            data_df = data_df.copy()
            data_df["split"] = "unknown"

    elif mode == "test":
        # No training. Load previously trained weights; every sample is test.
        weights_path = find_weights(base)
        if weights_path:
            try:
                model.model.load_weights(weights_path)
                log("loaded weights:", weights_path)
            except Exception as e:
                log("warning: could not load weights (%s); predictions will be "
                    "from an untrained model" % e)
        else:
            log("warning: no saved weights found for base=%s; predictions will "
                "be from an untrained model. Train with --mode both first." % base)
        data_df = data_df.copy()
        data_df["split"] = "test"

    # Report only the held-out test split so metrics reflect generalization,
    # not performance on rows the model was trained on (matches AWDNN's
    # toolwrapper.py, which only ever predicts on its x_test_* split).
    eval_df = data_df[data_df["split"] == "test"].copy()

    # Tool's own aggregate metrics -> stderr only.
    try:
        import contextlib
        with contextlib.redirect_stdout(sys.stderr):
            model.test()
    except Exception as e:
        log("note: model.test() metrics skipped:", e)

    preds = predict_all(model, eval_df)

    out = []
    for row, pred in zip(eval_df.to_dict("records"), preds):
        label = row.get("label")
        out.append({
            "id": row.get("id"),
            "split": row.get("split"),
            "predicted": int(pred),
            "label": (int(label) if label is not None else None),
        })

    _REAL_STDOUT.write(json.dumps(out))
    _REAL_STDOUT.flush()


if __name__ == "__main__":
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()