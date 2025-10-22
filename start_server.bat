@echo off
setlocal

REM Try using py, fallback to python
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set PY=py
) else (
  where python >nul 2>nul
  if %ERRORLEVEL%==0 (
    set PY=python
  ) else (
    echo Python bulunamad. Lütfen Python 3.11 kurup PATH'e ekleyin: https://www.python.org/downloads/windows/
    echo Kurulumda "Add python.exe to PATH" ve pip kurulumunu seçin.
    pause
    exit /b 1
  )
)

echo Creating virtual environment...
%PY% -m venv .venv
if %ERRORLEVEL% NEQ 0 (
  echo Venv olusturulamadi.
  pause
  exit /b 1
)

echo Upgrading pip...
".\.venv\Scripts\python" -m pip install --upgrade pip

echo Installing requirements...
".\.venv\Scripts\python" -m pip install -r requirements.txt

echo Initializing database...
".\.venv\Scripts\python" -c "from app.db import engine; from app.models import SQLModel; SQLModel.metadata.create_all(engine)"

echo Starting server...
".\.venv\Scripts\python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
