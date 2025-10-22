# 🐍 Python Kurulum Rehberi

## Python Kurulu mu Kontrol Et

Komut satırını açın (CMD) ve yazın:
```bash
python --version
```

Eğer "Python bulunamadı" hatası alıyorsanız, Python kurulu değil.

## Python Kurulumu (Windows)

### Adım 1: İndir
1. https://www.python.org/downloads/ adresine gidin
2. "Download Python 3.11.x" butonuna tıklayın
3. İndirilen dosyayı çalıştırın

### Adım 2: Kur
**ÖNEMLİ:** Kurulum sırasında:
- ✅ **"Add python.exe to PATH"** kutucuğunu işaretleyin (en önemli!)
- ✅ "Install pip" seçeneğini işaretleyin
- "Install Now" tıklayın

### Adım 3: Kontrol Et
Kurulum bittikten sonra:
1. Yeni bir CMD penceresi açın
2. Yazın: `python --version`
3. Python 3.11.x görmelisiniz

## Hızlı Kurulum (Chocolatey ile)

Eğer Chocolatey kuruluysa:
```bash
choco install python
```

## Kurulum Sonrası

Python kurulduktan sonra:
```bash
# Projeye gidin
cd C:\Users\ASUS\Desktop\admin-ses

# Setup scriptini çalıştırın
setup_and_run.bat
```

## Sorun Giderme

### "python komutu tanınmıyor"
- Python'u yeniden kurun ve "Add to PATH" seçeneğini işaretleyin
- Veya manuel olarak PATH'e ekleyin:
  1. Sistem Özellikleri > Gelişmiş > Ortam Değişkenleri
  2. Path değişkenine Python klasörünü ekleyin
  3. Örnek: `C:\Users\KULLANICI\AppData\Local\Programs\Python\Python311`

### Hangi Python versiyonu?
- Python 3.8 veya üzeri (önerilen: 3.11)
- Python 2.x ÇALIŞMAZ

## Alternatif: Portable Python

Python kurmak istemiyorsanız:
1. WinPython indir: https://winpython.github.io/
2. Zip'i aç
3. WinPython Command Prompt'u çalıştır
4. Proje klasörüne gidin ve setup_and_run.bat çalıştırın
