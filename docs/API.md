# HTTP API

SPAM//SCAN is a small Flask app. This page documents every route. All the JSON responses below were **captured from the running app** (`model.joblib` trained 2026-10-07, scikit-learn 1.9.1). They were captured on a spare local port and are shown here with the default `127.0.0.1:5000`.

← Back to the [README](../README.md) · See also [ARCHITECTURE.md](ARCHITECTURE.md) for how the fields are computed

## Contents

- [Overview](#overview)
- [POST /api/predict](#post-apipredict)
- [GET /api/health](#get-apihealth)
- [GET /api/model-info](#get-apimodel-info)
- [GET /](#get-) and [GET /how-it-works](#get-how-it-works)
- [Errors](#errors)
- [Using the API from code](#using-the-api-from-code)

## Overview

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `POST` | `/api/predict` | JSON | Classify and explain one message |
| `GET` | `/api/health` | JSON | Liveness check |
| `GET` | `/api/model-info` | JSON | `metrics.json`, without the probe miss lists |
| `GET` | `/` | HTML | Scanner UI and Threat Matrix. Supports `?q=` and `?open=` (handled in the browser) |
| `GET` | `/how-it-works` | HTML | Transparency page |

- **Base URL:** `http://127.0.0.1:5000` by default. Change it with the `HOST` and `PORT` environment variables.
- **No authentication, no rate limiting, no CORS headers.** It's meant to run on your own machine. Don't expose it to the internet as it is (see [SECURITY.md](../SECURITY.md)).
- Responses are UTF-8 JSON with keys in a fixed order (`sort_keys = False`) and non-ASCII characters left as they are (`ensure_ascii = False`), so Hindi text stays readable.
- Nothing is stored. Each request is independent.

## POST /api/predict

Classify one message and return the verdict plus everything needed to explain it.

### Request

```http
POST /api/predict
Content-Type: application/json

{"text": "<the SMS or e-mail text>"}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `text` | string | yes | Must be non-empty after trimming whitespace. At most **10,000** characters (`MAX_CHARS`). |

Other fields are ignored. The body is read with `request.get_json(silent=True)`, so a missing or invalid JSON body is treated like a missing `text` (HTTP 400).

### Response schema (200)

| Field | Type | Description |
|---|---|---|
| `label` | `"spam"` \| `"ham"` | Kept from the first version. `spam` if the verdict is spam, **or** if it is unsure and `spam_probability ≥ 0.5`. |
| `spam_probability` | number 0–1 | ML probability of spam, rounded to 4 decimal places. |
| `confidence` | number 0.5–1 | The ML model's confidence in its own label: `p` if `p ≥ 0.5`, else `1 − p`. |
| `verdict` | `"spam"` \| `"unsure"` \| `"ham"` | **The final verdict** (ML + rules). Use this field. |
| `verdict_reason` | string | One or two sentences on how the verdict was decided. |
| `ml_label` | `"spam"` \| `"ham"` | The ML model alone at a 0.5 threshold. |
| `verdict_display` | string | The title shown in the UI: `Spam`, `Unsure`, `Not spam`, `Not spam (standard alert)`, `Not spam (official link)`, `Not spam (standard alert + official link)`, `Unsure (looks like a standard alert)` or `Unsure (official link)`. |
| `red_flags` | array of objects | Rules that fired: `{id, title, explanation, severity: "high"\|"medium", matched: [string]}`. Empty if none fired. |
| `safe_signals` | array of objects | Safe signals whose pattern matched: `{id, title, explanation, matched: [string]}`. A signal blocked by its own extra condition also has a `rule_specific_block` string. |
| `safe_signal_applied` | boolean | True if a safe signal applied **and** no red flag fired. |
| `safe_signal_blocked_by` | array of strings | Plain-language reasons the safe signal was **not** applied. |
| `top_spam_features` | array (≤ 8) | Features with the largest **positive** contributions: `{feature, type: "word"\|"phrase"\|"char", contribution, words: [string]}`. |
| `top_safe_features` | array (≤ 8) | Features with the most **negative** contributions (same shape). |
| `highlights` | array | `{start, end, text, score}` for each whitespace token of the input whose absolute score is at least 0.02. `start` and `end` are character offsets into the original text. |
| `bias` | number | The model intercept (−3.288). `logit = bias + Σ contributions`. |

See [ARCHITECTURE.md](ARCHITECTURE.md#verdict-decision-logic) for the decision rules and [RULES.md](RULES.md) for every rule `id`.

### Example 1: prize claim → Spam (full response)

```bash
curl -s -X POST http://127.0.0.1:5000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "You have wo 1 million dollars"}'
```

```json
{
  "label": "spam",
  "spam_probability": 0.9193,
  "confidence": 0.9193,
  "verdict": "spam",
  "verdict_reason": "ML model is confident this is spam (92% spam probability), and 1 red-flag rule(s) also fired.",
  "ml_label": "spam",
  "verdict_display": "Spam",
  "red_flags": [
    {
      "id": "prize_claim",
      "title": "Prize / lottery / 'you won' claim",
      "explanation": "Claims you won a lottery, lucky draw, prize or large sum of money. You cannot win a contest you didn't enter.",
      "severity": "high",
      "matched": [
        "wo",
        "million"
      ]
    }
  ],
  "safe_signals": [],
  "safe_signal_applied": false,
  "safe_signal_blocked_by": [],
  "top_spam_features": [
    {
      "feature": "zznum",
      "type": "word",
      "contribution": 0.5431,
      "words": [
        "zznum"
      ]
    },
    {
      "feature": "dollars",
      "type": "word",
      "contribution": 0.4852,
      "words": [
        "dollars"
      ]
    },
    {
      "feature": "lars",
      "type": "char",
      "contribution": 0.2238,
      "words": [
        "dollars"
      ]
    },
    {
      "feature": "million dollars",
      "type": "phrase",
      "contribution": 0.2207,
      "words": [
        "dollars",
        "million"
      ]
    },
    {
      "feature": "lio",
      "type": "char",
      "contribution": 0.1963,
      "words": [
        "million"
      ]
    },
    {
      "feature": "␣zz",
      "type": "char",
      "contribution": 0.1871,
      "words": [
        "zznum"
      ]
    },
    {
      "feature": "you",
      "type": "word",
      "contribution": 0.1791,
      "words": [
        "you"
      ]
    },
    {
      "feature": "llars",
      "type": "char",
      "contribution": 0.1753,
      "words": [
        "dollars"
      ]
    }
  ],
  "top_safe_features": [
    {
      "feature": "wo",
      "type": "word",
      "contribution": -0.2309,
      "words": [
        "wo"
      ]
    },
    {
      "feature": "␣wo␣",
      "type": "char",
      "contribution": -0.0966,
      "words": [
        "wo"
      ]
    },
    {
      "feature": "wo␣",
      "type": "char",
      "contribution": -0.0937,
      "words": [
        "wo"
      ]
    },
    {
      "feature": "have",
      "type": "word",
      "contribution": -0.0893,
      "words": [
        "have"
      ]
    },
    {
      "feature": "␣ha",
      "type": "char",
      "contribution": -0.0811,
      "words": [
        "have"
      ]
    },
    {
      "feature": "zznum million",
      "type": "phrase",
      "contribution": -0.0808,
      "words": [
        "million",
        "zznum"
      ]
    },
    {
      "feature": "␣hav",
      "type": "char",
      "contribution": -0.0451,
      "words": [
        "have"
      ]
    },
    {
      "feature": "hav",
      "type": "char",
      "contribution": -0.0409,
      "words": [
        "have"
      ]
    }
  ],
  "highlights": [
    {
      "start": 0,
      "end": 3,
      "text": "You",
      "score": 0.624
    },
    {
      "start": 4,
      "end": 8,
      "text": "have",
      "score": -0.229
    },
    {
      "start": 9,
      "end": 11,
      "text": "wo",
      "score": -0.37
    },
    {
      "start": 12,
      "end": 13,
      "text": "1",
      "score": 1.472
    },
    {
      "start": 14,
      "end": 21,
      "text": "million",
      "score": 1.411
    },
    {
      "start": 22,
      "end": 29,
      "text": "dollars",
      "score": 2.813
    }
  ],
  "bias": -3.288
}
```

### Example 2: KYC block threat without a link → Spam (medium rule + borderline ML)

```bash
curl -s -X POST http://127.0.0.1:5000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "Your SBI account will be blocked today, update KYC"}'
```

Shortened response: feature lists and highlights are cut, and long `explanation` strings are replaced with `…`.

```json
{
  "label": "spam",
  "spam_probability": 0.6368,
  "confidence": 0.6368,
  "verdict": "spam",
  "verdict_reason": "ML score is borderline (64%) and a red flag was found (KYC / account / SIM block threat), so it is treated as spam.",
  "ml_label": "spam",
  "verdict_display": "Spam",
  "red_flags": [
    {
      "id": "kyc_block",
      "title": "KYC / account / SIM block threat",
      "explanation": "…",
      "severity": "medium",
      "matched": [
        "will be blocked",
        "update KYC"
      ]
    }
  ],
  "safe_signals": [],
  "safe_signal_applied": false,
  "safe_signal_blocked_by": [],
  "top_spam_features": [
    {
      "feature": "your",
      "type": "word",
      "contribution": 0.752,
      "words": [
        "your"
      ]
    },
    {
      "feature": "sbi",
      "type": "word",
      "contribution": 0.5507,
      "words": [
        "sbi"
      ]
    }
  ],
  "top_safe_features": [
    {
      "feature": "update",
      "type": "word",
      "contribution": -0.3779,
      "words": [
        "update"
      ]
    }
  ],
  "highlights": [
    {
      "start": 0,
      "end": 4,
      "text": "Your",
      "score": 1.883
    },
    {
      "start": 5,
      "end": 8,
      "text": "SBI",
      "score": 1.265
    }
  ],
  "bias": -3.288
}
```

### Example 3: borderline message → Unsure

```bash
curl -s -X POST http://127.0.0.1:5000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "Your Netflix payment failed. Update your payment method to continue watching."}'
```

Shortened response:

```json
{
  "label": "ham",
  "spam_probability": 0.4186,
  "confidence": 0.5814,
  "verdict": "unsure",
  "verdict_reason": "ML score is borderline (42%) and no red flags were found. Use your judgement.",
  "ml_label": "ham",
  "verdict_display": "Unsure",
  "red_flags": [],
  "safe_signals": [],
  "safe_signal_applied": false,
  "safe_signal_blocked_by": [],
  "top_spam_features": [
    {
      "feature": "your",
      "type": "word",
      "contribution": 0.8582,
      "words": [
        "your"
      ]
    },
    {
      "feature": "payment",
      "type": "word",
      "contribution": 0.285,
      "words": [
        "payment"
      ]
    }
  ],
  "top_safe_features": [
    {
      "feature": "watching",
      "type": "word",
      "contribution": -0.3005,
      "words": [
        "watching."
      ]
    }
  ],
  "highlights": [
    {
      "start": 0,
      "end": 4,
      "text": "Your",
      "score": 1.132
    },
    {
      "start": 5,
      "end": 12,
      "text": "Netflix",
      "score": 0.061
    }
  ],
  "bias": -3.288
}
```

### Example 4: genuine bank alert with an official link → Not spam

The ML model is 99.95% sure this is spam, but two independent good signs (the alert format and the official link) and no red flags make it Not spam.

```bash
curl -s -X POST http://127.0.0.1:5000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "Rs 1,250.00 debited from your HDFC Bank a/c XX4521 on 05-10-26 to VPA swiggy@icici. Not you? Report at https://www.hdfcbank.com/fraud or call 18002586161."}'
```

Shortened response:

```json
{
  "label": "ham",
  "spam_probability": 0.9995,
  "confidence": 0.9995,
  "verdict": "ham",
  "verdict_reason": "ML score was 100%, but the message matches a standard alert format (Standard bank debit/credit alert), its link goes only to an official domain (hdfcbank.com), and no red flags were found. Two independent good signs, so it is treated as Not spam even if the ML model is very confident. Never share OTP/PIN.",
  "ml_label": "spam",
  "verdict_display": "Not spam (standard alert + official link)",
  "red_flags": [],
  "safe_signals": [
    {
      "id": "official_link",
      "title": "Link goes only to an official domain",
      "explanation": "…",
      "matched": [
        "hdfcbank.com (HDFC Bank)"
      ]
    },
    {
      "id": "bank_txn_alert",
      "title": "Standard bank debit/credit alert",
      "explanation": "…",
      "matched": [
        "a/c XX4521",
        "debited"
      ]
    }
  ],
  "safe_signal_applied": true,
  "safe_signal_blocked_by": [],
  "top_spam_features": [
    {
      "feature": "call zzphone",
      "type": "phrase",
      "contribution": 0.9001,
      "words": [
        "call",
        "zzphone"
      ]
    },
    {
      "feature": "zzphone zzcaps",
      "type": "phrase",
      "contribution": 0.8527,
      "words": []
    }
  ],
  "top_safe_features": [
    {
      "feature": "zznum zznum",
      "type": "phrase",
      "contribution": -0.2653,
      "words": []
    }
  ],
  "highlights": [
    {
      "start": 0,
      "end": 2,
      "text": "Rs",
      "score": 0.954
    },
    {
      "start": 3,
      "end": 11,
      "text": "1,250.00",
      "score": 0.36
    }
  ],
  "bias": -3.288
}
```

### Example 5: alert format, but blocked → Spam

```bash
curl -s -X POST http://127.0.0.1:5000/api/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "Your SBI a/c XX4521 is debited Rs 9,999. If not done by you, call 9876543210 immediately to block your account."}'
```

Shortened response:

```json
{
  "label": "spam",
  "spam_probability": 0.9983,
  "confidence": 0.9983,
  "verdict": "spam",
  "verdict_reason": "ML model is confident this is spam (100% spam probability). A standard-alert format was detected but not applied (urges you to call a number to avoid blocking ('call 9876543210 immediately to block')).",
  "ml_label": "spam",
  "verdict_display": "Spam",
  "red_flags": [],
  "safe_signals": [
    {
      "id": "bank_txn_alert",
      "title": "Standard bank debit/credit alert",
      "explanation": "…",
      "matched": [
        "a/c XX4521",
        "debited"
      ]
    }
  ],
  "safe_signal_applied": false,
  "safe_signal_blocked_by": [
    "urges you to call a number to avoid blocking ('call 9876543210 immediately to block')"
  ],
  "top_spam_features": [
    {
      "feature": "call zzphone",
      "type": "phrase",
      "contribution": 0.9694,
      "words": [
        "call",
        "zzphone"
      ]
    },
    {
      "feature": "your",
      "type": "word",
      "contribution": 0.7231,
      "words": [
        "your"
      ]
    }
  ],
  "top_safe_features": [
    {
      "feature": "if",
      "type": "word",
      "contribution": -0.3053,
      "words": [
        "if"
      ]
    }
  ],
  "highlights": [
    {
      "start": 0,
      "end": 4,
      "text": "Your",
      "score": 1.068
    }
  ],
  "bias": -3.288
}
```

### Other captured results

| Text | `verdict` | `verdict_display` | `spam_probability` | Red flags |
|---|---|---|---:|---|
| `HDFC Bank: your netbanking will be deactivated. Login to continue: hdfcbnk.com/login` | spam | Spam | 0.4947 | `lookalike_domain` (high): `hdfcbnk.com`, `imitates HDFC Bank` |
| `Rs 450.00 sent to Ramesh Kumar via UPI on 06-Oct. UPI Ref 427815536201. Not you? Call 1800-111-109 - SBI` | unsure | Unsure (looks like a standard alert) | 0.984 | none (`upi_confirmation` applied) |
| `Big Billion Days are LIVE! Up to 80% off on mobiles. Shop now: https://www.flipkart.com` | unsure | Unsure (official link) | 0.99 | none |
| `hey are we still on for dinner tonight?` | ham | Not spam | 0.0156 | none |

## GET /api/health

```bash
curl -s http://127.0.0.1:5000/api/health
```

```json
{"status":"ok","model":"TF-IDF (word 1-2 grams + char 3-5 grams) + Logistic Regression","accuracy":0.9808}
```

Always returns 200 once the app has started. If `metrics.json` is missing, `model` and `accuracy` are `null`.

## GET /api/model-info

Returns `metrics.json`, except that the `probes` entries drop their `misses` lists. The response is about 8 KB.

```bash
curl -s http://127.0.0.1:5000/api/model-info
```

Top-level keys (captured): ``model`, `accuracy`, `precision`, `recall`, `f1`, `n_test`, `n_train`, `n_features`, `unsure_band`, `per_dataset`, `groups`, `datasets`, `top_spam_features`, `top_safe_features`, `top_spam_words`, `top_safe_words`, `sklearn_version`, `trained_at`, `probes``.

Shortened response:

```json
{
  "model": "TF-IDF (word 1-2 grams + char 3-5 grams) + Logistic Regression",
  "accuracy": 0.9808,
  "precision": 0.9853,
  "recall": 0.9672,
  "f1": 0.9762,
  "n_test": 12142,
  "n_train": 48554,
  "n_features": 470995,
  "unsure_band": [0.35, 0.65],
  "per_dataset": { "sms": {"accuracy": 0.9786, "precision": 0.9, "recall": 0.9286, "f1": 0.9141, "n": 1026, "tn": 887, "fp": 13, "fn": 9, "tp": 117}, "…": "…" },
  "groups": { "all": {…}, "sms_all": {…}, "email_all": {…} },
  "datasets": { "sms": {"name": "UCI SMS Spam Collection", "url": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection", "type": "SMS, English (Singapore/UK)", "messages": 5129, "spam": 629, "ham": 4500}, "…": "…" },
  "top_spam_features": [{"feature": "your", "type": "word", "weight": 6.264}, "…"],
  "top_safe_features": ["…"], "top_spam_words": ["…"], "top_safe_words": ["…"],
  "sklearn_version": "1.9.1",
  "trained_at": "2026-10-07T17:22:23+00:00",
  "probes": { "general": {"total": 32, "ml_correct": 29, "final_correct": 31, "final_unsure": 1}, "…": "…" }
}
```

| Key | Meaning |
|---|---|
| `per_dataset.<key>` / `groups.<all\|sms_all\|email_all>` | `accuracy`, `precision`, `recall`, `f1`, `n`, and the confusion counts `tn`, `fp`, `fn`, `tp` on the held-out 20% |
| `datasets.<key>` | `name`, `url`, `type`, `messages`, `spam`, `ham` (after de-duplication) |
| `top_*_features` / `top_*_words` | the top 20 global features by learned weight (`feature`, `type`, `weight`); `*_words` only includes word/phrase features |
| `probes.<group>` | `total`, `ml_correct`, `final_correct`, `final_unsure` |

## GET /

Returns the scanner UI (HTML). Two query parameters are read **by JavaScript in the page**, not by the server:

| Parameter | Effect | Example |
|---|---|---|
| `q` | Puts the text in the input and runs a scan straight away. The boot animation is skipped. | `/?q=You%20have%20wo%201%20million%20dollars` |
| `open` | Opens that Threat Matrix category's drawer. The value is a category `id` from `examples.json`: `upi`, `kyc`, `courier`, `arrest`, `care`, `bec`, `job`, `emergency`, `prize`, `invest`, `loan`, `electricity`, `romance`, `tax`, `kidnap`, `advancefee`, `genuine` or `gray`. | `/?open=gray` |

The text in `?q=` ends up in the URL, which means browser history and the server's request log. Use the text box or the API for anything private.

## GET /how-it-works

Returns the transparency page (HTML). It is built from `metrics.json`, `redflags.RULES`, `redflags.SAFE_RULES` and `domains.OFFICIAL`, and shows the datasets, held-out metrics, probe scores (with misses), the top features, every rule, and the official-domain list.

## Errors

| Situation | Status | Body (captured) |
|---|---|---|
| `text` missing, empty or whitespace-only, or the body is not valid JSON | 400 | `{"error":"Provide a non-empty 'text' string."}` |
| `text` longer than 10,000 characters | 413 | `{"error":"Text too long (max 10000 characters)."}` |
| Wrong method (for example `GET /api/predict`) | 405 | Flask's default HTML "405 Method Not Allowed" page |
| Unknown path | 404 | Flask's default HTML 404 page |

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:5000/api/predict \
     -H "Content-Type: application/json" -d '{"text": "   "}'
# {"error":"Provide a non-empty 'text' string."}
# HTTP 400
```

## Using the API from code

**Python (standard library only):**

```python
import json, urllib.request

def scan(text, base="http://127.0.0.1:5000"):
    req = urllib.request.Request(f"{base}/api/predict", data=json.dumps({"text": text}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)

r = scan("Aapka KYC pending hai, turant link pe click karo warna account band ho jayega")
print(r["verdict"], r["verdict_display"], [f["id"] for f in r["red_flags"]])
```

**Without a server.** Import the same functions the app uses:

```python
import joblib
from explain import Explainer, analyse

explainer = Explainer(joblib.load("model.joblib"))
print(analyse(explainer, "You have wo 1 million dollars")["verdict"])   # spam
```

**JavaScript (browser, same origin):**

```js
const r = await fetch('/api/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                       body: JSON.stringify({ text: 'u won 1 milion dolars' }) });
const data = await r.json();   // data.verdict, data.red_flags, data.highlights ...
```
