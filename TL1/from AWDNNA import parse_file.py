from AWDNNA import parse_file
import json
import sys
import numpy as np

# فرض: این‌ها از کد اصلی import می‌شوند
# from your_model_file import parse_file, get_vectors_df, WIDENNET_Attention
from config.arg_parser import parameter_parser
from config.fragment_vectorizer import FragmentVectorizer
from config.models.widennet_att import WIDENNET_Attention


def build_dataset(filename, vec_len):
    args = parameter_parser()

    base_vectors = []
    labels = []
    ids = []

    print("Building dataset...")

    vectorizer = FragmentVectorizer(vec_len)

    # اول pass برای ساخت vocab
    raw_samples = list(parse_file(filename,))

    for i, (fragment, val) in enumerate(raw_samples):
        vectorizer.add_fragment(fragment)

    vectorizer.train_model()

    # دوم pass برای vectorization
    for i, (fragment, val) in enumerate(raw_samples):
        vector = vectorizer.vectorize(fragment)

        base_vectors.append(vector)
        labels.append(val)
        ids.append(i)

    return np.array(base_vectors), labels, ids


def run_inference(filename, args):

    vec_len = args.vec_length

    X, y_true, ids = build_dataset(filename, vec_len)

    print("Loading model...")

    import pandas as pd

	dummy_df = pd.DataFrame({
	    "vector": list(X),
	    "val": y_true
	})
    model = WIDENNET_Attention(dummy_df, args)

    # ⚠ فرض: model.predict وجود ندارد، پس از internal keras model استفاده می‌کنیم
    preds = model.model.predict(X)

    outputs = []

    for i in range(len(X)):
        predicted = int(np.round(preds[i][0]))

        outputs.append({
            "id": ids[i],
            "label": int(y_true[i]),
            "predicted": predicted
        })

    return outputs


def main():
    args = parameter_parser()

    filename = args.filename

    outputs = run_inference(filename, args)

    print(json.dumps({
        "status": "success",
        "outputs": outputs
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()