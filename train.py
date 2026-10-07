"""Train the spam classifier on several real public SMS + email spam corpora.

Model: TF-IDF word 1-2 grams + TF-IDF character 3-5 grams (char_wb) on
normalised text (URLs/emails/phones/money/numbers -> placeholder tokens),
fed to a Logistic Regression. Logistic Regression was chosen over a
calibrated LinearSVC because scores were about the same and LR gives exact,
per-feature explanations (contribution = tfidf value x weight).

Each corpus is split 80/20 (stratified) so every dataset has its own held-out
test set. Training uses sample weights of 1/sqrt(n) per (dataset, class) cell
so the large Enron corpus doesn't drown out short SMS / Indian messages.

Outputs model.joblib and metrics.json (per-dataset test metrics, robustness
probe results, global top features, dataset sizes).
"""
import csv
import gzip
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from explain import Explainer, final_verdict  # noqa: E402
from textnorm import normalize, normalize_short  # noqa: E402
import probes  # noqa: E402

DATA = ROOT / "data" / "combined.csv.gz"
MODEL_FILE = ROOT / "model.joblib"
METRICS_FILE = ROOT / "metrics.json"
SEED = 42

DATASET_INFO = {
    "sms": ("UCI SMS Spam Collection", "https://archive.ics.uci.edu/dataset/228/sms+spam+collection", "SMS, English (Singapore/UK)"),
    "enron": ("Enron-Spam (preprocessed by MWiechmann)", "https://github.com/MWiechmann/enron_spam_data", "Email, English"),
    "spamassassin": ("Apache SpamAssassin public corpus", "https://spamassassin.apache.org/old/publiccorpus/", "Email, English (headers stripped)"),
    "deysi": ("Deysi/spam-detection-dataset", "https://huggingface.co/datasets/Deysi/spam-detection-dataset", "Mixed short texts/posts, English"),
    "india_sms": ("Indian Telecom SMS Spam Collection", "https://github.com/junioralive/india-spam-sms-classification", "SMS, Indian English (+ some Hinglish)"),
    "india_2011": ("IIIT-Delhi crowdsourced Indian SMS (Yadav et al. 2011)", "https://github.com/princebari/-SMS-Spam-Classification-on-Indian-Dataset-A-Crowdsourced-Collection-of-Hindi-and-English-Messages", "SMS, Indian English + Hinglish"),
    "hindi_mt": ("SMS Spam Multilingual Collection (Hindi column)", "https://huggingface.co/datasets/dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset", "SMS, Hindi Devanagari, machine-translated from UCI"),
}


def build_pipeline():
    """TF-IDF word 1-2 grams + char_wb 3-5 grams (FeatureUnion) -> LogisticRegression(C=10, liblinear)."""
    features = FeatureUnion([
        ("word", TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2), sublinear_tf=True,
                                 min_df=2, max_features=200_000, token_pattern=r"(?u)\b\w+\b",
                                 dtype=np.float32)),
        ("char", TfidfVectorizer(preprocessor=normalize_short, analyzer="char_wb", ngram_range=(3, 5),
                                 sublinear_tf=True, min_df=3, max_features=300_000, dtype=np.float32)),
    ])
    clf = LogisticRegression(C=10, max_iter=3000, solver="liblinear")
    return Pipeline([("features", features), ("clf", clf)])


