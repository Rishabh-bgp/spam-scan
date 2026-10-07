---
title: SPAM SCAN
emoji: 💀
colorFrom: green
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Explainable spam & scam detector for Indian SMS/email
tags:
  - spam-detection
  - phishing
  - scikit-learn
  - flask
  - india
  - hinglish
---

# SPAM//SCAN

An explainable spam and scam message classifier for India: paste an SMS, WhatsApp
message or email and get **Spam**, **Not spam** or **Unsure**, with the words that
pushed the model each way and the red-flag rules that fired (UPI collect requests,
KYC blocks, courier/customs fees, "digital arrest", fake customer care, job fees,
lookalike bank domains and more). Works on English, Hinglish, Hindi and misspelled text.

- Model: TF-IDF (word 1-2 grams + char 3-5 grams) + Logistic Regression, trained on ~60k messages (UCI SMS, Enron, SpamAssassin, Indian SMS, Hinglish, Hindi)
- Plus 15 transparent red-flag rules, 8 safe signals and an allowlist of official bank, UPI, courier and government domains
- **Source code, docs and API reference:** https://github.com/Rishabh-bgp/spam-scan

API: `POST /api/predict` with JSON `{"text": "..."}`. See the
[API docs](https://github.com/Rishabh-bgp/spam-scan/blob/main/docs/API.md).

This is a learning/demo project. It can be wrong, so never rely on it alone:
do not share OTPs, PINs or passwords, and report fraud at https://cybercrime.gov.in or call 1930.
