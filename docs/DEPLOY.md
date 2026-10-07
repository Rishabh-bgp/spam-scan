# Deploying SPAM//SCAN

← Back to the [README](../README.md) · See also [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and [SECURITY.md](../SECURITY.md)

**Live demo:** [spam-scan.onrender.com](https://spam-scan.onrender.com), running on Render's free plan from [`render.yaml`](../render.yaml).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Rishabh-bgp/spam-scan)

## Contents

- [Options at a glance](#options-at-a-glance)
- [Render (live demo)](#render-live-demo)
- [Docker (any host)](#docker-any-host)
- [Run the production server locally](#run-the-production-server-locally)
- [Hugging Face Spaces (needs PRO)](#hugging-face-spaces-needs-pro)
- [How production serving works](#how-production-serving-works)
- [Troubleshooting deployments](#troubleshooting-deployments)

## Options at a glance

| Option | Cost | Config | Notes |
|---|---|---|---|
| **Render** (primary, live) | Free plan | [`render.yaml`](../render.yaml) Blueprint | 512 MB RAM, sleeps after about 15 idle minutes, auto-deploys on every push to `main` |
| **Docker** (any host) | Depends on the host | [`Dockerfile`](../Dockerfile) | Works on a VPS, Railway, Fly.io, Cloud Run, or Render's Docker runtime |
| Local production server | Free | `gunicorn app:app` | For testing the production setup on macOS / Linux |
| Hugging Face Spaces | Needs a PRO subscription | `Dockerfile` + Space front matter | Not used by this project |

## Render (live demo)

The live demo is a free Render **web service** defined by the [`render.yaml`](../render.yaml) Blueprint in the repo root:

| Setting | Value |
|---|---|
| Runtime | Python, `PYTHON_VERSION=3.13.5` |
| Region | Singapore |
| Build | `pip install -r requirements.txt` |
| Start | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --worker-class gthread --timeout 120` |
| Health check | `/api/health` |
| Auto-deploy | On every push to `main` |

**Deploy your own copy:** click **Deploy to Render** above, sign in to Render (a free account is enough), and approve the Blueprint. Render builds the app and gives you a URL like `https://spam-scan-xxxx.onrender.com`. To deploy from your own fork, use `https://render.com/deploy?repo=https://github.com/<you>/spam-scan`.

Free-plan limits to know about:

- **512 MB of RAM.** One gunicorn worker with the model loaded uses about 330 MB, so the Blueprint runs a **single worker** with 4 threads and no `--preload`. Don't raise `--workers` on the free plan, or the instance will run out of memory.
- **It sleeps after about 15 minutes without traffic.** The next visit wakes it up, which takes around a minute. After that, predictions take a few milliseconds.
- Render sets `PORT` itself, and the start command binds to it. You don't need to set `HOST` or `PORT`.

## Docker (any host)

```bash
docker build -t spam-scan .
docker run --rm -p 8000:8000 spam-scan
# open http://127.0.0.1:8000
```

- The image is based on `python:3.13-slim` and runs as a non-root user (uid 1000). By default gunicorn runs 2 workers × 4 `gthread` threads with `--preload`, on `0.0.0.0:8000`.
- Platforms that inject a `PORT` variable (Render, Railway, Fly.io, Cloud Run) override the default automatically. To pick a port yourself, run `docker run -e PORT=9000 -p 9000:9000 spam-scan`.
- Tune the concurrency with `-e WEB_CONCURRENCY=<workers> -e GUNICORN_THREADS=<threads>`. On a **512 MB** host, use `WEB_CONCURRENCY=1`.
- `.dockerignore` keeps `.git`, `.venv`, `data/`, `docs/`, logs and archives out of the build context. Expect the image to be about 420 MB: roughly 125 MB of base image, 285 MB of Python packages (mostly scipy, numpy and scikit-learn) and the 8 MB model. *(This is an estimate. The image hasn't been measured with a real `docker build`.)*

## Run the production server locally

On macOS / Linux (gunicorn doesn't run on Windows; use `python app.py` there):

```bash
pip install -r requirements.txt
gunicorn app:app --bind 127.0.0.1:8000 --workers 2 --threads 4 --worker-class gthread --preload --timeout 60
# open http://127.0.0.1:8000
```

## Hugging Face Spaces (needs PRO)

As of October 2026, Hugging Face requires a **PRO subscription** to host Docker (and Gradio) Spaces on its CPU hardware. A free account gets *402 Payment Required* when it tries to create the Space. That's why the live demo runs on Render.

If you have PRO, the `Dockerfile` works as-is:

1. Create a Space with the **Docker** SDK and push this repo to it.
2. At the top of the Space's `README.md`, add front matter that tells Hugging Face which port to use:

   ```yaml
   ---
   title: SPAM SCAN
   sdk: docker
   app_port: 8000
   license: mit
   ---
   ```

(An earlier upload script for Spaces was removed in 1.1.0 because a free account can't use it. It's still in the git history at commit `a25c088`.)

## How production serving works

| | Local (`python app.py`, `run.sh`) | Render | Docker |
|---|---|---|---|
| Server | Flask development server | gunicorn, 1 worker × 4 threads | gunicorn, 2 workers × 4 threads, `--preload` |
| Address | `127.0.0.1:5000` | `0.0.0.0:$PORT` (set by Render) | `0.0.0.0:${PORT:-8000}` |
| Config | `HOST`, `PORT` | `render.yaml` | `HOST`, `PORT`, `WEB_CONCURRENCY`, `GUNICORN_THREADS` |

- The model is about 8 MB on disk and about 300–330 MB of RAM per process, including scikit-learn and the gallery stats computed at startup. With `--preload`, Docker loads it once in the master process, and the workers share it through copy-on-write.
- The app **writes no files** at runtime: no logs, uploads or caches. Access and error logs go to stdout/stderr, so read them in your platform's log viewer.
- Request bodies over 256 KB are rejected with **413**, as is any `text` over 10,000 characters.
- `requirements.txt` pins exact versions. **scikit-learn must stay at 1.9.1**, the version that pickled `model.joblib`. If you upgrade it, retrain with `python train.py` and commit the new `model.joblib` and `metrics.json` together.

## Troubleshooting deployments

- **Build fails on `pip install`:** the pinned numpy 2.5.3 and scipy 1.18.1 need **Python 3.12+**. On Render, check that `PYTHON_VERSION` is set (it's 3.13.5 in `render.yaml`).
- **Render shows "Out of memory" / the instance restarts:** use `--workers 1` on the free plan (512 MB).
- **The first request takes about a minute:** the free instance was asleep. This is expected.
- **`model.joblib not found`:** the model must be committed, because the build doesn't train it. Check that `git ls-files model.joblib` lists it.
- **`InconsistentVersionWarning` or an unpickling error at startup:** scikit-learn isn't at 1.9.1. Reinstall from `requirements.txt`.
- **Health check failing:** `GET /api/health` should return `{"status":"ok", ...}`. Check that the server binds `0.0.0.0` and the platform's `PORT`, not `127.0.0.1:5000`.

> [!NOTE]
> A public deployment has no authentication or rate limiting (see [SECURITY.md](../SECURITY.md)). Don't paste real personal messages into a shared instance.
