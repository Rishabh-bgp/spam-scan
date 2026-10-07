# SPAM//SCAN - production image (Hugging Face Docker Space compatible)
FROM python:3.13-slim

# Non-root user with uid 1000, as recommended by Hugging Face Spaces.
RUN useradd -m -u 1000 user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOST=0.0.0.0 \
    PORT=7860 \
    WEB_CONCURRENCY=2 \
    GUNICORN_THREADS=4

USER user
WORKDIR $HOME/app

# Install dependencies first so this layer is cached between code changes.
COPY --chown=user requirements.txt .
RUN pip install --user -r requirements.txt

# App code, templates, examples, metrics and the trained model (~8 MB).
COPY --chown=user . .

EXPOSE 7860

# 2 workers x 4 threads suits the free 2 vCPU / 16 GB Space.
# --preload loads model.joblib once in the master before forking (copy-on-write),
# --worker-tmp-dir /dev/shm keeps gunicorn's heartbeat files off the overlay disk.
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
