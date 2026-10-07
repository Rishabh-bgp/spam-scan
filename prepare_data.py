"""Download and merge the public spam corpora into data/combined.csv.gz.

Sources (all real, public datasets):
  sms           UCI SMS Spam Collection
  enron         Enron-Spam (preprocessed CSV by MWiechmann, from the AUEB Enron-Spam corpus)
  spamassassin  Apache SpamAssassin public corpus (easy_ham, easy_ham_2, hard_ham, spam, spam_2)
  deysi         Hugging Face "Deysi/spam-detection-dataset" (train + test parquet)
  india_sms     Indian Telecom SMS Spam Collection (github.com/junioralive/india-spam-sms-classification, MIT)
  india_2011    IIIT-Delhi crowdsourced Indian SMS spam set (Yadav, Kumaraguru et al. 2011; English + Hinglish),
                GitHub mirror at github.com/princebari/...-Hindi-and-English-Messages
  hindi_mt      Hindi (Devanagari) column of "SMS Spam Multilingual Collection" on Hugging Face
                (dbarbedillo/..., GPL): the UCI SMS messages machine-translated into Hindi

Output columns: text, label (1 = spam, 0 = ham), source.
Email headers are stripped; only the Subject line and the message body are kept.
Exact duplicates (after whitespace/case normalisation) are removed across all sources.

Needs pandas + pyarrow (see requirements-data.txt). You only need to run this if
data/combined.csv.gz is missing; train.py calls it automatically in that case.
"""
import csv
import email
import email.policy
import gzip
import html
import io
import re
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "combined.csv.gz"
MAX_CHARS = 4000  # long emails are truncated; the start carries most of the signal

SOURCES = {
    "sms.zip": "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
    "enron_spam_data.zip": "https://github.com/MWiechmann/enron_spam_data/raw/master/enron_spam_data.zip",
    "deysi_train.parquet": "https://huggingface.co/api/datasets/Deysi/spam-detection-dataset/parquet/default/train/0.parquet",
    "deysi_test.parquet": "https://huggingface.co/api/datasets/Deysi/spam-detection-dataset/parquet/default/test/0.parquet",
    "india_junioralive.csv": "https://raw.githubusercontent.com/junioralive/india-spam-sms-classification/main/dataset/spam_ham_india.csv",
    "india_precog_2011.csv": "https://raw.githubusercontent.com/princebari/-SMS-Spam-Classification-on-Indian-Dataset-A-Crowdsourced-Collection-of-Hindi-and-English-Messages/HEAD/indian_spam.csv",
    "multilingual_sms.csv": "https://huggingface.co/datasets/dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset/resolve/main/data-augmented.csv",
}
SA_BASE = "https://spamassassin.apache.org/old/publiccorpus/"
SA_FILES = {  # file -> label
    "20030228_easy_ham.tar.bz2": 0,
    "20030228_easy_ham_2.tar.bz2": 0,
    "20030228_hard_ham.tar.bz2": 0,
    "20030228_spam.tar.bz2": 1,
    "20050311_spam_2.tar.bz2": 1,
}
for _f in SA_FILES:
    SOURCES[_f] = SA_BASE + _f