def load():
    """Return (texts, labels, sources) from data/combined.csv.gz, building it first if missing."""
    if not DATA.exists():
        print("data/combined.csv.gz not found -> running prepare_data.py (needs pandas + pyarrow)")
        import prepare_data
        prepare_data.main()
    csv.field_size_limit(10_000_000)
    with gzip.open(DATA, "rt", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return ([r["text"] for r in rows], np.array([int(r["label"]) for r in rows]),
            np.array([r["source"] for r in rows]))


def sample_weights(y, src):
    """Weight 1/sqrt(n) per (dataset, class) cell, rescaled so the weights average 1."""
    w = np.ones(len(y))
    for s in np.unique(src):
        for c in (0, 1):
            m = (src == s) & (y == c)
            if m.any():
                w[m] = 1.0 / np.sqrt(m.sum())
    return w * len(w) / w.sum()


def scores(y, pred):
    """Accuracy / precision / recall / F1 (rounded to 4 d.p.) plus the confusion-matrix counts."""
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"accuracy": round(accuracy_score(y, pred), 4),
            "precision": round(precision_score(y, pred, zero_division=0), 4),
            "recall": round(recall_score(y, pred, zero_division=0), 4),
            "f1": round(f1_score(y, pred, zero_division=0), 4),
            "n": int(len(y)), "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def probe_report(model, verbose=True):
    """Robustness probes: ML alone vs final verdict (ML + red flags + safe signals)."""
    if verbose:
        print("\nRobustness probes (hand-written, never used for training)")
    res = {}
    for g, lst in probes.GROUPS.items():
        pp = model.predict_proba([t for _, t in lst])[:, 1]
        ml_ok, fin_ok, unsure, misses = 0, 0, 0, []
        for (exp, text), q in zip(lst, pp):
            ml_pred = "spam" if q >= 0.5 else "ham"
            verdict, _, _, flags, safe = final_verdict(float(q), text)
            ml_ok += ml_pred == exp
            fin_ok += verdict == exp
            unsure += verdict == "unsure"
            if verdict != exp or ml_pred != exp:
                misses.append({"expected": exp, "ml_probability": round(float(q), 3),
                               "ml_correct": ml_pred == exp, "final_verdict": verdict,
                               "red_flags": [f["id"] for f in flags],
                               "safe_signal": [s["id"] for s in safe["signals"]] if safe["applies"] and not flags else [],
                               "text": text})
        res[g] = {"total": len(lst), "ml_correct": ml_ok, "final_correct": fin_ok,
                  "final_unsure": unsure, "misses": misses}
        if verbose:
            print(f"  {g:<28} ML only {ml_ok:>2}/{len(lst):<3} final {fin_ok:>2}/{len(lst)}"
                  + (f"  ({unsure} unsure)" if unsure else ""))
    return res


def main():
    """Split per dataset (80/20, stratified, seed 42), fit, evaluate, run probes, save model + metrics."""
    t0 = time.time()
    texts, y, src = load()
    print(f"Loaded {len(texts)} messages from {len(set(src))} datasets")
    idx = np.arange(len(texts))
    tr_idx, te_idx = [], []
    for s in sorted(set(src)):
        m = idx[src == s]
        a, b = train_test_split(m, test_size=0.2, stratify=y[m], random_state=SEED)
        tr_idx.extend(a); te_idx.extend(b)
    tr_idx, te_idx = np.array(tr_idx), np.array(te_idx)

    model = build_pipeline()
    print("Fitting (TF-IDF word + char n-grams -> Logistic Regression) ...")
    model.fit([texts[i] for i in tr_idx], y[tr_idx],
              clf__sample_weight=sample_weights(y[tr_idx], src[tr_idx]))
    print(f"  done in {time.time() - t0:.0f}s, {len(model.named_steps['features'].get_feature_names_out())} features")

    p = model.predict_proba([texts[i] for i in te_idx])[:, 1]
    pred = (p >= 0.5).astype(int)
    per_ds = {}
    print("\nHeld-out test metrics (threshold 0.5)")
    print(f"  {'dataset':<13} {'n':>6} {'acc':>7} {'prec':>7} {'rec':>7} {'f1':>7}")
    for s in sorted(set(src)):
        m = src[te_idx] == s
        per_ds[s] = scores(y[te_idx][m], pred[m])
        r = per_ds[s]
        print(f"  {s:<13} {r['n']:>6} {r['accuracy']:>7.4f} {r['precision']:>7.4f} {r['recall']:>7.4f} {r['f1']:>7.4f}")
    overall = scores(y[te_idx], pred)
    sms_like = np.isin(src[te_idx], ["sms", "india_sms", "india_2011", "hindi_mt"])
    groups = {"all": overall,
              "sms_all": scores(y[te_idx][sms_like], pred[sms_like]),
              "email_all": scores(y[te_idx][np.isin(src[te_idx], ["enron", "spamassassin"])],
                                  pred[np.isin(src[te_idx], ["enron", "spamassassin"])])}
    for k, r in groups.items():
        print(f"  {k:<13} {r['n']:>6} {r['accuracy']:>7.4f} {r['precision']:>7.4f} {r['recall']:>7.4f} {r['f1']:>7.4f}")

    probe_res = probe_report(model)

    ex = Explainer(model)
    top_spam, top_safe = ex.global_top(20)
    top_spam_w, top_safe_w = ex.global_top(20, kind="word")

    counts = {}
    for s in sorted(set(src)):
        m = src == s
        counts[s] = {"name": DATASET_INFO[s][0], "url": DATASET_INFO[s][1], "type": DATASET_INFO[s][2],
                     "messages": int(m.sum()), "spam": int(y[m].sum()), "ham": int((y[m] == 0).sum())}

    metrics = {
        "model": "TF-IDF (word 1-2 grams + char 3-5 grams) + Logistic Regression",
        "accuracy": overall["accuracy"], "precision": overall["precision"],
        "recall": overall["recall"], "f1": overall["f1"], "n_test": overall["n"],
        "n_train": int(len(tr_idx)), "n_features": int(len(ex.coef)),
        "unsure_band": [0.35, 0.65],
        "per_dataset": per_ds, "groups": groups, "datasets": counts,
        "probes": probe_res,
        "top_spam_features": top_spam, "top_safe_features": top_safe,
        "top_spam_words": top_spam_w, "top_safe_words": top_safe_w,
        "sklearn_version": sklearn.__version__,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    joblib.dump(model, MODEL_FILE, compress=3)
    METRICS_FILE.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"\nSaved {MODEL_FILE.name} ({MODEL_FILE.stat().st_size / 1e6:.1f} MB) and {METRICS_FILE.name} "
          f"in {time.time() - t0:.0f}s total")


if __name__ == "__main__":
    main()
