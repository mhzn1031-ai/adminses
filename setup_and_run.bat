@echo off
echo ========================================
echo Teknik Destek Sistemi - Otomatik Kurulum
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Python 3.8+ yukleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Python bulundu
python --version

REM Install dependencies
echo.
echo [2/5] Paketler yukleniyor...
pip install -q fastapi uvicorn python-dotenv redis python-jose passlib[bcrypt] aiortc sqlmodel sqlalchemy httpx

REM Check Redis
echo.
echo [3/5] Redis kontrol ediliyor...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [UYARI] Redis calismiyorsa OTP sistemi calismaz
    echo Redis yuklemek icin: https://github.com/microsoftarchive/redis/releases
)

REM Create database
echo.
echo [4/5] Veritabani olusturuluyor...
python -c "from app.db import engine; from app.models import SQLModel; SQLModel.metadata.create_all(engine)" 2>nul
if errorlevel 1 (
    echo [HATA] Veritabani olusturulamadi
    pause
    exit /b 1
)

echo [OK] Veritabani hazir

REM Start server
echo.
echo [5/5] Server baslatiliyor...
echo.
echo ========================================
echo Server calisiyor:
echo - Ana sayfa: http://localhost:8000
echo - Musteri: http://localhost:8000/static/index.html
echo - Admin: http://localhost:8000/static/admin.html
echo ========================================
echo.
echo Durdurmak icin CTRL+C basin
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
