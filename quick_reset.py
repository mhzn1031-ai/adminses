#!/usr/bin/env python3
"""Quick server reset - cleans all state"""
import os
import shutil
import asyncio

async def reset_redis():
    """Flush Redis cache"""
    try:
        import redis.asyncio as redis
        client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        await client.flushall()
        print("✓ Redis flushed")
        await client.close()
    except Exception as e:
        print(f"✗ Redis error: {e}")

def reset_database():
    """Drop and recreate database"""
    try:
        if os.path.exists("database.db"):
            os.remove("database.db")
            print("✓ Database deleted")
        
        from app.db import engine
        from app.models import SQLModel
        SQLModel.metadata.create_all(engine)
        print("✓ Database recreated")
        
        # Create admin user
        from app.auth import create_admin
        from sqlmodel import Session
        with Session(engine) as session:
            create_admin(session, "admin", "adminpass")
        print("✓ Admin user created (admin/adminpass)")
    except Exception as e:
        print(f"✗ Database error: {e}")

def reset_recordings():
    """Delete all recordings"""
    try:
        if os.path.exists("recordings"):
            shutil.rmtree("recordings")
            print("✓ Recordings deleted")
        os.makedirs("recordings", exist_ok=True)
        print("✓ Recordings folder recreated")
    except Exception as e:
        print(f"✗ Recordings error: {e}")

async def main():
    print("=" * 50)
    print("SERVER RESET - Cleaning all state")
    print("=" * 50)
    print()
    
    reset_database()
    await reset_redis()
    reset_recordings()
    
    print()
    print("=" * 50)
    print("RESET COMPLETE!")
    print("=" * 50)
    print()
    print("Cleaned:")
    print("  - All call sessions")
    print("  - All recordings")
    print("  - Redis cache (OTP, rate limits)")
    print("  - Admin user (recreated)")
    print()
    print("New admin:")
    print("  Username: admin")
    print("  Password: adminpass")
    print()

if __name__ == "__main__":
    asyncio.run(main())
