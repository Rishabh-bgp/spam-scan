#!/usr/bin/env bash
# Deploy SPAM//SCAN to a Hugging Face Docker Space.
#
# Usage:
#   HF_TOKEN=hf_xxx deploy/hf/deploy.sh [SPACE_ID] [--dry-run] [--no-wait]
#
#   SPACE_ID   defaults to <your-hf-username>/spam-scan (username looked up from the token)
#   --dry-run  only list the files that would be uploaded (still needs HF_TOKEN for the username)
#   --no-wait  don't wait for the Space to finish building
#
# The token needs WRITE access (classic "write" token, or fine-grained with
# "write access to contents/settings of all repos under your personal namespace").
# huggingface_hub is installed into a separate tools venv (default
# ~/.cache/spam-scan/hf-tools, override with HF_TOOLS_VENV), never into the app's .venv.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
TOOLS_VENV="${HF_TOOLS_VENV:-$HOME/.cache/spam-scan/hf-tools}"

if [ -z "${HF_TOKEN:-}" ]; then
  echo "error: HF_TOKEN is not set. Create a write token at https://huggingface.co/settings/tokens" >&2
  exit 1
fi

PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python

if [ ! -x "$TOOLS_VENV/bin/python" ]; then
  echo "Creating tools venv at $TOOLS_VENV ..."
  "$PY" -m venv "$TOOLS_VENV"
fi
if ! "$TOOLS_VENV/bin/python" -c "import huggingface_hub" >/dev/null 2>&1; then
  echo "Installing huggingface_hub into the tools venv ..."
  "$TOOLS_VENV/bin/python" -m pip install --quiet --upgrade pip
  "$TOOLS_VENV/bin/python" -m pip install --quiet "huggingface_hub>=1.0,<3"
fi

export HF_HUB_DISABLE_TELEMETRY=1
exec "$TOOLS_VENV/bin/python" "$HERE/deploy.py" --repo-root "$REPO_ROOT" "$@"
