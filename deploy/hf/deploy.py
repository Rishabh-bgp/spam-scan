"""Upload SPAM//SCAN to a Hugging Face Docker Space (called by deploy.sh).

Stages the git-tracked runtime files into a temp folder, swaps in the Space
README (deploy/hf/README.md, which carries the HF YAML front matter), then
creates the Space if needed and uploads with HfApi.upload_folder.
"""
import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from huggingface_hub import HfApi

# Git-tracked files the container needs (plus a few small, useful extras).
ALLOW = ["*.py", "templates/*.html", "examples.json", "metrics.json", "model.joblib",
         "requirements.txt", "Dockerfile", ".dockerignore", "LICENSE"]
# Never upload these even if they match ALLOW.
IGNORE = ["deploy/*", "docs/*", ".github/*", "data/*", ".venv/*", "__pycache__/*", "*.pyc",
          "*.log", "*.tgz", "*.zip", "README.md"]
# Remote files matching these are removed if no longer present locally
# (keeps the Space in sync; never touches .gitattributes or README.md).
DELETE = ["*.py", "templates/*", "*.json", "model.joblib", "requirements.txt",
          "Dockerfile", ".dockerignore", "LICENSE"]


def git_files(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f]


def wanted(path: str) -> bool:
    if any(fnmatch.fnmatch(path, p) for p in IGNORE):
        return False
    return any(fnmatch.fnmatch(path, p) for p in ALLOW)


def space_host(space_id: str) -> str:
    return "https://" + space_id.lower().replace("/", "-").replace("_", "-").replace(".", "-") + ".hf.space"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("space_id", nargs="?", help="<user-or-org>/<name>, default <you>/spam-scan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--timeout", type=int, default=1200, help="seconds to wait for the build")
    a = ap.parse_args()

    root = Path(a.repo_root)
    api = HfApi(token=os.environ["HF_TOKEN"])
    me = api.whoami()  # GET /api/whoami-v2
    user = me["name"]
    role = (me.get("auth", {}).get("accessToken", {}) or {}).get("role")
    print(f"Logged in to Hugging Face as: {user} (token role: {role or 'unknown'})")
    if role == "read":
        print("error: this token is read-only; create a WRITE token.", file=sys.stderr)
        return 2
    space_id = a.space_id or f"{user}/spam-scan"

    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        print("warning: tracked files have uncommitted changes; the working-tree versions will be uploaded:\n"
              + dirty)

    files = [f for f in git_files(root) if wanted(f)]
    for must in ("app.py", "model.joblib", "Dockerfile", "requirements.txt"):
        if must not in files:
            print(f"error: {must} is not git-tracked / missing", file=sys.stderr)
            return 2

    with tempfile.TemporaryDirectory(prefix="spam-scan-space-") as tmp:
        stage = Path(tmp)
        for f in files:
            (stage / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / f, stage / f)
        shutil.copy2(root / "deploy/hf/README.md", stage / "README.md")
        staged = sorted(str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file())
        total = sum((stage / p).stat().st_size for p in staged)
        print(f"Space: {space_id}  ({len(staged)} files, {total / 1e6:.1f} MB)")
        for p in staged:
            print("  ", p)
        if a.dry_run:
            print("Dry run: nothing created or uploaded.")
            return 0

        url = api.create_repo(space_id, repo_type="space", space_sdk="docker", private=False, exist_ok=True)
        print(f"Space ready: {url}")
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True,
                             text=True).stdout.strip() or "unknown"
        info = api.upload_folder(
            repo_id=space_id, repo_type="space", folder_path=stage,
            allow_patterns=ALLOW + ["README.md"], ignore_patterns=[p for p in IGNORE if p != "README.md"],
            delete_patterns=DELETE,
            commit_message=f"Deploy SPAM//SCAN from GitHub Rishabh-bgp/spam-scan@{sha}",
        )
        print(f"Uploaded: {getattr(info, 'commit_url', info)}")

    print(f"Space page: https://huggingface.co/spaces/{space_id}")
    print(f"App URL:    {space_host(space_id)}")
    if a.no_wait:
        return 0

    print("Waiting for the Docker build (first build takes a few minutes)...")
    deadline, last = time.time() + a.timeout, None
    while time.time() < deadline:
        rt = api.get_space_runtime(space_id)
        if rt.stage != last:
            print(f"  [{time.strftime('%H:%M:%S')}] stage: {rt.stage}")
            last = rt.stage
        if rt.stage == "RUNNING":
            print(f"Live: {space_host(space_id)}")
            return 0
        if rt.stage in ("BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR", "NO_APP_FILE"):
            print(f"error: Space stopped at {rt.stage}. See the logs at "
                  f"https://huggingface.co/spaces/{space_id}?logs=build", file=sys.stderr)
            return 3
        time.sleep(15)
    print("Timed out waiting; check the Space page for build logs.", file=sys.stderr)
    return 4


if __name__ == "__main__":
    sys.exit(main())
