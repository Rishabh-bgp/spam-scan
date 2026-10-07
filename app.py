"""Flask web app for the transparent spam classifier."""
import json
import os
import sys
from pathlib import Path

import joblib
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from explain import UNSURE_HIGH, UNSURE_LOW, Explainer, analyse, final_verdict  # noqa: E402
from domains import OFFICIAL  # noqa: E402
from redflags import RULES, SAFE_RULES  # noqa: E402

MODEL_FILE = ROOT / "model.joblib"
METRICS_FILE = ROOT / "metrics.json"
MAX_CHARS = 10000

if not MODEL_FILE.exists():
    raise SystemExit("model.joblib not found. Run `python train.py` first.")

model = joblib.load(MODEL_FILE)
explainer = Explainer(model)
metrics = json.loads(METRICS_FILE.read_text(encoding="utf-8")) if METRICS_FILE.exists() else {}

EXAMPLES_FILE = ROOT / "examples.json"
EXAMPLE_CATEGORIES = (json.loads(EXAMPLES_FILE.read_text(encoding="utf-8"))["categories"]
                      if EXAMPLES_FILE.exists() else [])
LANG_CODES = {"English": "EN", "Hinglish": "HI-EN", "Hindi": "HI", "Misspelled": "TYPO"}


def threat_level(ml_caught, total):
    """Threat level = how often the ML model ALONE misses this scam type on the
    gallery examples (the rules may still catch it). Computed, not hand-set."""
    r = ml_caught / total if total else 1.0
    if r >= 1.0:
        return "LOW"
    if r >= 0.75:
        return "MED"
    if r >= 0.5:
        return "HIGH"
    return "CRIT"


def compute_example_stats():
    """Run every gallery example through the model + rules once at startup (cached)."""
    for c in EXAMPLE_CATEGORIES:
        texts = [e["text"] for e in c["examples"]]
        probs = model.predict_proba(texts)[:, 1] if texts else []
        ml_ok = final_ok = 0
        for e, p in zip(c["examples"], probs):
            verdict = final_verdict(float(p), e["text"])[0]
            e["verdict"], e["ml_probability"] = verdict, round(float(p), 3)
            e["lang_code"] = LANG_CODES.get(e.get("lang"), e.get("lang", "?")[:4].upper())
            ml_ok += ("spam" if p >= 0.5 else "ham") == e.get("expected", "spam")
            final_ok += verdict == e.get("expected", "spam")
        n = len(texts)
        if c["id"] == "gray":      # gray zone: borderline messages, "correct" = still lands in Unsure
            level = "GRAY"
        elif c["id"] == "genuine":
            level = "SAFE"
        else:
            level = threat_level(ml_ok, n)
        c["stats"] = {"total": n, "ml_correct": ml_ok, "final_correct": final_ok, "level": level}


compute_example_stats()

app = Flask(__name__)
# Reject oversized request bodies early (413). The text itself is capped at MAX_CHARS.
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024


@app.context_processor
def fx_context():
    """Inject the small `fx` dict (feature/rule/dataset counts, accuracy) into every template."""
    # numbers shown in the boot sequence / status line
    return {"fx": {"features": metrics.get("n_features", 0), "rules": len(RULES), "safe": len(SAFE_RULES),
                   "datasets": len(metrics.get("datasets", {})), "accuracy": metrics.get("accuracy", 0)}}
app.json.sort_keys = False
app.json.ensure_ascii = False


@app.get("/")
def index():
    """Main scanner page with the Threat Matrix gallery."""
    return render_template("index.html", categories=EXAMPLE_CATEGORIES, metrics=metrics,
                           max_chars=MAX_CHARS, low=UNSURE_LOW, high=UNSURE_HIGH)


@app.get("/how-it-works")
def how_it_works():
    """Transparency page: datasets, metrics, probes, top features, rules, safe signals, allowlist."""
    rules = [{"id": r[0], "title": r[1], "explanation": r[2], "severity": r[3]} for r in RULES]
    safe_rules = [{"id": r[0], "title": r[1], "explanation": r[2]} for r in SAFE_RULES]
    return render_template("how.html", m=metrics, rules=rules, safe_rules=safe_rules,
                           official=OFFICIAL, low=UNSURE_LOW, high=UNSURE_HIGH)


@app.post("/api/predict")
def api_predict():
    """POST {"text": "..."} -> full analysis JSON (see docs/API.md). 400 if empty, 413 if > MAX_CHARS."""
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        return jsonify(error="Provide a non-empty 'text' string."), 400
    if len(text) > MAX_CHARS:
        return jsonify(error=f"Text too long (max {MAX_CHARS} characters)."), 413
    return jsonify(analyse(explainer, text))


@app.get("/api/health")
def health():
    """Liveness check: status, model description and held-out accuracy."""
    return jsonify(status="ok", model=metrics.get("model"), accuracy=metrics.get("accuracy"))


@app.get("/api/model-info")
def model_info():
    """metrics.json without the per-probe miss lists (those are only shown on /how-it-works)."""
    return jsonify({k: v for k, v in metrics.items() if k != "probes"} | {
        "probes": {g: {k: v for k, v in r.items() if k != "misses"} for g, r in metrics.get("probes", {}).items()}})


if __name__ == "__main__":
    # Local dev server. Defaults to 127.0.0.1:5000; HOST / PORT env vars override it.
    # In production (Docker / Hugging Face Space) gunicorn serves `app:app` instead,
    # reading the same HOST / PORT variables (see Dockerfile).
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    print(f"Spam classifier running at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
