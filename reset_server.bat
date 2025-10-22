@echo off
echo ========================================
echo Server Reset - Tum State Temizleniyor
echo ========================================
echo.

echo [1/4] Veritabani siliniyor...
if exist database.db (
    del database.db
    echo - database.db silindi
) else (
    echo - database.db bulunamadi
)

echo.
echo [2/4] Redis temizleniyor...
redis-cli FLUSHALL >nul 2>&1
if %ERRORLEVEL%==0 (
    echo - Redis temizlendi
) else (
    echo - Redis bulunamadi veya calismiyor
)

echo.
echo [3/4] Recordings siliniyor...
if exist recordings (
    rmdir /s /q recordings
    echo - recordings/ silindi
) else (
    echo - recordings/ bulunamadi
)

echo.
echo [4/4] Yeni veritabani olusturuluyor...
python -c "from app.db import engine; from app.models import SQLModel; SQLModel.metadata.create_all(engine)"
if %ERRORLEVEL%==0 (
    echo - Veritabani olusturuldu
) else (
    echo - HATA: Veritabani olusturulamadi
    pause
    exit /b 1
)

echo.
echo ========================================
echo RESET TAMAMLANDI!
echo ========================================
echo.
echo Temizlenen:
echo - Tum call sessions
echo - Tum recordings
echo - Redis cache (OTP, rate limits)
echo - Admin user (yeniden olusturuldu)
echo.
echo Yeni admin:
echo - Username: admin
echo - Password: adminpass
echo.
echo Server baslatmak icin: setup_and_run.bat
echo.

pause
