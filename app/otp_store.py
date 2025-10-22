import redis.asyncio as redis
from typing import Optional
import json

class OTPStore:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.otp_prefix = "otp:"
        self.expiry_seconds = 300  # 5 minutes

    async def set_otp(self, username: str, otp: str) -> bool:
        """Store OTP with expiry"""
        key = f"{self.otp_prefix}{username}"
        data = {"otp": otp, "attempts": 0}
        try:
            await self.redis.setex(key, self.expiry_seconds, json.dumps(data))
            return True
        except Exception:
            return False

    async def verify_otp(self, username: str, otp: str) -> bool:
        """Verify OTP and increment attempts"""
        key = f"{self.otp_prefix}{username}"
        try:
            data_str = await self.redis.get(key)
            if not data_str:
                return False

            data = json.loads(data_str)
            if data["attempts"] >= 3:  # Max 3 attempts
                await self.redis.delete(key)
                return False

            if data["otp"] == otp:
                await self.redis.delete(key)  # Clear on success
                return True
            else:
                data["attempts"] += 1
                await self.redis.setex(key, self.expiry_seconds, json.dumps(data))
                return False
        except Exception as e:
            print(f"OTP verification error: {e}")
            return False

    async def clear_otp(self, username: str) -> bool:
        """Manually clear OTP"""
        key = f"{self.otp_prefix}{username}"
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"OTP clear error: {e}")
            return False
