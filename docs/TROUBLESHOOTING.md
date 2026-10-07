# Troubleshooting

← Back to the [README](../README.md) · See also the [FAQ](FAQ.md)

## Contents

- [Port 5000 is already in use](#port-5000-is-already-in-use)
- [scikit-learn version mismatch when loading model.joblib](#scikit-learn-version-mismatch-when-loading-modeljoblib)
- [model.joblib not found](#modeljoblib-not-found)
- [The app stops when I close the terminal (macOS / Linux)](#the-app-stops-when-i-close-the-terminal-macos--linux)
- [Windows: PowerShell won't activate the virtual environment](#windows-powershell-wont-activate-the-virtual-environment)
- [python / python3 not found, or the wrong version](#python--python3-not-found-or-the-wrong-version)
- [./run.sh: Permission denied](#runsh-permission-denied)
- [Retraining fails: pandas or pyarrow missing, or downloads fail](#retraining-fails-pandas-or-pyarrow-missing-or-downloads-fail)
- [Can't open the app from my phone or another computer](#cant-open-the-app-from-my-phone-or-another-computer)
- [No sound](#no-sound)
- [The page is too animated or slow](#the-page-is-too-animated-or-slow)
- [I changed a rule or example but nothing changed](#i-changed-a-rule-or-example-but-nothing-changed)
- [Results differ from the docs](#results-differ-from-the-docs)
- [Deployment problems (Render, Docker)](DEPLOY.md#troubleshooting-deployments)

## Port 5000 is already in use

The error looks like `Address already in use` or `Port 5000 is in use by another program`.

- **On macOS (Monterey and later), AirPlay Receiver listens on port 5000.** Either turn it off (*System Settings → General → AirDrop & Handoff → AirPlay Receiver*) or use another port.
- Use another port:

  ```bash
  PORT=5001 ./run.sh                 # macOS / Linux
  PORT=5001 python app.py
  ```

  ```bat
  :: Windows cmd
  set PORT=5001
  python app.py
  ```

  ```powershell
  $env:PORT=5001; python app.py      # Windows PowerShell
  ```

  Note that `run.bat` always prints `http://127.0.0.1:5000`, but the app itself uses `PORT`.
- Find and stop whatever is using the port. It's often an old copy of this app:

  ```bash
  lsof -i :5000                      # macOS / Linux: shows the PID
  kill <PID>
  pkill -f "python app.py"           # stop an old SPAM//SCAN
  ```

  ```bat
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  ```

## scikit-learn version mismatch when loading model.joblib

The symptoms are `InconsistentVersionWarning: Trying to unpickle estimator ... from version 1.9.1 when using version X`, or errors such as `AttributeError` or `ModuleNotFoundError` while loading the model.

`model.joblib` was saved with **scikit-learn 1.9.1**. `requirements.txt` allows any version `>=1.3,<2`, and pickled models are only guaranteed to load with the same version. To fix it, do one of these:

1. **Install the matching version** (quickest):

   ```bash
   .venv/bin/pip install "scikit-learn==1.9.1"      # Windows: .venv\Scripts\pip install "scikit-learn==1.9.1"
   ```

2. **Retrain with your version** (about 2 minutes and 1.5 GB of RAM; downloads about 40 MB):

   ```bash
   .venv/bin/pip install -r requirements-data.txt
   .venv/bin/python train.py
   ```

Also make sure `textnorm.py` is next to `app.py`. The model imports `textnorm.normalize` when it loads.

## model.joblib not found

`app.py` stops with ``model.joblib not found. Run `python train.py` first.``

- Check that you're running from the project folder (`cd spam-scan`).
- If you downloaded the ZIP from GitHub, make sure `model.joblib` (about 8 MB) is in it.
- Or train one: `pip install -r requirements-data.txt && python train.py`. `run.sh` and `run.bat` do this automatically when the model is missing.

## The app stops when I close the terminal (macOS / Linux)

A process started from a terminal is killed when the terminal closes. To keep the app running in the background:

```bash
nohup .venv/bin/python app.py > server.log 2>&1 &
```

If that still dies on macOS (for example when started from an automation tool), start it in a **new session**, fully detached:

```bash
.venv/bin/python -c "import subprocess; log=open('server.log','ab'); p=subprocess.Popen(['.venv/bin/python','app.py'],stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True); print(p.pid)"
```

Check it's up and stop it later:

```bash
curl -s http://127.0.0.1:5000/api/health
pkill -f "\.venv/bin/python app.py"
```

`server.log` is git-ignored.

## Windows: PowerShell won't activate the virtual environment

The error is `running scripts is disabled on this system`.

- Run this once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Or don't activate at all: `.venv\Scripts\python.exe app.py`.
- Or use `run.bat`, which doesn't need activation.

## python / python3 not found, or the wrong version

- You need **Python 3.12 or newer**. The code itself runs on 3.9+, but `requirements.txt` pins numpy 2.5.3 and scipy 1.18.1, which need 3.12+, and scikit-learn 1.9.1 (needed to load `model.joblib`) needs 3.11+. It was tested with Python 3.13.
- macOS / Linux: `python3 --version`. `run.sh` tries `python3` and then `python`.
- Windows: install Python from python.org and tick **"Add python.exe to PATH"**, or use the launcher: `py -3 -m venv .venv`. `run.bat` falls back to `py -3` automatically.
- If an old `.venv` was made with another Python, delete it and run the script again.

## ./run.sh: Permission denied

```bash
chmod +x run.sh && ./run.sh      # or: bash run.sh
```

## Retraining fails: pandas or pyarrow missing, or downloads fail

- `ModuleNotFoundError: pandas` / `pyarrow`: run `pip install -r requirements-data.txt`. They're only needed by `prepare_data.py`.
- **Download errors** (HTTP 404, timeouts, or a corporate proxy blocking Hugging Face or GitHub): the source URLs are listed in `prepare_data.SOURCES`. Download the files by hand into `data/raw/` with the same file names, then rerun. Files that already exist are skipped.
- **Out of memory**: training peaked at about 1.5 GB on the author's machine. Close other apps, or lower `max_features` in `train.build_pipeline()`. That changes the model, so the metrics will differ.

## Can't open the app from my phone or another computer

By default the app only listens on `127.0.0.1` (this computer). To reach it from your local network:

```bash
HOST=0.0.0.0 PORT=5000 python app.py
```

Then open `http://<your-computer's-LAN-IP>:5000` on the other device, and allow Python through your firewall if asked. Only do this on a network you trust. There's no login, and it's a development server (see [SECURITY.md](../SECURITY.md)). To use it from anywhere, try the [live demo](https://spam-scan.onrender.com) or deploy your own copy ([DEPLOY.md](DEPLOY.md)).

## No sound

- Sounds only play **after your first click or key press** on the page (a browser rule).
- Check that the header says `[ SFX: ON ]`. The setting is saved in `localStorage`.
- Check that the browser tab isn't muted.

## The page is too animated or slow

Turn on your operating system's **reduce motion** setting (macOS: *Accessibility → Display → Reduce motion*; Windows: *Accessibility → Visual effects → Animation effects* off). The boot screen and Matrix rain then disappear and all animations stop. See [UI.md](UI.md#accessibility-and-reduced-motion).

## I changed a rule or example but nothing changed

`app.py` loads the model, the rules and `examples.json` **once at start-up**. Restart the server after any change. Gallery tile statistics are also computed at start-up.

## Results differ from the docs

- Check `metrics.json` → `trained_at` and `sklearn_version`. A retrained model gives different numbers. A retrain with the current code differs very slightly from the shipped model (see [MODEL.md](MODEL.md#how-to-retrain)).
- A different scikit-learn or NumPy version can change probabilities in the last decimal places.
