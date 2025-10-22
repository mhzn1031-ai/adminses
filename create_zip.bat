@echo off
echo ========================================
echo Proje ZIP Olusturuluyor
echo ========================================
echo.

set PROJECT_NAME=admin-ses
set OUTPUT_PATH=C:\Users\ASUS\Desktop\%PROJECT_NAME%.zip

echo [1/2] Gereksiz dosyalar temizleniyor...
if exist database.db del database.db
if exist recordings rmdir /s /q recordings
if exist __pycache__ rmdir /s /q __pycache__
if exist app\__pycache__ rmdir /s /q app\__pycache__

echo.
echo [2/2] ZIP olusturuluyor...
powershell -command "Compress-Archive -Path '%CD%' -DestinationPath '%OUTPUT_PATH%' -Force"

if %ERRORLEVEL%==0 (
    echo.
    echo ========================================
    echo ZIP OLUSTURULDU!
    echo ========================================
    echo.
    echo Konum: %OUTPUT_PATH%
    echo Boyut: 
    powershell -command "(Get-Item '%OUTPUT_PATH%').Length / 1KB | ForEach-Object { '{0:N0} KB' -f $_ }"
    echo.
    echo Dosyayi paylasabilirsiniz!
    echo.
) else (
    echo.
    echo HATA: ZIP olusturulamadi
)

pause
