# 📥 Proje İndirme ve Kurulum

## 🔗 İndirme Seçenekleri

### Seçenek 1: ZIP İndirme (Önerilen)

Projeyi ZIP olarak indirmek için:

1. Proje klasörünü sıkıştırın:
   - `admin-ses` klasörüne sağ tıklayın
   - "Sıkıştırılmış (zip) klasör olarak gönder" seçin
   - `admin-ses.zip` oluşacak

2. Veya komut satırından:
```bash
# PowerShell
Compress-Archive -Path "C:\Users\ASUS\Desktop\admin-ses" -DestinationPath "C:\Users\ASUS\Desktop\admin-ses.zip"
```

### Seçenek 2: GitHub'a Yükle

```bash
cd C:\Users\ASUS\Desktop\admin-ses

# Git init
git init
git add .
git commit -m "Initial commit: WebRTC Teknik Destek Sistemi"

# GitHub'a push (önce GitHub'da repo oluşturun)
git remote add origin https://github.com/KULLANICI_ADI/admin-ses.git
git branch -M main
git push -u origin main
```

### Seçenek 3: Google Drive / Dropbox

1. `admin-ses` klasörünü Google Drive veya Dropbox'a yükleyin
2. Paylaşım linkini alın
3. Linki paylaşın

---

## 📦 Proje İçeriği

```
admin-ses/
├── app/                    # Backend (7 dosya)
│   ├── auth.py
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   ├── otp_store.py
│   ├── telegram_bot.py
│   └── webrtc_handler.py
├── static/                 # Frontend (5 dosya)
│   ├── css/style.css
│   ├── js/
│   │   ├── admin.js
│   │   └── client.js
│   ├── admin.html
│   └── index.html
├── .env                    # Environment variables
├── .gitignore
├── requirements.txt        # Python dependencies
├── README.md
├── KURULUM.md
├── PRODUCTION_READY.md
├── SISTEM_ANALIZI.md
└── setup_and_run.bat       # Auto setup script
```

**Toplam Boyut:** ~50 KB (kod only, dependencies hariç)

---

## 🚀 Kurulum (İndirdikten Sonra)

### 1. Projeyi Aç
```bash
cd admin-ses
```

### 2. Python Kurulu mu Kontrol Et
```bash
python --version
```

Eğer kurulu değilse: https://www.python.org/downloads/

### 3. Otomatik Kurulum
```bash
setup_and_run.bat
```

Veya manuel:
```bash
pip install -r requirements.txt
python init_db.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Telegram Bot Ayarla

`.env` dosyasını düzenle:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_CHAT_ID=your_chat_id_here
```

Bot oluşturma: https://t.me/BotFather

---

## 🌐 Erişim

- **Ana Sayfa:** http://localhost:8000
- **Müşteri:** http://localhost:8000/static/index.html
- **Admin:** http://localhost:8000/static/admin.html

**Admin Giriş:**
- Username: `admin`
- Password: `adminpass`

---

## 📋 Gereksinimler

- Python 3.8+
- Redis (opsiyonel - OTP için)
- ffmpeg (opsiyonel - recording için)

---

## 🔗 Alternatif İndirme Yöntemleri

### WeTransfer
1. https://wetransfer.com/ adresine gidin
2. `admin-ses.zip` yükleyin
3. Link alın (7 gün geçerli)

### GitHub Gist
```bash
# Tüm dosyaları tek bir gist'e yükle
# https://gist.github.com/
```

### Pastebin (Kod için)
- https://pastebin.com/
- Her dosyayı ayrı paste olarak yükle

---

## 📞 Destek

Sorun yaşarsanız:
1. `KURULUM.md` dosyasını okuyun
2. `BASLAMADAN_ONCE.txt` dosyasını kontrol edin
3. `fix_otp.bat` çalıştırın (OTP sorunları için)

---

## 📄 Lisans

MIT License - Ticari kullanım için uygun

---

## 🎯 Hızlı Başlangıç

```bash
# 1. İndir ve aç
unzip admin-ses.zip
cd admin-ses

# 2. Kur ve çalıştır
setup_and_run.bat

# 3. Tarayıcıda aç
http://localhost:8000
```

**Hazır! 🚀**
