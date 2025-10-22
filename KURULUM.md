# 🚀 Hızlı Kurulum

## Otomatik Kurulum (Önerilen)

1. **`setup_and_run.bat`** dosyasına çift tıklayın
2. Bekleyin (paketler yüklenecek)
3. Server otomatik başlayacak

## Manuel Kurulum

```bash
# 1. Paketleri yükle
pip install fastapi uvicorn python-dotenv redis python-jose passlib[bcrypt] aiortc sqlmodel sqlalchemy httpx

# 2. Veritabanı oluştur
python -c "from app.db import engine; from app.models import SQLModel; SQLModel.metadata.create_all(engine)"

# 3. Serveri başlat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Erişim

- **Ana Sayfa**: http://localhost:8000
- **Müşteri**: http://localhost:8000/static/index.html
- **Admin**: http://localhost:8000/static/admin.html

## Gereksinimler

- Python 3.8+
- Redis (OTP için - opsiyonel)

## Redis Kurulumu (Windows)

1. İndir: https://github.com/microsoftarchive/redis/releases
2. Kur ve başlat
3. Test: `redis-cli ping` (PONG dönmeli)

## Sorun Giderme

### "Python bulunamadı"
- Python yükleyin: https://www.python.org/downloads/
- Kurulumda "Add to PATH" seçeneğini işaretleyin

### "Redis bağlanamıyor"
- Redis'i başlatın veya .env'de `REDIS_URL` ayarlayın
- Redis olmadan da çalışır (OTP sistemi devre dışı)

### Port zaten kullanımda
```bash
# Farklı port kullanın
python -m uvicorn app.main:app --port 8001
```

## Admin Giriş

- Kullanıcı: `admin`
- Şifre: `adminpass` (ilk girişte OTP isteyecek)
- Telegram'dan 6 haneli kod gelecek
