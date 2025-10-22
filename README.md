# Teknik Destek Sistemi

WebRTC tabanlı teknik destek video görüşme sistemi.

## Özellikler

- İsim girme ve Telegram bildirimi
- Admin OTP girişi (6 haneli)
- Kabul/Reddet mekanizması
- Video/Ses kontrolleri (kamera, mikrofon, hoparlör, diafon)
- Arama süresi takibi
- Geçmiş aramalar
- Günlük limit (10 çağrı)
- Server-side recording

## Kurulum

```bash
pip install -r requirements.txt
python -c "from app.db import engine; from app.models import SQLModel; SQLModel.metadata.create_all(engine)"
```

## Çalıştırma

```bash
uvicorn app.main:app --reload
```

## Environment Variables

```
SECRET_KEY=your_secret_key
ADMIN_USER=admin
ADMIN_PASS=adminpass
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./database.db
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id
ALLOWED_ORIGINS=*
```

## Kullanım

- Müşteri: http://localhost:8000/static/index.html
- Admin: http://localhost:8000/static/admin.html
