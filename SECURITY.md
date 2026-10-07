# Security and responsible use

## SPAM//SCAN is an educational tool

SPAM//SCAN is a learning project. It **does not guarantee** that a message is safe or that it is a scam.

- A **Not spam** verdict only means no known warning sign was found. Scammers can copy genuine alerts word for word.
- A **Spam** verdict can be wrong too. Genuine messages are sometimes flagged (see the [limitations](README.md#limitations)).
- **Never share an OTP, UPI PIN, CVV, password or card details, and never pay through a link in a message**, whatever the verdict.
- Check unexpected requests through the organisation's official app or a phone number you already know.
- In India, report cyber fraud on **1930** or at [cybercrime.gov.in](https://cybercrime.gov.in). Report suspicious SMS or calls through **Chakshu** on [sancharsaathi.gov.in](https://sancharsaathi.gov.in).

## Privacy

- The app runs locally and listens on `127.0.0.1` by default. It loads **no external scripts, fonts or trackers**.
- Messages are analysed in memory and **not stored** by the app.
- **Exception:** the `/?q=<text>` deep link puts the message in the URL, so it can end up in browser history and in the Flask console log (`server.log` if you redirect output there). Use the text box or `POST /api/predict` for private messages.
- **Don't paste real personal data into GitHub issues.** Anonymise numbers, names, OTPs and links first (see [CONTRIBUTING.md](CONTRIBUTING.md#privacy-first-anonymise-messages)).

## Deployment

The app uses Flask's **development server** and has no authentication, rate limiting, CSRF protection or TLS. It is meant for `localhost`.

- Setting `HOST=0.0.0.0` exposes it to your network. Only do that on a network you trust.
- To host it publicly, use the production setup in the `Dockerfile` (gunicorn; see [docs/DEPLOY.md](docs/DEPLOY.md)) behind HTTPS. Hugging Face Spaces provides TLS, but there is still no authentication or rate limiting, and `debug` is always off. Request bodies are capped at 256 KB and `text` at 10,000 characters.

## Reporting a vulnerability

If you find a security issue in the code (for example an injection in the templates or a way to crash or abuse the server), please **don't post exploit details publicly**:

1. Use GitHub's **private vulnerability reporting** (*Security → Report a vulnerability*) on [the repository](https://github.com/Rishabh-bgp/spam-scan/security) if it's enabled, or
2. Open an issue that just asks for a private contact, without details.

Wrong verdicts (false positives or negatives) are **not** security vulnerabilities. Please report them with the issue template.

## Supported versions

Only the latest commit on `main` is maintained.
