# Spam Checker: a transparent SMS/email spam and scam classifier

Paste an SMS or email (English, Hinglish or Hindi) and the app shows you:

- **Verdict:** Spam, Unsure, or Not spam, plus a sentence on how it was decided.
- **ML spam probability** from a TF-IDF + Logistic Regression model. Anything between 35% and 65% counts as "unsure".
- **Red flags:** named, hand-written rules for common scams (UPI PIN to receive money, KYC/SIM block (high with a link/number, medium without), parcel fee,
  "digital arrest", fake customer care, CEO fraud, job registration fee, emergency money requests, prize/lottery claims,
  shortened links, kidnap/blackmail extortion, look-alike bank/brand web addresses, and more). Each one shows what it matched.
- **Official-domain check:** every link's real host is checked against an allowlist of official Indian bank, payment-app,
  telecom, courier, shop and government domains (plus any `*.gov.in` / `*.bank.in`). An official link is a good sign; a
  look-alike (`sbi-kyc-update.com`, `hdfcbank.com.verify.xyz`, `1cici.co`) is a high red flag.
- **Why:** each word is highlighted red (pushes toward spam) or green (pushes toward not spam), with the top
  contributing words, phrases and character n-grams and their exact weights.
- **How this model works** at `/how-it-works`: the datasets, per-dataset test metrics, probe results, the top 20 global
  features, the rules, and known limitations.

## Quick start

| OS | Command |
|----|---------|
| macOS / Linux | `./run.sh` |
| Windows | `run.bat` |

The script creates `.venv`, installs the requirements, trains the model if `model.joblib` is missing, and starts
the server. Then open **http://127.0.0.1:5000**.

## Manual setup (Python 3.9+; tested with 3.13 and scikit-learn 1.9.1)

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python train.py      # optional: model.joblib is included. Takes about 2 minutes and 3 GB of RAM.
python app.py
```

**Windows**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python train.py
python app.py
```
If PowerShell blocks `activate`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or just call
`.venv\Scripts\python.exe app.py`. To use another port, set `PORT` (for example `PORT=8000 python app.py`).

`model.joblib` was saved with scikit-learn 1.9.1. If a different version prints warnings or won't load it,
run `python train.py` again.

### Using the web UI
- **Threat matrix**: a grid of 17 scam categories (UPI, KYC, PKG … 419, plus a green SAFE tile for genuine messages)
  and a yellow `???` GRAY tile of borderline messages that land in Unsure (its tile reads "unsure x/y").
  Each tile shows a threat level and "caught x/y", both computed from `examples.json` when the server starts.
  The level comes from how many examples the **ML model alone** catches (LOW = all, MED ≥ 75%, HIGH ≥ 50%, CRIT < 50%).
  "Caught" counts the final verdict, after the red-flag rules. Click a tile to open its drawer, then click a line to
  scan that message. `[ RANDOM PAYLOAD ]`, or pressing **R** when you're not typing, scans a random example.
  `/?open=kyc` opens a drawer and `/?q=<text>` scans a message directly.
- **Sound effects**: short tones made with the Web Audio API (no audio files). They play only after you click or
  press a key. Turn them on or off with `[ SFX: ON/OFF ]` in the header; the setting is saved in your browser.
- **Verdict characters** (original inline SVGs, one per verdict): a neon skull with "!! THREAT DETECTED !!" for
  SPAM, a floating angel with a pulsing halo and "// ALL CLEAR //" for NOT SPAM (including standard alerts), and a
  glitchy ghost with a question mark and "?? ANALYSIS INCONCLUSIVE ??" for UNSURE. If your system asks for reduced
  motion, the characters stay still and the boot screen and matrix rain are turned off.

### Rebuilding the dataset (optional)
`data/combined.csv.gz` (about 16 MB, 60,696 messages) is included. To rebuild it from the original sources:
```bash
pip install -r requirements-data.txt   # adds pandas + pyarrow
python prepare_data.py                 # downloads ~40 MB into data/raw/ and rebuilds combined.csv.gz
python train.py
```

## Data (real, public datasets only)

