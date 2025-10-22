import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_telegram():
    from app.telegram_bot import send_otp, generate_otp
    
    print("Testing Telegram OTP...")
    print(f"Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
    print(f"Chat ID: {os.getenv('TELEGRAM_ADMIN_CHAT_ID')}")
    
    otp = generate_otp()
    print(f"Generated OTP: {otp}")
    
    print("Sending OTP to Telegram...")
    success = await send_otp(otp)
    
    if success:
        print("✓ OTP sent successfully! Check Telegram.")
    else:
        print("✗ Failed to send OTP. Check:")
        print("  1. Bot token is correct")
        print("  2. Chat ID is correct")
        print("  3. You started the bot (/start)")
        print("  4. Internet connection")

if __name__ == "__main__":
    asyncio.run(test_telegram())
