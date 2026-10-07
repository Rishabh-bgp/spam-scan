# Testing

SPAM//SCAN has no unit-test framework yet. Its tests are **hand-written robustness probes** in [`probes.py`](../probes.py): realistic messages with an expected label, plus unit cases for the domain matcher. None of these messages are used for training.

← Back to the [README](../README.md) · See also [MODEL.md](MODEL.md#evaluation) for the held-out test-set results

## Contents

- [What is tested](#what-is-tested)
- [How to run](#how-to-run)
- [Current scores](#current-scores)
- [Current misses](#current-misses)
- [Reading the numbers honestly](#reading-the-numbers-honestly)
- [Other checks](#other-checks)
- [How to add probes](#how-to-add-probes)

## What is tested

Each probe is a tuple `(expected, message)`, where `expected` is `"spam"` or `"ham"`. They are organised into **13 groups** (`probes.GROUPS`, **167 messages**):

| Group | Probes | What it covers |
|---|---:|---|
| `general` | 32 | Short prize claims (including the user-reported `You have wo 1 million dollars`), obfuscated spam (`G3t fr33 v1agra`), phishing e-mails, Indian scams, crypto, genuine OTPs, bank alerts, order updates, newsletters, work e-mails and casual chat |
| `misspelled` | 26 | Typo-heavy and txt-speak spam (`u won 1 milion dolars`) and normal chat (`sry im runnin late`) |
| `hinglish` | 26 | Roman-script Hinglish and Devanagari Hindi scams and chat |
| `india:upi_phishing` | 6 | "Enter UPI PIN to receive", OLX QR scam, plus a genuine UPI-sent alert and a GPay chat |
| `india:kyc_alert` | 6 | KYC/SIM block scams, plus a genuine branch-KYC reminder and a "KYC verified" notice |
| `india:courier_fee` | 6 | Redelivery fee, customs duty, seized-parcel scams, plus genuine Delhivery tracking and chat |
| `india:digital_arrest` | 6 | CBI, police and customs "digital arrest", TRAI disconnection, plus a genuine e-challan and passport verification |
| `india:fake_customer_care` | 5 | Fake helplines asking for an OTP or AnyDesk, plus genuine support replies |
| `india:ceo_fraud_bec` | 5 | Urgent wire transfers, gift cards, changed bank details, plus genuine PO and expense approvals |
| `india:job_fee` | 6 | Registration-fee and deposit job scams, plus genuine recruiter and HR mails |
| `india:emergency_money` | 6 | "Papa accident", "new number", police-station scams, plus genuine family messages |
| `india:alert_lookalike_scams` | 8 | Scams that **copy genuine alert formats** (masked a/c + PIN request, OTP + link, e-challan on a fake domain…), to check that the safe signals can't be abused |
| `india:official_domains` | 29 | Genuine alerts with **official** links (should be ham), the same alerts with **look-alike** links (spam), brand-named messages that link elsewhere (spam), and scams that add an official link as a **decoy** (must stay spam) |

There are also **43 domain-matcher unit cases** (`probes.DOMAIN_CASES`), each mapping a link to the expected kind (`official`, `lookalike`, `other`, `shortener` or `neutral`). See [RULES.md](RULES.md#unit-cases-a-selection-from-probesdomain_cases-all-43-pass).

## How to run

**ML-only scores and the domain matcher:**

```bash
.venv/bin/python probes.py            # Windows: .venv\Scripts\python.exe probes.py
```

This prints every probe with `ok`/`MISS`, the ML probability, and `(unsure)` when P is in 35–65%. It then prints all domain cases and a summary. `probes.py` scores the **ML model alone** (P ≥ 0.5 means spam).

**Final-verdict scores (ML + rules + safe signals).** These are the numbers that matter to users:

```bash
.venv/bin/python -c "import joblib, train; train.probe_report(joblib.load('model.joblib'))"
```

`train.py` runs the same report at the end of every training run and saves it, with the list of misses, in `metrics.json` → `probes`. The `/how-it-works` page shows it too.

Both commands take a few seconds and need only `requirements.txt`. The training data is **not** needed.

## Current scores

Measured on the shipped `model.joblib` on 2026-10-08. They are identical before and after the documentation commit.

| Group | Probes | ML only | Final verdict | Final *Unsure* |
|---|---:|---:|---:|---:|
| `general` | 32 | 29 | **31** | 1 |
| `misspelled` | 26 | 20 | **22** | 3 |
| `hinglish` | 26 | 22 | **26** | 0 |
| `india:upi_phishing` | 6 | 4 | **5** | 1 |
| `india:kyc_alert` | 6 | 3 | **5** | 0 |
| `india:courier_fee` | 6 | 4 | **6** | 0 |
| `india:digital_arrest` | 6 | 4 | **6** | 0 |
| `india:fake_customer_care` | 5 | 5 | **5** | 0 |
| `india:ceo_fraud_bec` | 5 | 2 | **5** | 0 |
| `india:job_fee` | 6 | 5 | **6** | 0 |
| `india:emergency_money` | 6 | 2 | **6** | 0 |
| `india:alert_lookalike_scams` | 8 | 8 | **8** | 0 |
| `india:official_domains` | 29 | 19 | **28** | 1 |
| **Total** | **167** | **127 (76%)** | **159 (95%)** | 6 |
| Domain-matcher cases | 43 | | **43** | |

Raw output of `python probes.py` (summary lines):

```text
  general     29/32
  misspelled  20/26
  hinglish    22/26
  india:upi_phishing 4/6
  india:kyc_alert 3/6
  india:courier_fee 4/6
  india:digital_arrest 4/6
  india:fake_customer_care 5/5
  india:ceo_fraud_bec 2/5
  india:job_fee 5/6
  india:emergency_money 2/6
  india:alert_lookalike_scams 8/8
  india:official_domains 19/29
  domain cases 43/43
```

## Current misses

These are all 8 final-verdict misses, with nothing hidden:

| Group | Expected | Final | ML P(spam) | Message (shortened) | Why |
|---|---|---|---:|---|---|
| `general` | ham | Unsure | 1.000 | `Rs 1,250.00 debited from your HDFC Bank a/c XX4521 … Call 18002586161.` | Genuine alert with no link. ML ≥ 95%, so the `bank_txn_alert` safe signal can only lower it to Unsure |
| `misspelled` | spam | Unsure | 0.200 | `Ur acount has been suspnded. Verfy ur detials imediately at http://secure-bank-verfy.com` | Only the medium `suspicious_link` fired, and ML is below 35% |
| `misspelled` | spam | Unsure | 0.190 | `Dear costumer ur KYC is expird, updte now or ur acount wil be blokd` | `kyc_block` fired as medium (no link), and ML is below 35% |
| `misspelled` | spam | **Not spam** | 0.217 | `Hot singels in ur area want to met u tonite, reply YES` | Typo-heavy promo: low ML score and no rule for dating spam |
| `misspelled` | spam | Unsure | 0.455 | `Claime ur reward now!! limted time ofer, dont mis out` | Borderline ML, and no prize word that `prize_claim` recognises |
| `india:upi_phishing` | ham | Unsure | 0.984 | `Rs 450.00 sent to Ramesh Kumar via UPI … UPI Ref 427815536201 …` | Genuine alert. ML ≥ 95%, so `upi_confirmation` only lowers it to Unsure |
| `india:kyc_alert` | ham | **Spam** | 0.995 | `Dear Customer, as per RBI guidelines, please complete your periodic KYC update by visiting your nearest HDFC Bank branch…` | **False positive.** No safe signal covers branch-KYC reminders, and ML ≥ 65% |
| `india:official_domains` | ham | Unsure | 0.983 | `Aapka Jio recharge Rs 299 safal raha. Validity 28 din. Details: https://www.jio.com/selfcare` | Official link but no known alert format, and ML ≥ 95% |

All 8 of these are also wrong for the ML model alone. Another 32 probes are wrong for the ML model alone (167 − 127 = 40 in total) but are fixed by the rules or safe signals. The full lists (with `ml_correct: false`) are in `metrics.json` and on `/how-it-works`.

## Reading the numbers honestly

- **The probes were written alongside the rules.** Rules were added or widened after looking at the probe misses, so the "final verdict" column is **optimistic**. Expect lower accuracy on messages nobody has seen.
- **The ML-only column is the fairer test of the model**, and it shows the model alone is weak on modern Indian scams. It gets 2/6 on emergency money and 2/5 on CEO fraud.
- **Small groups.** One message changes a 6-probe group by 17 percentage points.
- **Better independent evidence** is the held-out test set ([MODEL.md](MODEL.md#evaluation)), including the one-off run of the full system on 2,836 held-out SMS (22 false positives, 38 false negatives, 72 Unsure).

## Other checks

- **Threat Matrix gallery.** At start-up, `app.py` runs all 83 `examples.json` messages through the model and rules, and each tile shows its result. Currently every scam tile is fully caught except `SXT` (3/4, the miss is "Hot singels"), `SAFE` scores 7/9 (two genuine alerts come back Unsure), and the Gray zone keeps 8/8 messages in Unsure. See [UI.md](UI.md#threat-matrix).
- **Rules on their own:** `python redflags.py "<message>"` prints which rules fire.
- **Domains on their own:** `python domains.py <link> [<link> ...]` prints how each link is classified.
- **Syntax:** `python -m py_compile *.py`.

## How to add probes

1. Open `probes.py` and add `(SPAM, "…")` or `(HAM, "…")` to the right list (`GENERAL`, `MISSPELLED`, `HINGLISH` or an `INDIA_SCAMS[...]` category). A new key in `INDIA_SCAMS` automatically becomes a new group `india:<key>`.
2. **Use fake details.** Use placeholder numbers (`98XXXXXX12`, or obviously fake ones like `9876543210`), fake domains (`*.xyz`, `example.com`) and made-up names. Never paste a real person's OTP, account number or phone number.
3. **Add the genuine twin.** For every scam, add a genuine message that looks similar. That's what catches false positives.
4. For a new official domain, add `(link, expected_kind)` to `DOMAIN_CASES`.
5. Run both commands from [How to run](#how-to-run). If you changed rules, check that **no `ham` probe became Spam**.
6. If you retrain, `train.py` stores the new probe results in `metrics.json` automatically.