| Key | Dataset | Kind | Messages (spam / ham) |
|-----|---------|------|-----------------------|
| `sms` | [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) | SMS, English | 5,129 (629 / 4,500) |
| `enron` | [Enron-Spam, preprocessed](https://github.com/MWiechmann/enron_spam_data) | Email | 30,089 (14,537 / 15,552) |
| `spamassassin` | [SpamAssassin public corpus](https://spamassassin.apache.org/old/publiccorpus/) | Email (headers stripped) | 5,785 (1,677 / 4,108) |
| `deysi` | [Deysi/spam-detection-dataset](https://huggingface.co/datasets/Deysi/spam-detection-dataset) | Short texts/posts | 10,653 (5,498 / 5,155) |
| `india_sms` | [Indian Telecom SMS Spam Collection](https://github.com/junioralive/india-spam-sms-classification) (MIT) | Indian SMS | 2,001 (728 / 1,273) |
| `india_2011` | IIIT-Delhi crowdsourced Indian SMS (Yadav, Kumaraguru et al. 2011), [GitHub mirror](https://github.com/princebari/-SMS-Spam-Classification-on-Indian-Dataset-A-Crowdsourced-Collection-of-Hindi-and-English-Messages) | Indian SMS, English + Hinglish | 1,932 (965 / 967) |
| `hindi_mt` | [SMS Spam Multilingual Collection](https://huggingface.co/datasets/dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset), Hindi column (GPL) | UCI SMS machine-translated to Devanagari | 5,107 (630 / 4,477) |

The data is de-duplicated across all sources. Email headers are removed (only the subject and body are kept), and long emails are cut to 4,000 characters.
Synthetic and template-generated datasets I looked at (for example `CloveAI/india-spam-sms` and `alusci/sms-otp-spam-dataset`)
were deliberately **not** used.

## Model
- Text normalisation (`textnorm.py`): URLs, emails, phone numbers, currency and numbers become placeholder tokens, and
  pre-tokenised Enron text is re-joined.
- Features: word 1–2-gram TF-IDF (sublinear tf), plus **character 3–5-gram TF-IDF (`char_wb`)** for misspellings,
  obfuscation (`fr33`) and Hinglish spelling variants. There are about 471k features.
- Classifier: Logistic Regression (C=10). Training uses per-(dataset, class) weights of 1/√n so the large Enron corpus doesn't drown out SMS.
  A calibrated LinearSVC scored about the same. Logistic Regression won because its explanations are exact.
- Each dataset is split 80/20 (stratified). The shipped model is the one trained on the 80% split, so the reported metrics describe it exactly.

Results are in `metrics.json` and on the `/how-it-works` page. Run `python probes.py` to re-score the hand-written probes.

## API
```bash
curl -X POST http://127.0.0.1:5000/api/predict -H "Content-Type: application/json" \
     -d '{"text": "You have wo 1 million dollars"}'
```
These fields are unchanged from v1:
- `label`: `spam`/`ham`. It is now the final verdict, with Unsure resolved by the 50% ML threshold.
- `spam_probability`: the ML probability.
- `confidence`: the ML model's confidence in its own label.

New fields:
- `verdict`: `spam`, `unsure` or `ham`.
- `verdict_reason`: how the verdict was decided.
- `ml_label`: the ML model's label on its own.
- `red_flags`: a list with `id`, `title`, `explanation`, `severity` and `matched`.
- `top_spam_features` and `top_safe_features`: each has `feature`, `type`, `contribution` and `words`.
- `highlights`: character spans of the input, each with a `score`.
- `bias`: the model's intercept.
- `verdict_display`: the title shown in the UI, for example "Not spam (standard alert)".
- `safe_signals`: the safe-signal rules that matched.
- `safe_signal_applied`: whether a safe signal changed the verdict.
- `safe_signal_blocked_by`: plain-language reasons a safe signal wasn't applied.

Other endpoints: `GET /api/health` and `GET /api/model-info`.

## How the verdict is decided
0. **Safe signal ("looks like a standard transactional alert")**: if the message matches a genuine-alert format
   (bank debit/credit alert with a masked a/c, UPI confirmation with a ref no., OTP with "do not share" and no link
   other than the bank's own domain,
   courier status update, e-challan linking only to parivahan.gov.in, KYC-verified notice, expense/PO approval) **and**
   no red flag fired, there is no link to a non-official domain, no shortened link, no request for a PIN/OTP/password/card
   details, no payment/fee request, and no "call to avoid blocking", then the verdict is **Not spam (standard alert)**,
   or **Unsure** if ML ≥ 95%. The UI and API (`safe_signals`, `safe_signal_applied`, `safe_signal_blocked_by`)
   always say why it was or wasn't applied. **Scammers may imitate the format**, so never share an OTP/PIN or pay via a link.
   - **Official link** (`official_link`): every link goes to an allowlisted official domain. On its own it works like the
     formats above (Not spam, or Unsure if ML ≥ 95%), but not if the message also gives a mobile number. Together with an
     alert format it gives **Not spam (standard alert + official link)** even when ML ≥ 95%. It never overrides a red flag:
     an OTP request, digital-arrest threat or UPI-PIN trick with an official link as a decoy is still Spam, and a payment
     request still blocks it.
1. ML ≥ 65% → Spam.
2. Otherwise, any **high** red flag → Spam. The rules override the ML score.
3. Otherwise, a **medium** red flag and ML ≥ 35% → Spam.
4. Otherwise, ML at 35–65% or a medium flag → Unsure.
5. Otherwise → Not spam.

## Official domains and look-alikes (`domains.py`)
- **Allowlist:** exact domain or a real sub-domain only. `netbanking.hdfcbank.com` is HDFC Bank; `hdfcbank.com.evil.xyz`
  (owned by `evil.xyz`), `hdfcbank-kyc.com` and `http://onlinesbi.sbi@evil.xyz` (everything before `@` is decoration) are not.
  Restricted zones `*.gov.in`, `*.nic.in`, `*.bank.in` (RBI's bank-only domain) and SBI's `.sbi` TLD are always official.
  The full list with owners is on `/how-it-works`.
- **`lookalike_domain` (high):** a non-official host that contains a brand name (sbi, hdfc, icici, axis, kotak, pnb, paytm,
  phonepe, amazon, flipkart, jio, airtel, india post, delhivery, uidai, incometax, parivahan, paypal...) or a typo of one
  (digit swaps 0→o 1→i/l 3→e 5→s, rn→m; one-letter typos for long names like hdfcbank/flipkart). Short names
  (sbi, pnb, rbi, jio) only count at the start or end of a word, so "lesbian"/"turbine" don't match.
- **`brand_link_mismatch` (medium):** the message names a brand and asks you to act (verify, claim, pay, track, log in...)
  within ~200 characters of a link to an unrelated domain or a URL shortener.
- Brand short links (`amzn.to`, `fkrt.it`, `paytm.me`) and `amazonaws.com` are neutral: neither good nor look-alike.
- If the only link in a KYC/account-block message is official (and there's no phone number), the KYC rule is medium, not high.
- Tests: `python probes.py` runs the message probes (group `india:official_domains`) and 43 domain-matcher unit cases.

## Known limitations
- **False positives on real transactional SMS.** The ML model often scores bank debit alerts, OTPs, KYC reminders and
  courier updates high, because there's almost no public data of genuine Indian transactional messages. The safe-signal
  rules fix the common formats, but alerts the ML model is ≥ 95% sure about only drop to Unsure, and uncovered
  formats (for example a branch-KYC reminder) can still show as Spam.
- **Little real Hinglish data.** There are a few hundred real messages. The Devanagari data is machine-translated, and its quality is poor.
- Newer scam types (digital arrest, CEO fraud, emergency-money texts) are rare in public data, so the rules
  catch them, not the ML model. The rules were written while looking at the probe messages, so probe scores that include rules are optimistic.
- The email corpora are from 2000–2005.
- **The domain allowlist is hand-made.** A genuine domain that isn't listed but contains a brand name (a bank's sister
  company, a new campaign site) is flagged as a look-alike. Punycode / non-Latin look-alike letters and brand names hidden in
  the link *path* (`evil.xyz/hdfcbank.com`) aren't caught by the look-alike rule. Genuine messages with an official link but
  no known alert format (e.g. a Jio recharge confirmation the ML scores 98%) still only reach Unsure.

## Files
| File | Purpose |
|------|---------|
| `app.py` | Flask server: UI, `/how-it-works`, `/api/predict`, `/api/health`, `/api/model-info` |
| `train.py` | Trains, evaluates per dataset and on the probes, saves `model.joblib` and `metrics.json` |
| `prepare_data.py` | Downloads and merges the public datasets into `data/combined.csv.gz` |
| `textnorm.py` | Text normalisation (shared by training and serving) |
| `explain.py` | Per-prediction explanations and verdict logic |
| `redflags.py` | Transparent red-flag rules and safe-signal (standard alert) rules |
| `domains.py` | Official-domain allowlist, link/host extraction and look-alike domain detection |
| `probes.py` | Hand-written robustness probes (tests only, never training data) |
| `examples.json` | Example gallery shown in the UI (18 categories, 81 messages, fake placeholder numbers and links) |
| `templates/` | `index.html`, `how.html`, shared CSS (no external CDNs) |
| `run.sh`, `run.bat` | One-step setup and run |

Dataset credits: Almeida & Gómez Hidalgo (UCI SMS, CC BY 4.0); Metsis, Androutsopoulos & Paliouras (Enron-Spam);
Apache SpamAssassin; Deysi (Hugging Face); junioralive (MIT); Yadav, Kumaraguru, Goyal, Gupta & Naik (IIIT-Delhi, 2011);
rajnathpatel / dbarbedillo (multilingual translations, GPL).
