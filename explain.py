"""Per-prediction explanations and the final verdict logic.

The model is   P(spam) = sigmoid(intercept + sum_j x_j * w_j)
where x_j is a TF-IDF feature value (word/phrase or character n-gram) and w_j is
its learned weight. Each feature's contribution x_j * w_j is exact, so we can
show which features pushed the message towards spam (positive) or towards
not-spam (negative), and map character n-grams back to the words they came from.
"""
import math
import re

import numpy as np

from redflags import check as check_red_flags, safe_signals
from textnorm import normalize

UNSURE_LOW, UNSURE_HIGH = 0.35, 0.65


class Explainer:
    """Exact per-feature explanations for a fitted TF-IDF + LogisticRegression pipeline."""

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.features = pipeline.named_steps["features"]
        clf = pipeline.named_steps["clf"]
        self.coef = np.asarray(clf.coef_).ravel()
        self.intercept = float(np.ravel(clf.intercept_)[0])
        self.names = self.features.get_feature_names_out()
        # "word__free cash" / "char__ fre" -> kind, ngram
        self.kind = np.array([n.split("__", 1)[0] for n in self.names])
        self.gram = np.array([n.split("__", 1)[1] for n in self.names], dtype=object)

    # ---------- global view ----------
    def global_top(self, k=20, kind=None):
        """Top-k features by learned weight: (towards spam, towards not spam). kind = "word" or "char"."""
        idx = np.arange(len(self.coef))
        if kind:
            idx = idx[self.kind == kind]
        order = idx[np.argsort(self.coef[idx])]
        fmt = lambda i: {"feature": self._label(i), "type": self.kind[i],
                         "weight": round(float(self.coef[i]), 3)}
        return ([fmt(i) for i in order[::-1][:k]], [fmt(i) for i in order[:k]])

    def _label(self, i):
        """Readable feature name; spaces in char n-grams are shown as the visible-space symbol."""
        g = self.gram[i]
        return g if self.kind[i] == "word" else repr(g.replace(" ", "␣"))[1:-1]

    # ---------- per-message ----------
    def explain(self, text, k=8):
        """Return (probability, top_spam, top_safe, highlight_spans, intercept) for one message."""
        x = self.features.transform([text]).tocsr()
        idx, vals = x.indices, x.data
        contrib = vals * self.coef[idx]
        logit = self.intercept + float(contrib.sum())
        prob = 1.0 / (1.0 + math.exp(-logit))

        norm_words = normalize(text).split()
        word_scores = [0.0] * len(norm_words)
        feats = []
        for j, c in zip(idx, contrib):
            g, kind = self.gram[j], self.kind[j]
            hits = self._word_hits(g, kind, norm_words)
            for h in hits:
                word_scores[h] += c / len(hits)
            feats.append({
                "feature": self._label(j), "type": "phrase" if kind == "word" and " " in g else kind,
                "contribution": round(float(c), 4),
                "words": sorted({norm_words[h] for h in hits})[:3],
            })
        feats.sort(key=lambda f: f["contribution"])
        top_spam = [f for f in feats[::-1][:k] if f["contribution"] > 0]
        top_safe = [f for f in feats[:k] if f["contribution"] < 0]
        spans = self._spans(text, norm_words, word_scores)
        return prob, top_spam, top_safe, spans, self.intercept

    @staticmethod
    def _word_hits(gram, kind, words):
        """Indices of the normalised words a word/phrase/char n-gram feature came from."""
        if kind == "word":
            toks = gram.split()
            hits = []
            for i, w in enumerate(words):
                wt = re.findall(r"\w+", w)
                if toks[0] in wt:
                    if len(toks) == 1:
                        hits.append(i)
                    elif i + 1 < len(words) and toks[1] in re.findall(r"\w+", words[i + 1]) + wt[wt.index(toks[0]) + 1:]:
                        hits.extend([i, i + 1] if toks[1] not in wt else [i])
            return sorted(set(hits))
        core = gram.strip()
        if not core:
            return []
        hits = []
        for i, w in enumerate(words):
            if gram.startswith(" ") and gram.endswith(" "):
                ok = w == core
            elif gram.startswith(" "):
                ok = w.startswith(core)
            elif gram.endswith(" "):
                ok = w.endswith(core)
            else:
                ok = core in w
            if ok:
                hits.append(i)
        return hits

    @staticmethod
    def _spans(text, norm_words, word_scores):
        """Map normalised-word scores back onto character spans of the original text."""
        score_of = {}
        for w, s in zip(norm_words, word_scores):
            score_of.setdefault(w, []).append(s)
        out = []
        for m in re.finditer(r"\S+", text):
            pieces = normalize(m.group(0)).split()
            vals = [sum(score_of[p]) / len(score_of[p]) for p in pieces if p in score_of]
            s = float(sum(vals)) if vals else 0.0
            if abs(s) >= 0.02:
                out.append({"start": m.start(), "end": m.end(), "text": m.group(0),
                            "score": round(s, 3)})
        return out


