@echo off
REM Create venv, install deps, train if needed, and start the app.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv || py -3 -m venv .venv
    if errorlevel 1 (
        echo Could not create a virtual environment. Is Python 3 installed and on PATH?
        exit /b 1
    )
)
set "VENV_PY=.venv\Scripts\python.exe"

echo Installing dependencies...
"%VENV_PY%" -m pip install --quiet --upgrade pip
"%VENV_PY%" -m pip install --quiet -r requirements.txt || exit /b 1

if not exist "model.joblib" if not exist "data\combined.csv.gz" (
    echo Training data missing; installing data-prep extras ^(pandas, pyarrow^)...
    "%VENV_PY%" -m pip install --quiet -r requirements-data.txt || exit /b 1
)

if not exist "model.joblib" (
    echo Training model...
    "%VENV_PY%" train.py || exit /b 1
)

echo Starting app at http://127.0.0.1:5000
"%VENV_PY%" app.py
