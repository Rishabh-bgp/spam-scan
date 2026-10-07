# SPAM//SCAN - production container image (works on any Docker host).
# Build:  docker build -t spam-scan .
# Run:    docker run --rm -p 8000:8000 spam-scan     ->  http://127.0.0.1:8000
# The live demo does not use this image: it runs on Render's native Python runtime (render.yaml).
FROM python:3.13-slim

# Run as an unprivileged user (uid 1000) instead of root.
RUN useradd -m -u 1000 user

# PORT: platforms such as Render, Railway, Fly.io or Cloud Run inject their own PORT,
# which overrides the default below. HOST must stay 0.0.0.0 inside a container.
# WEB_CONCURRENCY / GUNICORN_THREADS: gunicorn workers and threads per worker.
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WEB_CONCURRENCY=2 \
    GUNICORN_THREADS=4

USER user
WORKDIR $HOME/app

# Install dependencies first so this layer is cached between code changes.
COPY --chown=user requirements.txt .
RUN pip install --user -r requirements.txt

# App code, templates, examples, metrics and the trained model (~8 MB).
COPY --chown=user . .

EXPOSE 8000

# 2 workers x 4 threads suits a host with 2 vCPUs and >= 1 GB RAM. Each process needs
# roughly 300 MB; on a 512 MB host use -e WEB_CONCURRENCY=1.
# --preload loads model.joblib once in the master before forking (copy-on-write);
# --worker-tmp-dir /dev/shm keeps gunicorn's heartbeat files off the container disk.
CMD exec gunicorn app:app \
    --bind ${HOST}:${PORT} \
    --workers ${WEB_CONCURRENCY} \
    --threads ${GUNICORN_THREADS} \
    --worker-class gthread \
    --preload \
    --timeout 60 \
    --graceful-timeout 20 \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile -
