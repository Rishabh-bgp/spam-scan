"""Text normalisation shared by train.py and app.py (must be importable when
loading model.joblib).

Replaces things that vary per message but carry the same meaning with stable
placeholder tokens, so the model learns "contains a link / money amount / phone
number" instead of memorising specific URLs or numbers.
"""
import re

_URL = re.compile(
    r"(?:https?://|www\.)\S+"
    r"|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|info|biz|ly|in|co|io|xyz|top|club|online|site|me|us|uk|ru|cn)\b(?:/\S*)?",
    re.I)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_MONEY = re.compile(r"[$£€₹¥]|\b(?:rs|inr|usd|eur|gbp)\b\.?", re.I)
_PHONE = re.compile(r"(?<![\w])\+?\d[\dXx\s().-]{8,}\d(?![\w])")  # X = masked placeholder digits
_NUM = re.compile(r"(?<![a-z0-9])\d+(?:[.,]\d+)*(?![a-z0-9])", re.I)
_CAPS_WORD = re.compile(r"\b[A-Z]{3,}\b")
# Enron-Spam is pre-tokenised ("don ' t", "$ 1 , 000"); undo that so it looks like real text.
_SPACE_PUNCT = re.compile(r"\s+([.,!?;:%)])")
_SPACE_APOS = re.compile(r"(\w)\s+'\s+(\w)")
_SPACE_NUM = re.compile(r"(\d)\s*([.,])\s*(\d)")
_SPACE_CUR = re.compile(r"([$£€₹])\s+(\d)")
_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lower-cased text with URL/EMAIL/PHONE/MONEY/NUM placeholders."""
    if not isinstance(text, str):
        text = str(text)
    text = text[:6000]
    text = _SPACE_APOS.sub(r"\1'\2", text)
    text = _SPACE_PUNCT.sub(r"\1", text)
    text = _SPACE_NUM.sub(r"\1\2\3", text)
    text = _SPACE_CUR.sub(r"\1\2", text)
    caps = len(_CAPS_WORD.findall(text))
    text = _EMAIL.sub(" zzemail ", text)
    text = _URL.sub(" zzurl ", text)
    text = _MONEY.sub(" zzmoney ", text)
    text = _PHONE.sub(" zzphone ", text)
    text = _NUM.sub(" zznum ", text)
    text = _WS.sub(" ", text).strip().lower()
    if caps >= 2:
        text += " zzcaps"
    return text


def normalize_short(text: str) -> str:
    """Same as normalize(), truncated for the (more expensive) character n-grams."""
    return normalize(text)[:1500]
