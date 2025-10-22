# 🚀 Render.com Deployment Rehberi

## Hızlı Başlangıç

### 1. Render Hesabı Oluştur
- https://render.com adresine git
- GitHub hesabınla giriş yap

### 2. Blueprint ile Deploy

#### Otomatik Kurulum (Önerilen)
1. Render Dashboard → **New** → **Blueprint**
2. GitHub repo seç: `mhzn1031-ai/adminses`
3. `render.yaml` otomatik algılanacak
4. **Apply** tıkla
5. 2 servis oluşturulacak:
   - `admin-ses` (Web Service)
   - `admin-ses-redis` (Redis)

#### Manuel Kurulum
Eğer Blueprint çalışmazsa:

**A. Redis Oluştur**
1. Dashboard → **New** → **Redis**
2. Name: `admin-ses-redis`
3. Region: Frankfurt
4. Plan: Free
5. **Create Redis**

**B. Web Service Oluştur**
1. Dashboard → **New** → **Web Service**
2. GitHub repo: `mhzn1031-ai/adminses`
3. Ayarlar:
   - **Name:** admin-ses
   - **Region:** Frankfurt
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

### 3. Environment Variables Ayarla

Web Service → **Environment** sekmesinde:

```
SECRET_KEY=<Auto-generate ile oluştur>
ADMIN_USER=admin
ADMIN_PASS=<Güçlü şifre belirle>
REDIS_URL=<Redis internal URL'i yapıştır>
DATABASE_URL=sqlite:///./database.db
TELEGRAM_BOT_TOKEN=7801493894:AAHQTlDbrugF5Lb7bsYZc0sS5vEKGd-e-pc
TELEGRAM_ADMIN_CHAT_ID=6476943853
ALLOWED_ORIGINS=*
```

**Redis URL Alma:**
- Redis servisine git → **Connect** → Internal URL'i kopyala
- Format: `redis://red-xxxxx:6379`

### 4. Deploy

- **Save Changes** → Otomatik deploy başlar
- Build logs'u izle (3-5 dakika)
- Deploy tamamlandığında URL: `https://admin-ses.onrender.com`

---

## Erişim URL'leri

```
Client: https://admin-ses.onrender.com/static/index.html
Admin:  https://admin-ses.onrender.com/static/admin.html
API:    https://admin-ses.onrender.com/docs
```

---

## İlk Kurulum Adımları

### 1. Admin Kullanıcı Oluştur

Render Shell'den:
```bash
python -c "from app.db import engine; from app.models import SQLModel; SQLModel.metadata.create_all(engine)"
python -c "from app.auth import create_admin_user; create_admin_user('admin', 'YourStrongPassword123')"
```

Ya da local'de oluşturup database.db'yi upload et.

### 2. Test Et

1. Client sayfasını aç
2. İsim gir → Telegram'a bildirim gelsin
3. Admin paneline gir (OTP ile)
4. Çağrıyı kabul et
5. Video görüşme başlasın

---

## Önemli Notlar

### Free Plan Limitleri

- **Web Service:**
  - 750 saat/ay (sleep after 15 min inactivity)
  - 512 MB RAM
  - 0.1 CPU
  - Cold start: ~30 saniye

- **Redis:**
  - 25 MB storage
  - Eviction policy: noeviction

### Persistent Storage

⚠️ **SQLite Sorunu:** Render free plan'de disk ephemeral (geçici)
- Her deploy'da database sıfırlanır
- **Çözüm:** PostgreSQL kullan (ücretsiz 1GB)

#### PostgreSQL'e Geçiş

1. Dashboard → **New** → **PostgreSQL**
2. Name: `admin-ses-db`
3. Plan: Free
4. **Create Database**
5. Internal URL'i kopyala
6. Environment variable güncelle:
   ```
   DATABASE_URL=postgresql://user:pass@host/db
   ```
7. `requirements.txt`'e ekle:
   ```
   psycopg2-binary==2.9.9
   ```

### WebRTC STUN/TURN

Free plan'de P2P bağlantı sorun olabilir:
- **STUN:** Google STUN sunucuları kullanılıyor (ücretsiz)
- **TURN:** Gerekirse Twilio/Metered kullan

### Recording Storage

⚠️ Kayıtlar ephemeral disk'te:
- Her deploy'da silinir
- **Çözüm:** S3/Cloudflare R2 entegrasyonu ekle

---

## Troubleshooting

### Build Hatası

```bash
# Logs'da hata varsa:
ERROR: Could not find a version that satisfies the requirement aiortc
```

**Çözüm:** `requirements.txt`'de version pin'le:
```
aiortc==1.6.0
```

### Redis Connection Error

```
redis.exceptions.ConnectionError
```

**Çözüm:**
1. Redis servisinin çalıştığını kontrol et
2. `REDIS_URL` doğru mu kontrol et
3. Internal URL kullan (external değil)

### WebSocket Hatası

```
WebSocket connection failed
```

**Çözüm:**
- HTTPS kullan (HTTP değil)
- CORS ayarlarını kontrol et
- Browser console'da detaylı hata bak

### Cold Start

Free plan'de 15 dakika inactivity sonrası sleep:
- İlk istek 30 saniye sürebilir
- **Çözüm:** Cron job ile ping at (UptimeRobot)

---

## Production Checklist

- [ ] `ADMIN_PASS` güçlü şifre
- [ ] `SECRET_KEY` auto-generate
- [ ] PostgreSQL kullan (SQLite yerine)
- [ ] `ALLOWED_ORIGINS` spesifik domain
- [ ] HTTPS enforce
- [ ] Telegram bot token güvenli
- [ ] Rate limiting test et
- [ ] WebRTC bağlantı test et
- [ ] Recording test et
- [ ] Monitoring ekle (Sentry)

---

## Maliyet

### Free Plan (Başlangıç)
- Web Service: $0
- Redis: $0
- PostgreSQL: $0
- **Toplam: $0/ay**

### Paid Plan (Production)
- Web Service (Starter): $7/ay
- Redis (25MB): $10/ay
- PostgreSQL (1GB): $7/ay
- **Toplam: $24/ay**

---

## Alternatif Deployment

Eğer Render çalışmazsa:

1. **Railway.app** (Benzer, daha kolay)
2. **Fly.io** (Daha hızlı, karmaşık)
3. **Heroku** (Ücretli)
4. **DigitalOcean App Platform** ($5/ay)

---

## Destek

- Render Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com
