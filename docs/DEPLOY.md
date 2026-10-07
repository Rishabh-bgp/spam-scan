# Deploying SPAM//SCAN

← Back to the [README](../README.md) · See also [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and [SECURITY.md](../SECURITY.md)

**Live demo:** https://spam-scan.onrender.com (Hugging Face Space, free CPU tier)

## Contents

- [How production serving works](#how-production-serving-works)
- [Run the production server locally](#run-the-production-server-locally)
- [Docker](#docker)
- [Deploying to Hugging Face Spaces](#deploying-to-hugging-face-spaces)
- [Updating the Space](#updating-the-space)
- [Troubleshooting the Space](#troubleshooting-the-space)

## How production serving works

| | Local (`python app.py`, `run.sh`) | Production (Docker / Hugging Face) |
|---|---|---|
| Server | Flask development server | [gunicorn](https://gunicorn.org/) `app:app` |
| Address | `127.0.0.1:5000` | `0.0.0.0:7860` |
| Config | `HOST`, `PORT` env vars | `HOST`, `PORT`, `WEB_CONCURRENCY` (workers, default 2), `GUNICORN_THREADS` (threads per worker, default 4) |

- gunicorn runs with `--preload`, so `model.joblib` (about 8 MB on disk, about 300 MB of RAM including scikit-learn and the gallery stats) is loaded **once** in the master process and shared with the workers through copy-on-write.
- 2 workers × 4 `gthread` threads suits the free Hugging Face hardware (2 vCPU, 16 GB RAM). A prediction takes a few milliseconds, so this handles plenty of traffic.
- The app **writes no files** at runtime: no logs, uploads or caches. Access and error logs go to stdout/stderr. `PYTHONDONTWRITEBYTECODE=1` stops `__pycache__` writes, gunicorn's heartbeat files live in `/dev/shm` and its control socket goes in `$HOME/.gunicorn`. This matters on Hugging Face, where only `/tmp` and the home directory are writable.
- Request bodies over 256 KB are rejected with **413**, as is any `text` over 10,000 characters.
- `requirements.txt` pins exact versions. **scikit-learn must stay at 1.9.1**, the version that pickled `model.joblib`. If you upgrade it, retrain with `python train.py`.

## Run the production server locally

macOS / Linux (gunicorn doesn't run on Windows):

```bash
pip install -r requirements.txt
HOST=127.0.0.1 PORT=7860 gunicorn app:app --bind 127.0.0.1:7860 \
  --workers 2 --threads 4 --worker-class gthread --preload --timeout 60
# open http://127.0.0.1:7860
```

## Docker

```bash
docker build -t spam-scan .
docker run --rm -p 7860:7860 spam-scan
# open http://127.0.0.1:7860
```

The image is based on `python:3.13-slim`, runs as a non-root user (uid 1000) and listens on port 7860. `.dockerignore` keeps `.venv`, `data/`, `docs/`, logs, archives and `.git` out of the build context. Expect the image to be about 420 MB: roughly 125 MB of base image, 285 MB of Python packages (mostly scipy, numpy and scikit-learn) and 8 MB of model.

Override the concurrency with `docker run -e WEB_CONCURRENCY=4 -e GUNICORN_THREADS=8 ...`.

## Deploying to Hugging Face Spaces

The Space uses the **Docker SDK**. Hugging Face reads the Space settings (`sdk: docker`, `app_port: 7860`, title, emoji, licence) from YAML front matter at the top of the Space's `README.md`. That front matter would look messy on GitHub, so the Space has its own README at [`deploy/hf/README.md`](../deploy/hf/README.md), which the deploy script uploads as `README.md`.

1. Create a free account at [huggingface.co](https://huggingface.co/join).
2. Create a **write** token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). For a fine-grained token, allow write access to repos in your personal namespace.
3. From the repository root, run:

   ```bash
   HF_TOKEN=hf_xxxxxxxx deploy/hf/deploy.sh            # creates/updates <your-username>/spam-scan
   HF_TOKEN=hf_xxxxxxxx deploy/hf/deploy.sh me/my-name # or pick a Space id
   HF_TOKEN=hf_xxxxxxxx deploy/hf/deploy.sh --dry-run  # only list the files it would upload
   ```

The script:

- installs `huggingface_hub` into a separate tools venv (`~/.cache/spam-scan/hf-tools`, override with `HF_TOOLS_VENV`), never into the app's `.venv`;
- looks up your username with the token (`/api/whoami-v2`) and stops if the token is read-only;
- creates the **public** Space if it's missing (`create_repo(repo_type="space", space_sdk="docker", exist_ok=True)`);
- uploads the git-tracked runtime files (`*.py`, `templates/`, `model.joblib`, `examples.json`, `metrics.json`, `requirements.txt`, `Dockerfile`, `.dockerignore`, `LICENSE`) plus the Space README, with `upload_folder`. Docs, screenshots, `.github/` and training data are not uploaded;
- waits for the Docker build and prints the live URL, for example `https://<username>-spam-scan.hf.space`.

The first build takes about 3–5 minutes. After that, the Space page is `https://huggingface.co/spaces/<username>/spam-scan`.

> [!NOTE]
> Free Spaces **go to sleep after about 48 hours without visitors** and wake up on the next visit, which takes about a minute. The public app has no authentication or rate limiting (see [SECURITY.md](../SECURITY.md)), so don't paste real personal messages into a shared deployment.

## Updating the Space

Commit your change, then run the same command again. The Hub skips files that haven't changed, and the script removes app files from the Space that no longer exist in the repo. Hugging Face rebuilds automatically. If tracked files have uncommitted changes, the script warns you and uploads the working-tree versions.

## Troubleshooting the Space

- **Build error:** open the Space and click **Logs → Build**. The usual cause is a `requirements.txt` change that has no wheel for Python 3.13.
- **"Application startup failed" / runtime error:** check **Logs → Container**. `model.joblib not found` means the model wasn't uploaded (it must be git-tracked). An `InconsistentVersionWarning` or unpickling error means scikit-learn isn't at 1.9.1.
- **The Space shows "Starting" for a long time:** make sure the README front matter has `app_port: 7860` and the server binds `0.0.0.0` (the Dockerfile's `HOST` default).
- **401 / 403 from the deploy script:** the token is missing, expired or read-only.

## Render (current live deployment)

The live demo runs on Render's free plan at https://spam-scan.onrender.com, defined by `render.yaml` in the repo root
(Python runtime, one gunicorn worker with 4 threads, health check `/api/health`, auto-deploy on every push to `main`).

- One-click deploy of your own copy: https://render.com/deploy?repo=https://github.com/Rishabh-bgp/spam-scan
- Free instances sleep after about 15 minutes without traffic, so the first request after that can take around a minute.

> Note (October 2026): Hugging Face now requires a PRO subscription to host Docker and Gradio Spaces on free CPU hardware,
> so the Hugging Face path above only works on a PRO account.
