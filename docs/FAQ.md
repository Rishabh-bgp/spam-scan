# FAQ

← Back to the [README](../README.md)

### Is a "Not spam" verdict safe to trust?

No. It means the model and rules found no known warning sign, and nothing more. Scammers can copy the exact format of a real bank alert. **Never share an OTP, UPI PIN, CVV or password, and never pay through a link in a message**, whatever the verdict says. Check unexpected debits in your bank's own app. In India, report fraud on **1930** or at [cybercrime.gov.in](https://cybercrime.gov.in).

### Why does my genuine bank alert say "Unsure"?

The ML model has seen very little genuine Indian transactional SMS, so it often gives real alerts a score of 95% or more. A safe signal (for example "standard bank debit/credit alert") can then only lower the verdict to **Unsure**, not Not spam. If the alert links to the bank's **official** domain (for example `hdfcbank.com` or `sbi.bank.in`), the combination of format and official link is enough for **Not spam**. See [RULES.md](RULES.md#safe-signals).

### Why was this obvious spam marked "Not spam"?

Usually it's because the message is typo-heavy or uses a style the ML model hasn't learned, **and** no rule covers it. "Hot singels in ur area…" is a known miss. Please open a [false negative issue](https://github.com/Rishabh-bgp/spam-scan/issues/new/choose) with the personal details removed.

### What is the difference between "ML" and "rules"?

- The **ML model** (TF-IDF + logistic regression) learned word and character patterns from about 48,500 labelled messages and outputs a probability.
- The **rules** are hand-written, readable patterns for specific scams (UPI PIN to receive money, KYC block threats, look-alike bank links…) and for genuine alert formats.

The final verdict combines the two in a fixed order. A high-severity rule wins over the ML score. See [ARCHITECTURE.md](ARCHITECTURE.md#verdict-decision-logic).

### What do the percentages mean?

`p(spam)` is the ML model's probability. It isn't recalibrated, so treat it as a score rather than an exact chance. 35–65% is treated as uncertain.

### Does it send my messages anywhere? Does it store them?

No. Everything runs on your computer (`127.0.0.1`). The page loads no external scripts, fonts or trackers. The app keeps nothing on disk, and each request is analysed and forgotten. One exception: if you use the `/?q=` deep link, the message is part of the URL, so it appears in your browser history and in the server's console log.

### Which languages does it support?

It supports English, Hinglish (Hindi in Roman script) and Hindi in Devanagari, including common misspellings. Hindi accuracy is the weakest, because its training data is machine-translated.

### Does it work on e-mails?

Yes. The model was trained on SpamAssassin and Enron e-mail as well as SMS. Paste the subject and body. Headers aren't needed (they're stripped during training anyway). Note that the e-mail data is old (about 2000–2005).

### How accurate is it?

98.1% accuracy (F1 0.976) on 12,142 held-out messages from 7 public datasets, using the ML model alone. On hand-written probes, the full system gets 159/167, but those probes were written alongside the rules, so that figure is optimistic. See [MODEL.md](MODEL.md#evaluation) and [TESTING.md](TESTING.md).

### Can I use it as a library or an API?

Yes. `POST /api/predict` returns everything the UI shows, and you can also import `explain.analyse` directly. See [API.md](API.md#using-the-api-from-code).

### Do I need to train the model?

No. `model.joblib` is included. You only need to retrain if you change the features, `textnorm.py` or the data. See [MODEL.md](MODEL.md#how-to-retrain).

### Why isn't the training data in the repository?

It's about 16 MB compressed (plus about 40 MB of raw downloads), and some datasets have their own licences. `prepare_data.py` downloads everything from the original sources.

### Can I deploy it publicly?

Not as it is. It uses Flask's development server and has no authentication or rate limiting. If you want to host it, put it behind a production WSGI server and a reverse proxy, and read [SECURITY.md](../SECURITY.md) first.

### Can I add my bank's domain or a new scam rule?

Yes, please do. See [RULES.md](RULES.md#how-to-add-an-official-domain) and [CONTRIBUTING.md](../CONTRIBUTING.md).

### Why "SPAM//SCAN v2"?

"v2" refers to the redesigned cyberpunk interface. The project history is in [CHANGELOG.md](../CHANGELOG.md).
