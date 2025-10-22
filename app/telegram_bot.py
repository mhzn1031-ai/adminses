import os
import httpx
import secrets
from typing import Optional

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")

async def send_telegram_message(text: str, chat_id: Optional[str] = None) -> bool:
    """Send message to Telegram chat"""
    if not TELEGRAM_BOT_TOKEN:
        return False
    target_chat = chat_id or TELEGRAM_ADMIN_CHAT_ID
    if not target_chat:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"chat_id": target_chat, "text": text, "parse_mode": "HTML"}, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

async def send_call_notification(caller_name: str) -> bool:
    """Notify admin about incoming call"""
    safe_name = caller_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    message = f"\U0001F514 <b>Biri seni arıyor</b>\n\n\U0001F464 {safe_name}"
    return await send_telegram_message(message)

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return f"{secrets.randbelow(1000000):06d}"

async def send_otp(otp: str) -> bool:
    """Send OTP to admin via Telegram"""
    message = f"\U0001F510 <b>Giriş Kodunuz</b>\n\n<code>{otp}</code>\n\n\u23F0 Kod 5 dakika geçerlidir."
    return await send_telegram_message(message)