def download_all() -> None:
    """Download every raw source into data/raw/ (files that already exist are skipped)."""
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        dest = RAW / name
        if dest.exists() and dest.stat().st_size > 0:
            continue
        print(f"  downloading {name} ...")
        req = urllib.request.Request(url, headers={"User-Agent": "spam-classifier/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            dest.write_bytes(resp.read())


_TAG_RE = re.compile(r"<[^>]+>")
_STYLE_RE = re.compile(r"<(style|script)[^>]*>.*?</\1>", re.S | re.I)


def html_to_text(s: str) -> str:
    """Very small HTML-to-text converter for HTML-only e-mails (drops style/script and tags)."""
    s = _STYLE_RE.sub(" ", s)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", s, flags=re.I)
    return html.unescape(_TAG_RE.sub(" ", s))


def clean(s: str) -> str:
    """Normalise whitespace and truncate to MAX_CHARS."""
    s = s.replace("\r", "")
    s = re.sub(r"[ \t\f\v]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()[:MAX_CHARS]


def load_sms():
    """Yield (text, label) from the UCI SMS Spam Collection."""
    with zipfile.ZipFile(RAW / "sms.zip") as zf:
        raw = zf.read("SMSSpamCollection").decode("utf-8", errors="replace")
    for line in raw.splitlines():
        label, _, text = line.partition("\t")
        if label in ("ham", "spam") and text.strip():
            yield text, int(label == "spam")


def load_enron():
    """Yield (subject + body, label) from the preprocessed Enron-Spam CSV."""
    import pandas as pd
    with zipfile.ZipFile(RAW / "enron_spam_data.zip") as zf:
        df = pd.read_csv(zf.open("enron_spam_data.csv"))
    for subj, msg, lab in zip(df["Subject"], df["Message"], df["Spam/Ham"]):
        subj = "" if pd.isna(subj) else str(subj)
        msg = "" if pd.isna(msg) else str(msg)
        text = (subj + "\n\n" + msg).strip()
        if text:
            yield text, int(lab == "spam")


def email_body(msg) -> str:
    """Plain-text body of an e-mail (text/plain parts, else text/html converted to text)."""
    parts_plain, parts_html = [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        try:
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "latin-1"
            try:
                txt = payload.decode(charset, errors="replace")
            except LookupError:
                txt = payload.decode("latin-1", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        (parts_plain if ctype == "text/plain" else parts_html).append(txt)
    if parts_plain:
        return "\n".join(parts_plain)
    return "\n".join(html_to_text(h) for h in parts_html)


def load_spamassassin():
    """Yield (subject + body, label) from the SpamAssassin tarballs; headers are dropped."""
    for fname, label in SA_FILES.items():
        with tarfile.open(RAW / fname, "r:bz2") as tf:
            for member in tf.getmembers():
                if not member.isfile() or member.name.split("/")[-1] == "cmds":
                    continue
                data = tf.extractfile(member).read()
                msg = email.message_from_bytes(data, policy=email.policy.compat32)
                subj = str(msg.get("Subject", "") or "")
                try:
                    subj = str(email.header.make_header(email.header.decode_header(subj)))
                except Exception:  # noqa: BLE001
                    pass
                body = email_body(msg)
                text = (subj + "\n\n" + body).strip()
                if text:
                    yield text, label


def load_deysi():
    """Yield (text, label) from the Deysi/spam-detection-dataset parquet files."""
    import pandas as pd
    for f in ("deysi_train.parquet", "deysi_test.parquet"):
        df = pd.read_parquet(RAW / f)
        for text, lab in zip(df["text"], df["label"]):
            if isinstance(text, str) and text.strip():
                yield text, int(lab == "spam")


def _read_csv(path):
    """pandas.read_csv with a latin-1 fallback for files that are not valid UTF-8."""
    import pandas as pd
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")


def load_india_sms():
    """Yield (text, label) from the Indian Telecom SMS Spam Collection."""
    df = _read_csv(RAW / "india_junioralive.csv")
    for text, lab in zip(df["Msg"], df["Label"]):
        if isinstance(text, str) and str(lab).strip() in ("ham", "spam"):
            yield text, int(str(lab).strip() == "spam")


def load_india_2011():
    """Yield (text, label) from the IIIT-Delhi 2011 crowdsourced Indian SMS set."""
    df = _read_csv(RAW / "india_precog_2011.csv")
    for lab, text in zip(df["v1"], df["v2"]):
        if isinstance(text, str) and str(lab).strip() in ("ham", "spam"):
            yield text, int(str(lab).strip() == "spam")


def load_hindi_mt():
    """Yield (text, label) from the Hindi (text_hi) column of the multilingual SMS set."""
    df = _read_csv(RAW / "multilingual_sms.csv")
    for lab, text in zip(df["labels"], df["text_hi"]):
        if isinstance(text, str) and str(lab).strip() in ("ham", "spam"):
            yield text, int(str(lab).strip() == "spam")


def main() -> None:
    """Download, load, clean and de-duplicate all sources, then write data/combined.csv.gz."""
    import email.header  # noqa: F401  (used in load_spamassassin)
    download_all()
    seen = set()
    rows, stats = [], {}
    loaders = {"sms": load_sms, "enron": load_enron,
               "spamassassin": load_spamassassin, "deysi": load_deysi,
               "india_sms": load_india_sms, "india_2011": load_india_2011,
               "hindi_mt": load_hindi_mt}
    for source, loader in loaders.items():
        kept = dup = 0
        for text, label in loader():
            text = clean(text)
            key = re.sub(r"\W+", " ", text.lower()).strip()
            if len(key) < 2:
                continue
            if key in seen:
                dup += 1
                continue
            seen.add(key)
            rows.append((text, label, source))
            kept += 1
        spam = sum(1 for r in rows if r[2] == source and r[1] == 1)
        stats[source] = (kept, spam, dup)
        print(f"  {source:<13} kept {kept:>6} ({spam} spam, {kept - spam} ham), dropped {dup} duplicates")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["text", "label", "source"])
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
