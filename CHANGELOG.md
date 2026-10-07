# Changelog

All notable changes to SPAM//SCAN are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

> Versions 0.1–0.12 are **retrospective labels** for the development stages before the first public commit. All of them are contained in `1.0.0` (commit `3d637fb`). "SPAM//SCAN v2" in the UI refers to the redesigned interface (0.7 onwards), not to a release number. The stage contents are summarised from the development history, so the exact boundaries between stages are approximate.

## [1.1.0] – 2026-10-08

### Added
- Production serving: a `Dockerfile` (`python:3.13-slim`, non-root uid 1000, gunicorn `gthread` with 2 workers × 4 threads, `--preload`, port 7860) and a `.dockerignore`.
- Hugging Face Spaces deployment: `deploy/hf/README.md` (Space front matter) and `deploy/hf/deploy.sh` / `deploy.py` (create the Space if needed and upload the app with `huggingface_hub`).
- `docs/DEPLOY.md`, plus a deploy section in the README.

### Changed
- `requirements.txt` now pins exact versions (scikit-learn 1.9.1, numpy 2.5.3, scipy 1.18.1, joblib 1.6.0, Flask 3.1.3) and adds gunicorn 26.2.0 (skipped on Windows). This needs **Python 3.12+**.
- Request bodies over 256 KB are rejected with 413 (`MAX_CONTENT_LENGTH`). Predictions are unchanged.

## [1.0.1] – 2026-10-08

### Added
- Full documentation: a rewritten `README.md`, plus `docs/ARCHITECTURE.md`, `MODEL.md`, `RULES.md`, `API.md`, `TESTING.md`, `UI.md`, `FAQ.md` and `TROUBLESHOOTING.md`.
- `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`, an MIT `LICENSE`, and GitHub issue templates (bug report; false positive / false negative).
- Fresh screenshots of the current UI in `docs/images/`.
- Docstrings for functions that lacked them. There are **no behaviour changes**, and the probe scores are identical before and after.

## [1.0.0] – 2026-10-08

### Added
- First public release on GitHub, containing everything below.

## [0.12] – Official-domain check

### Added
- `domains.py`: an allowlist of **96 official domains** (banks, UPI apps, telecoms, couriers, shops, government), with `*.gov.in`, `*.nic.in`, `*.bank.in` and `.sbi` treated as official. Exact-or-subdomain matching, and handling of the `user@host` trick.
- Look-alike detection: brand tokens, digit swaps (`0→o`, `1→i/l`, …) and one-typo fuzzy matching (`hdcfbank`, `flipkrat`).
- New rules: `lookalike_domain` (high) and `brand_link_mismatch` (medium).
- New safe signal: `official_link`. Alert format + official link gives *Not spam* even when the ML score is very high.
- Probe group `india:official_domains` (29 messages) and 43 domain-matcher unit cases.

### Changed
- `suspicious_link` ignores links to official domains, and `kyc_block` drops to medium when its only link is official.
- The original 138 probes went from 129 to 131 correct, and the new group scores 28/29. No genuine probe turned into Spam.

## [0.11] – KYC rule

### Changed
- `kyc_block` gained a second form. A block/suspension **threat** plus a KYC/PAN/Aadhaar update **demand** fires as **medium** even without a link, and as high with one. Misspellings (`blokd`, `updte`, `expird`) and Hinglish (`band ho jayega`) are covered. A branch/visit mention switches the no-link form off.
- "Your SBI account will be blocked today, update KYC" went from *Unsure* (ML 64%) to *Spam*.
- *Expired* alone (with a link or number) still counts as a KYC red flag, on purpose.
- The Gray zone was refilled with new borderline examples.

## [0.10] – Gray zone

### Added
- The yellow `???` **Gray zone** tile in the Threat Matrix: borderline messages that land in *Unsure* (the ghost). Each counts as correct while it stays Unsure.

## [0.9] – Sound effects and verdict characters

### Added
- Web Audio sound effects (no audio files) with an `[ SFX: ON/OFF ]` toggle saved in `localStorage`.
- Original inline-SVG characters: a neon **skull** for Spam, a floating **angel** for Not spam, and a glitchy **ghost** (`.phantom`) for Unsure.

## [0.8] – Threat Matrix

### Changed
- The scrolling example list was replaced by the **Threat Matrix**: a no-scroll grid of category tiles with a computed threat level (how often the ML model alone misses that category), a "caught x/y" score, and an accordion drawer.

### Added
- `[ RANDOM PAYLOAD ]` button and the <kbd>R</kbd> shortcut.
- Deep links `/?open=<category>` and `/?q=<text>`.

## [0.7] – Cyberpunk / hacker UI

### Changed
- A full visual redesign as **SPAM//SCAN v2**: neon cyberpunk theme, ASCII logo, boot sequence, Matrix rain, live scan log, glitch and typewriter effects.
- Reduced-motion and high-contrast support. No external assets.

## [0.6] – Example gallery

### Added
- `examples.json`: predefined example messages by fraud category (UPI, KYC, courier, digital arrest, customer care, BEC, job, emergency, prize, investment, loan, electricity, sextortion, tax), plus **family kidnap** and the classic **Nigerian prince / 419** scam, and genuine messages. Each is tagged with a language (English, Hinglish, Hindi, misspelled).

## [0.5] – Standard bank-alert rule

### Added
- **Safe signals**, the "looks like a standard transactional alert" rules: bank debit/credit alert, UPI confirmation, OTP notice, courier update, official e-challan, KYC-complete notice and expense approval. Each has blockers (any red flag, non-official link, short link, PIN/OTP request, payment request, "call to avoid blocking").
- Probe group `india:alert_lookalike_scams`, to check that scams copying alert formats are still caught.

## [0.4] – Transparency

### Added
- Exact per-prediction explanations: word highlighting, top spam- and safe-leaning features with their contributions, and the score arithmetic.
- `/how-it-works` page generated from `metrics.json` (datasets, per-dataset metrics, probes, top features, rules, limitations).
- API fields `verdict`, `verdict_reason`, `ml_label`, `red_flags`, `top_*_features`, `highlights` and `bias`. `label`, `spam_probability` and `confidence` are unchanged.

## [0.3] – Indian scam rules

### Added
- Hand-written red-flag rules for Indian scams: UPI PIN to receive, KYC/SIM block, parcel fee, digital arrest, fake customer care, CEO fraud/BEC, job fee, emergency money, electricity disconnection, prize claims and OTP requests. Each rule is tolerant of misspellings and Hinglish.
- Verdict logic that combines the ML score with the rules (high rules override the ML score, and medium rules count when the ML score is borderline).
- Probe groups for each Indian scam category.

## [0.2] – Robust retrain

### Changed
- Retrained on **7 public datasets** (60,696 messages after de-duplication): UCI SMS, Enron-Spam, SpamAssassin, Deysi, Indian Telecom SMS, IIIT-Delhi 2011 (English + Hinglish) and machine-translated Hindi.
- Added character 3–5-gram features and text normalisation (URL, phone, money and number placeholders) for misspellings, obfuscation and Hinglish. The classifier is logistic regression with per-dataset sample weights.
- Fixed user-reported misses such as "You have wo 1 million dollars" (previously *Not spam* at 22%).
- Added hand-written robustness probes for misspellings and Hinglish/Hindi.

## [0.1] – Initial model

### Added
- First version: an SMS spam classifier (scikit-learn) served by a Flask web app on `127.0.0.1:5000`, with a JSON API returning `label`, `spam_probability` and `confidence`.
