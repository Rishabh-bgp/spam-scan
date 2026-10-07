# The machine-learning model

This page covers the datasets, preprocessing, features, classifier, training procedure and evaluation, and how to retrain the model. Every number here comes from `metrics.json`, from the code, or from a run on the shipped `model.joblib`.

← Back to the [README](../README.md) · See also [ARCHITECTURE.md](ARCHITECTURE.md), [TESTING.md](TESTING.md)

## Contents

- [At a glance](#at-a-glance)
- [Datasets](#datasets)
- [Data preparation](#data-preparation-prepare_datapy)
- [Text normalisation](#text-normalisation-textnormpy)
- [Features](#features)
- [Classifier](#classifier)
- [Training procedure](#training-procedure-trainpy)
- [Evaluation](#evaluation)
- [What the model learned](#what-the-model-learned)
- [How to retrain](#how-to-retrain)
- [Caveats](#caveats)

## At a glance

| | |
|---|---|
| Pipeline | `FeatureUnion(TF-IDF word 1–2 grams, TF-IDF char_wb 3–5 grams)` → `LogisticRegression` |
| Features | **470,995** (200,000 word/phrase + 270,995 character n-grams) |
| Training / test messages | 48,554 / 12,142 (80/20 stratified split *within each dataset*, seed 42) |
| Held-out accuracy / F1 | **0.9808 / 0.9762** (precision 0.9853, recall 0.9672) |
| Intercept (bias) | −3.288 |
| scikit-learn | 1.9.1 (`metrics.json` → `sklearn_version`) |
| Trained at | 2026-10-07 17:22:23 UTC (22:52 IST) |
| File | `model.joblib`, about 8.2 MB (joblib, `compress=3`) |

## Datasets

Seven real, public datasets were used. No synthetic or template-generated data went in. Two candidate datasets (`CloveAI/india-spam-sms` and `alusci/sms-otp-spam-dataset`) were looked at and deliberately **not** used, because they are synthetic or template-generated.

| Key | Dataset | Kind | Messages | Spam | Ham | Licence |
|---|---|---|---:|---:|---:|---|
| `sms` | [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) | SMS, English (Singapore/UK) | 5,129 | 629 | 4,500 | CC BY 4.0 |
| `enron` | [Enron-Spam (preprocessed by M. Wiechmann)](https://github.com/MWiechmann/enron_spam_data) | E-mail, English | 30,089 | 14,537 | 15,552 | GPL-3.0 (CSV repo). Original: see source |
| `spamassassin` | [Apache SpamAssassin public corpus](https://spamassassin.apache.org/old/publiccorpus/) (`easy_ham`, `easy_ham_2`, `hard_ham`, `spam`, `spam_2`) | E-mail, English (headers stripped) | 5,785 | 1,677 | 4,108 | No explicit licence; see source |
| `deysi` | [Deysi/spam-detection-dataset](https://huggingface.co/datasets/Deysi/spam-detection-dataset) (train + test) | Mixed short texts/posts, English | 10,653 | 5,498 | 5,155 | Apache-2.0 |
| `india_sms` | [Indian Telecom SMS Spam Collection](https://github.com/junioralive/india-spam-sms-classification) | SMS, Indian English (+ some Hinglish) | 2,001 | 728 | 1,273 | MIT |
| `india_2011` | IIIT-Delhi crowdsourced Indian SMS (Yadav et al. 2011), [GitHub mirror](https://github.com/princebari/-SMS-Spam-Classification-on-Indian-Dataset-A-Crowdsourced-Collection-of-Hindi-and-English-Messages) | SMS, Indian English + Hinglish | 1,932 | 965 | 967 | Not stated; see source |
| `hindi_mt` | [SMS Spam Multilingual Collection](https://huggingface.co/datasets/dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset), `text_hi` column | SMS, Hindi (Devanagari), machine-translated from UCI | 5,107 | 630 | 4,477 | GPL |
| **Total** | | | **60,696** | **24,664** | **36,032** | |

The counts are **after** cleaning and cross-dataset de-duplication. The licences were checked on the source pages in October 2026. Please confirm them yourself before reusing a dataset.

## Data preparation (`prepare_data.py`)

1. **Download** every source into `data/raw/` (about 40 MB). Files that already exist are skipped.
2. **Parse**:
   - SMS sets are read from their TSV or CSV files.
   - Enron is read from its CSV, as `Subject + "\n\n" + Message`.
   - SpamAssassin messages are parsed with Python's `email` package. The **headers are dropped**, and only the decoded Subject and body are kept. The `text/plain` parts are preferred, and HTML-only mail is converted to text.
   - Deysi is read from parquet, which needs `pandas` and `pyarrow`.
3. **Clean**: `\r` is removed, runs of spaces and tabs are collapsed, blank lines are squeezed, and each message is **truncated to 4,000 characters**. The start of a long e-mail carries most of the signal.
4. **De-duplicate across all sources**. The key is the lower-cased text with every run of non-word characters replaced by one space. The first occurrence wins, in this order: `sms`, `enron`, `spamassassin`, `deysi`, `india_sms`, `india_2011`, `hindi_mt`. Keys shorter than 2 characters are dropped.
5. **Write** `data/combined.csv.gz` with the columns `text`, `label` (1 = spam, 0 = ham) and `source`. It is about 16 MB and git-ignored.

## Text normalisation (`textnorm.py`)

`normalize()` is the `preprocessor` of the word vectoriser. `normalize_short()` is the same text cut to 1,500 characters, and it feeds the more expensive character vectoriser. Both are imported by `model.joblib`, so **`textnorm.py` must stay importable and keep the same behaviour** for the shipped model to work.

Steps, in order:

1. Truncate to 6,000 characters.
2. **Undo Enron's pre-tokenisation**: `don ' t` → `don't`, `word .` → `word.`, `1 , 000` → `1,000`, `$ 1` → `$1`.
3. Count ALL-CAPS words (3 or more capital letters) **before** lower-casing.
4. Replace the variable parts of a message with stable placeholder tokens:

| Token | Replaces | Pattern (simplified) |
|---|---|---|
| `zzemail` | e-mail addresses | `name@domain.tld` |
| `zzurl` | links | `http(s)://…`, `www.…`, or a bare `domain.tld` for common TLDs (`com net org info biz ly in co io xyz top club online site me us uk ru cn`) |
| `zzmoney` | currency | `$ £ € ₹ ¥`, `rs`, `inr`, `usd`, `eur`, `gbp` |
| `zzphone` | phone numbers | an optional `+`, then 10 or more digits, spaces, `-`, `.`, `()` or masked `X` |
| `zznum` | any other number | `123`, `1,000`, `4.5` |
| `zzcaps` | appended once | if the message had **2 or more** ALL-CAPS words |

5. Collapse whitespace and lower-case.

A real example (output of `normalize`):

```text
in : Win $ 1 , 000 NOW!!! Call +91 98765 43210 or visit www.win-big.xyz, email prize@win.com. FREE ENTRY
out: win zzmoney zznum now!!! call zzphone or visit zzurl email zzemail . free entry zzcaps
```

This way the model learns "contains a link, money amount or phone number" instead of memorising particular URLs and numbers.

## Features

Both vectorisers use `sublinear_tf=True` (1 + log tf), L2-normalised TF-IDF and `float32`, combined with a `FeatureUnion`.

| Name | Settings | Size in the shipped model |
|---|---|---:|
| `word` | `preprocessor=normalize`, `ngram_range=(1, 2)`, `token_pattern=r"(?u)\b\w+\b"` (keeps 1-letter tokens like `u`), `min_df=2`, `max_features=200_000` | 200,000 |
| `char` | `preprocessor=normalize_short`, `analyzer="char_wb"`, `ngram_range=(3, 5)`, `min_df=3`, `max_features=300_000` | 270,995 |

The **character n-grams** (`char_wb` builds n-grams only inside word boundaries, padded with spaces) make the model tolerant of misspellings (`milion`, `winer`), obfuscation (`fr33`, `v1agra`) and Hinglish spelling variants (`jeeto`, `jeete`, `jeeta`).

## Classifier

```python
LogisticRegression(C=10, max_iter=3000, solver="liblinear")   # L2 penalty (default)
```

- `C=10` is weak regularisation, which suits a very sparse, high-dimensional TF-IDF matrix.
- Logistic regression was chosen over a calibrated LinearSVC. The scores were about the same, and LR gives exact per-feature explanations (contribution = TF-IDF value × weight). See the `train.py` docstring.
- The probabilities are the raw LR outputs. They are **not** recalibrated.

## Training procedure (`train.py`)

1. **Load** `data/combined.csv.gz`. If it's missing, `prepare_data.main()` runs first, which needs `requirements-data.txt`.
2. **Split each dataset separately**, 80/20, stratified by label, `random_state=42`. Every dataset gets its own held-out test set, and small Indian sets are guaranteed to appear in the test data.
3. **Sample weights**: every (dataset, class) cell gets the weight `1/√n`, and all weights are rescaled to average 1. This stops the 30k-message Enron corpus drowning out the 2k-message Indian SMS sets, without fully equalising them.
4. **Fit** the pipeline on the training part with `clf__sample_weight`.
5. **Evaluate** on the held-out part at a 0.5 threshold, per dataset and for three groups: `all`, `sms_all` (`sms`, `india_sms`, `india_2011`, `hindi_mt`) and `email_all` (`enron`, `spamassassin`).
6. **Probe report**: every probe group is scored with the ML model alone and with the final verdict. See [TESTING.md](TESTING.md).
7. **Save** `model.joblib` (`compress=3`) and `metrics.json`. The JSON holds the metrics, dataset counts, probe results (including misses), the top 20 global features of each kind, the scikit-learn version and a UTC timestamp.

The shipped model **is** the one trained on the 80% split, so the reported test metrics describe exactly the model you run.

## Evaluation

### Held-out test set (ML model alone, threshold 0.5)

| Test set | n | Accuracy | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| `deysi` | 2,131 | 0.9967 | 0.9964 | 0.9973 | 0.9968 | 4 | 3 |
| `enron` | 6,018 | 0.9794 | 0.9933 | 0.9639 | 0.9784 | 19 | 105 |
| `hindi_mt` | 1,022 | 0.9658 | 0.8824 | 0.8333 | 0.8571 | 14 | 21 |
| `india_2011` | 387 | 0.9690 | 0.9945 | 0.9430 | 0.9681 | 1 | 11 |
| `india_sms` | 401 | 0.9850 | 0.9667 | 0.9932 | 0.9797 | 5 | 1 |
| `sms` | 1,026 | 0.9786 | 0.9000 | 0.9286 | 0.9141 | 13 | 9 |
| `spamassassin` | 1,157 | 0.9767 | 0.9556 | 0.9642 | 0.9599 | 15 | 12 |
| **`sms_all`** | 2,836 | 0.9736 | 0.9433 | 0.9289 | 0.9361 | 33 | 42 |
| **`email_all`** | 7,175 | 0.9790 | 0.9892 | 0.9639 | 0.9764 | 34 | 117 |
| **`all`** | 12,142 | **0.9808** | 0.9853 | 0.9672 | **0.9762** | 71 | 162 |

*Reproduced:* while writing these docs, the split was re-created and the shipped `model.joblib` re-scored. Every figure above matched `metrics.json` exactly.

### Held-out SMS with the full system (ML + rules)

This was a one-off run for this documentation; the code does not save it. The same 2,836 held-out SMS-type messages (`sms_all`) were put through `final_verdict()`:

| True label | → Not spam | → Unsure | → Spam |
|---|---:|---:|---:|
| ham (2,245) | 2,192 | 31 | **22** |
| spam (591) | **38** | 41 | 512 |

Compared with the ML model alone (33 false positives, 42 false negatives on the same messages), the full system makes fewer confident mistakes (22 and 38). In exchange, it sends 72 messages to *Unsure*. The rules were not written with these held-out messages in view.

### Robustness probes

There are 167 hand-written messages. The ML model alone gets **127/167** right, and the final verdict gets **159/167**. The probes were written alongside the rules, so the second figure is optimistic. Details are in [TESTING.md](TESTING.md).

## What the model learned

From `metrics.json` (`top_spam_words`, `top_safe_words`):

- **Towards spam:** `your`, `zznum`, `to zznum`, `re zznum`, `zznum क`, `zzphone`, `call zzphone`, `sms`, `zznum zzcaps`, `click zzurl` …
- **Towards not spam:** `i`, `enron`, `url zzurl`, `zzurl date`, `url`, `data`, `म`, `if`, `u`, `wrote` …

Words like `enron` show the model has partly learned **dataset-specific vocabulary**. A message that mentions Enron looks "safe" because Enron ham is full of it. The full top-20 lists, including character n-grams, are on `/how-it-works` and in `GET /api/model-info`.

## How to retrain

```bash
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements-data.txt      # adds pandas + pyarrow (only needed to (re)build the data)
python prepare_data.py                    # optional: train.py runs it automatically if data/combined.csv.gz is missing
python train.py                           # writes model.joblib + metrics.json and prints the metrics and probe report
```

A full retrain on the author's box (8 CPU cores, Python 3.13, scikit-learn 1.9.1) took **about 2 minutes** (116 s in total, 95 s of it fitting) and peaked at about **1.5 GB** of RAM (max RSS 1,461 MB).

> [!NOTE]
> Retraining with the current code gives **very slightly different** numbers from the shipped model: 470,958 instead of 470,995 features, accuracy 0.9810 instead of 0.9808, and `hindi_mt` F1 0.865 instead of 0.857. The other six datasets and all probe scores come out identical. The most likely cause is that `textnorm.py` was edited after `model.joblib` was trained (its file timestamp is later than the model's). The shipped model and `metrics.json` match each other exactly.

After retraining:

- Restart `app.py`, because the model is loaded once at start-up.
- Run `python probes.py` (see [TESTING.md](TESTING.md)).
- Commit `model.joblib` and `metrics.json` together. `/how-it-works` and the UI status line read `metrics.json`.

**Changing the model.** Edit `build_pipeline()` in `train.py`. Keep a **linear** final step with `coef_` and `intercept_`, and keep the `features` / `clf` step names, because `Explainer` depends on them. If you change `textnorm.py`, you must retrain, since the shipped model calls it at prediction time.

## Caveats

- **Few genuine Indian transactional messages.** Public data has hardly any real bank, UPI or OTP alerts, so the model tends to score them as spam. The safe-signal rules partly make up for this (see [RULES.md](RULES.md)).
- **Hindi is machine-translated UCI SMS.** Its F1 (0.857) is the lowest. `hindi_mt` messages are translations of UCI `sms` messages, and de-duplication only removes *exact* duplicates. A Hindi test message can therefore be the translation of an English training message, which may make the `hindi_mt` score a little optimistic.
- **Old e-mail.** Enron and SpamAssassin are from about 2000–2005. Modern phishing styles are under-represented.
- **Uncalibrated probabilities.** Treat 35–65% as uncertain, as the app does.
- **Bag of n-grams.** The model has no notion of intent or context beyond two-word phrases.
