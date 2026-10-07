# Contributing to SPAM//SCAN

Thank you for helping make SPAM//SCAN better. Every kind of help is welcome, from reporting one wrong verdict to adding a new rule.

## Ways to help

| You have… | Please… |
|---|---|
| A message that got the **wrong verdict** | Open a **False positive / false negative** issue (template provided). This is the most useful thing you can do. |
| A bug, crash or UI glitch | Open a **Bug report** issue. |
| A missing **official domain** (bank, wallet, courier, government) | Open an issue or a PR. Include a source that proves the organisation owns it. |
| A new **scam pattern** | Open an issue with 3–5 example messages, or a PR with a rule and probes. |
| Better docs or translations | Send a PR. Small fixes are very welcome. |

## Privacy first: anonymise messages

Before you paste **any** real message into an issue, PR, probe or example:

- Replace phone numbers with `98XXXXXX12`, account and card numbers with `XX1234`, and names with made-up ones.
- **Remove OTPs, UPI IDs, links with tracking tokens, addresses and e-mail addresses.**
- Keep the wording, spelling mistakes and structure, since those are what the model and rules see.

Issues are public. Don't post anything you wouldn't want the whole internet to read.

## Development setup

```bash
git clone https://github.com/Rishabh-bgp/spam-scan.git
cd spam-scan
python3 -m venv .venv && source .venv/bin/activate     # Windows: py -3 -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python app.py                                          # http://127.0.0.1:5000
```

You only need `pip install -r requirements-data.txt` if you want to rebuild the dataset or retrain.

## Before you open a pull request

1. **Run the probes** and include the before/after numbers in your PR:

   ```bash
   python probes.py                                                          # ML-only + domain matcher
   python -c "import joblib, train; train.probe_report(joblib.load('model.joblib'))"   # final verdicts
   ```

   No `ham` probe should turn into Spam, and the domain matcher must stay at 100%.
2. **Add probes** for what you changed: the scam, **and** a genuine message that looks like it. See [docs/TESTING.md](docs/TESTING.md#how-to-add-probes).
3. **Restart the app** and try your messages in the UI. Check the rule's explanation reads well on the result card.
4. **Keep it explainable.** Every rule needs an `id`, a short title and a plain-language explanation. Prefer several narrow pattern groups to one broad regex.
5. **Don't change `textnorm.py` without retraining.** The shipped model calls it at prediction time.
6. **If you retrain**, commit `model.joblib` and `metrics.json` together, and say so in the PR. Note the scikit-learn version.
7. **Update the docs** if behaviour changes: [docs/RULES.md](docs/RULES.md) for rules, [docs/API.md](docs/API.md) for API fields, and [CHANGELOG.md](CHANGELOG.md).

## Style

- Python 3.12+ (the pinned numpy/scipy need it), standard library plus the packages in `requirements*.txt`. Keep functions small and add a one-line docstring.
- Regular expressions: case-insensitive, with `\b` boundaries for short words. Comment anything non-obvious.
- Templates: no external CDNs, fonts or trackers. Respect `prefers-reduced-motion`. Every new control must work with the keyboard.
- Gallery and probe messages: fake numbers and domains only (`98XXXXXX12`, `*.xyz`, `example.com`).

## Commit messages

Use the imperative mood with a short summary line, for example `Add DTDC look-alike cases to domain probes` or `Fix kyc_block firing on "visit branch" notices`.

## Code of conduct

Be kind and assume good intent. Harassment, or sharing someone else's private messages without consent, isn't acceptable here.

## Licence

By contributing, you agree that your contributions are licensed under the project's [MIT License](LICENSE).