def decide(prob, flags, safe=None):
    """Combine the ML probability, red-flag rules and safe signals.
    Returns (verdict, reason, display_title)."""
    safe = safe or {"applies": False, "signals": [], "blocked_by": []}
    high = [f for f in flags if f["severity"] == "high"]
    medium = [f for f in flags if f["severity"] != "high"]
    pct = f"{prob * 100:.0f}%"
    if not flags and safe["applies"]:
        clean = [s for s in safe["signals"] if "rule_specific_block" not in s]
        names = ", ".join(s["title"] for s in clean)
        official = [s for s in clean if s["id"] == "official_link"]
        formats = [s for s in clean if s["id"] != "official_link"]
        hosts = ", ".join(m.split(" (")[0] for s in official for m in s["matched"])
        if official and formats:
            fnames = ", ".join(s["title"] for s in formats)
            return "ham", (f"ML score was {pct}, but the message matches a standard alert format ({fnames}), its link goes "
                           f"only to an official domain ({hosts}), and no red flags were found. Two independent good signs, "
                           f"so it is treated as Not spam even if the ML model is very confident. Never share OTP/PIN."), \
                "Not spam (standard alert + official link)"
        if official and not formats:
            if prob >= 0.95:
                return "unsure", (f"ML model says spam ({pct}), but every link goes to an official domain ({hosts}) and no red "
                                  f"flags were found. ML is very confident and the message doesn't match a known alert "
                                  f"format, so it is marked Unsure. Open the organisation's app or type its address yourself."), \
                    "Unsure (official link)"
            return "ham", (f"ML score is {pct}, but every link goes to an official domain ({hosts}), and there is no red flag, "
                           f"mobile number, payment or PIN/OTP request, so it is treated as Not spam."), "Not spam (official link)"
        if prob >= 0.95:
            return "unsure", (f"ML model says spam ({pct}), but the message matches a standard alert format ({names}) "
                              f"and no red flags were found. ML is very confident, so it is marked Unsure, not Not spam. "
                              f"Check the sender before acting."), "Unsure (looks like a standard alert)"
        if prob >= UNSURE_LOW:
            return "ham", (f"ML score was {pct}, but the message matches a standard alert format ({names}) and no red "
                           f"flags were found, so it is treated as Not spam. Scammers can copy this format; "
                           f"never share OTP/PIN or pay via links."), "Not spam (standard alert)"
        return "ham", (f"ML model says not spam ({pct}), no red flags were found, and the message matches a standard "
                       f"alert format ({names})."), "Not spam (standard alert)"
    if prob >= UNSURE_HIGH:
        reason = f"ML model is confident this is spam ({pct} spam probability)"
        if flags:
            reason += f", and {len(flags)} red-flag rule(s) also fired"
        if safe["signals"]:
            reason += ". A standard-alert format was detected but not applied (" + "; ".join(safe["blocked_by"]) + ")"
        return "spam", reason + ".", None
    if high:
        names = ", ".join(f["title"] for f in high)
        return "spam", (f"Red-flag rule fired ({names}). High-severity rules override the ML score, "
                        f"which was {pct}."), None
    if medium and prob >= UNSURE_LOW:
        return "spam", (f"ML score is borderline ({pct}) and a red flag was found "
                        f"({medium[0]['title']}), so it is treated as spam."), None
    if UNSURE_LOW <= prob < UNSURE_HIGH:
        reason = f"ML score is borderline ({pct}) and no red flags were found. Use your judgement."
        if safe["signals"]:
            reason += " A standard-alert format was detected but not applied (" + "; ".join(safe["blocked_by"]) + ")."
        return "unsure", reason, None
    if medium:
        return "unsure", (f"ML model leans not-spam ({pct}) but a red flag was found "
                          f"({medium[0]['title']}). Be careful."), None
    return "ham", f"ML model says not spam ({pct} spam probability) and no red flags were found.", None


def final_verdict(prob, text):
    """Run the red-flag and safe-signal rules and decide(). Returns (verdict, reason, title, flags, safe)."""
    flags = check_red_flags(text)
    safe = safe_signals(text, flags)
    verdict, reason, title = decide(prob, flags, safe)
    return verdict, reason, title, flags, safe


def analyse(explainer, text, k=8):
    """Full /api/predict response: ML explanation + rules + final verdict."""
    prob, top_spam, top_safe, spans, intercept = explainer.explain(text, k=k)
    verdict, reason, title, flags, safe = final_verdict(prob, text)
    ml_label = "spam" if prob >= 0.5 else "ham"
    return {
        # backward-compatible fields
        "label": "spam" if verdict == "spam" or (verdict == "unsure" and prob >= 0.5) else "ham",
        "spam_probability": round(prob, 4),
        "confidence": round(prob if ml_label == "spam" else 1 - prob, 4),
        # new fields
        "verdict": verdict,
        "verdict_reason": reason,
        "ml_label": ml_label,
        "verdict_display": title or {"spam": "Spam", "ham": "Not spam", "unsure": "Unsure"}[verdict],
        "red_flags": flags,
        "safe_signals": safe["signals"],
        "safe_signal_applied": safe["applies"] and not flags,
        "safe_signal_blocked_by": safe["blocked_by"],
        "top_spam_features": top_spam,
        "top_safe_features": top_safe,
        "highlights": spans,
        "bias": round(intercept, 3),
    }
