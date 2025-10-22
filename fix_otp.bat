@echo off
echo ========================================
echo OTP Sistemi Test ve Duzeltme
echo ========================================
echo.

echo [1] Telegram ayarlari kontrol ediliyor...
echo.
type .env | findstr TELEGRAM
echo.

echo [2] Telegram OTP testi yapiliyor...
python test_telegram.py
echo.

echo ========================================
echo SORUN COZUM:
echo ========================================
echo.
echo 1. Bot'a /start mesaji gonderin
echo    Telegram'da bot'u arayip /start yazin
echo.
echo 2. Chat ID dogru mu kontrol edin
echo    https://api.telegram.org/bot7801493894:AAHQTlDbrugF5Lb7bsYZc0sS5vEKGd-e-pc/getUpdates
echo.
echo 3. Redis calisiyor mu?
echo    redis-cli ping
echo.
echo 4. OTP olmadan giris icin:
echo    Admin panelde sadece username girin
echo    Sifre: adminpass (direkt giris)
echo.

pause
