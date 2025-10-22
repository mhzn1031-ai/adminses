import os
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from typing import Dict, Set
from contextlib import asynccontextmanager

from app.webrtc_handler import handle_record_offer, stop_recording as webrtc_stop_recording
from app.telegram_bot import send_call_notification, send_otp, generate_otp
from app.otp_store import OTPStore
from app.models import CallSession
from app.db import init_db, engine
from app.auth import get_admin_by_username, create_access_token
from sqlmodel import Session, select
from datetime import datetime
import redis.asyncio as redis

# Redis client
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)



# OTP Store
otp_store = OTPStore(redis_client)

# WebSocket connections
active_connections: Dict[str, WebSocket] = {}
session_connections: Dict[str, Set[str]] = {}  # session_id -> set of client_ids

logger = logging.getLogger("main")

# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    # Seed admin user
    from app.auth import create_admin
    with Session(engine) as session:
        create_admin(session, os.getenv("ADMIN_USER", "admin"), os.getenv("ADMIN_PASS", "adminpass"))
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

# CORS - Production: restrict origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Daily call limit check
async def check_daily_limit() -> bool:
    """Check if daily call limit (10) is exceeded"""
    today = datetime.utcnow().date()
    with Session(engine) as db:
        statement = select(CallSession).where(
            CallSession.start_time >= today,
            CallSession.status.in_(["accepted", "ended"])
        )
        today_calls = db.exec(statement).all()
        return len(today_calls) < 10

# Request OTP endpoint with rate limiting
@app.post("/api/auth/request-otp")
async def request_otp(req: Request):
    data = await req.json()
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="username required")

    # Rate limiting: 3 attempts per minute per username
    rate_key = f"otp_rate:{username}"
    attempts = await redis_client.incr(rate_key)
    if attempts == 1:
        await redis_client.expire(rate_key, 60)  # 1 minute
    if attempts > 3:
        raise HTTPException(status_code=429, detail="Too many OTP requests. Try again later.")

    with Session(engine) as session:
        user = get_admin_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()
    await otp_store.set_otp(username, otp)
    success = await send_otp(otp)
    return {"ok": success, "message": "OTP sent to Telegram" if success else "Telegram not configured"}

# Verify OTP endpoint
@app.post("/api/auth/verify-otp")
async def verify_otp(req: Request):
    data = await req.json()
    username = data.get("username")
    otp = data.get("otp")
    if not username or not otp:
        raise HTTPException(status_code=400, detail="username and otp required")

    valid = await otp_store.verify_otp(username, otp)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    with Session(engine) as session:
        user = get_admin_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        token = create_access_token(user.username)

    return {"access_token": token, "token_type": "bearer"}

# Call notification endpoint
@app.post("/api/call/notify")
async def notify_call(req: Request):
    data = await req.json()
    caller_name = data.get("caller_name", "Anonim")
    caller_id = data.get("caller_id")
    session_id = data.get("session_id")
    
    if not caller_id or not session_id:
        raise HTTPException(status_code=400, detail="caller_id and session_id required")
    
    # Add caller to session
    add_client_to_session(session_id, caller_id)
    
    # Save to DB
    with Session(engine) as db:
        call = CallSession(
            session_id=session_id,
            caller_id=caller_id,
            caller_name=caller_name,
            status="pending"
        )
        db.add(call)
        db.commit()
    
    # Send Telegram notification
    await send_call_notification(caller_name)
    
    # Broadcast pending_update to all admin clients
    for client_id, ws_conn in active_connections.items():
        if client_id.startswith("agent_"):
            try:
                await ws_conn.send_text(json.dumps({
                    "type": "pending_update"
                }))
            except Exception:
                pass
    
    return {"ok": True}

# Accept/Reject call endpoint
@app.post("/api/call/respond")
async def respond_call(req: Request):
    data = await req.json()
    session_id = data.get("session_id")
    action = data.get("action")  # "accept" or "reject"
    agent_id = data.get("agent_id")
    
    if not session_id or action not in ["accept", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    # Check daily limit for accept action
    if action == "accept":
        limit_ok = await check_daily_limit()
        if not limit_ok:
            raise HTTPException(status_code=429, detail="Daily call limit exceeded (10 calls)")
    
    with Session(engine) as db:
        statement = select(CallSession).where(CallSession.session_id == session_id)
        call = db.exec(statement).first()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        call.status = "accepted" if action == "accept" else "rejected"
        if action == "accept":
            call.agent_id = agent_id
            # Add agent to session
            add_client_to_session(session_id, agent_id)
        db.add(call)
        db.commit()
    
    return {"ok": True, "action": action}

# End call and update duration
@app.post("/api/call/end")
async def end_call(req: Request):
    data = await req.json()
    session_id = data.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    with Session(engine) as db:
        statement = select(CallSession).where(CallSession.session_id == session_id)
        call = db.exec(statement).first()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        call.status = "ended"
        call.end_time = datetime.utcnow()
        if call.start_time:
            call.duration = int((call.end_time - call.start_time).total_seconds())
        db.add(call)
        db.commit()

    # Broadcast call_ended to other clients in session
    if session_id in session_connections:
        for other_client in session_connections[session_id]:
            if other_client in active_connections:
                try:
                    await active_connections[other_client].send_text(json.dumps({
                        "type": "call_ended"
                    }))
                except Exception:
                    pass

    return {"ok": True}

# Get call history
@app.get("/api/calls/history")
async def get_call_history(req: Request, limit: int = 50):
    with Session(engine) as db:
        statement = select(CallSession).order_by(CallSession.start_time.desc()).limit(limit)
        calls = db.exec(statement).all()
        return [{"id": c.id, "session_id": c.session_id, "caller_name": c.caller_name, 
                 "status": c.status, "start_time": c.start_time.isoformat(), 
                 "duration": c.duration, "agent_id": c.agent_id} for c in calls]

# Get pending calls
@app.get("/api/calls/pending")
async def get_pending_calls(req: Request):
    with Session(engine) as db:
        statement = select(CallSession).where(CallSession.status == "pending").order_by(CallSession.start_time.desc())
        calls = db.exec(statement).all()
        return [{"id": c.id, "session_id": c.session_id, "caller_name": c.caller_name, 
                 "start_time": c.start_time.isoformat()} for c in calls]

@app.post("/api/record/offer")
async def record_offer_endpoint(req: Request):
    """
    Accepts JSON body:
    {
      "sdp": "<offer sdp>",
      "type": "offer",
      "session_id": "<optional session id>",
      "role": "agent"|"caller"
    }
    Returns:
    { "sdp": "<answer sdp>", "type": "answer" }
    """
    data = await req.json()
    sdp = data.get("sdp")
    sdp_type = data.get("type", "offer")
    session_id = data.get("session_id")
    role = data.get("role", "unknown")
    if not sdp:
        raise HTTPException(status_code=400, detail="sdp required")
    try:
        res = await handle_record_offer(sdp, sdp_type, session_id, role)
        return res
    except Exception as e:
        logger.exception("handle_record_offer failed")
        raise HTTPException(status_code=500, detail="record offer failed")

@app.post("/api/record/stop")
async def record_stop_endpoint(req: Request):
    """
    Accepts JSON body:
    { "session_id": "<session>", "role": "agent"|"caller" }
    Stops server-side recording and returns file info.
    """
    data = await req.json()
    session_id = data.get("session_id")
    role = data.get("role", "unknown")
    try:
        info = await webrtc_stop_recording(session_id, role)
        if not info:
            return {"ok": False, "msg": "no active recorder"}
        return {"ok": True, "file": info.get("file"), "s3": info.get("s3")}
    except Exception:
        logger.exception("record_stop failed")
        raise HTTPException(status_code=500, detail="stop failed")

# WebSocket endpoint for signaling
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            
            if msg_type == "join_session":
                # Add client to session
                session_id = message.get("session_id")
                if session_id:
                    add_client_to_session(session_id, client_id)

            elif msg_type == "offer":
                # Agent sending offer to caller
                target_session = message.get("target")
                if target_session and target_session in session_connections:
                    # Find caller in session
                    for conn_id in session_connections[target_session]:
                        if conn_id.startswith("caller_"):
                            if conn_id in active_connections:
                                await active_connections[conn_id].send_text(json.dumps({
                                    "type": "offer",
                                    "sdp": message["sdp"]
                                }))
                            break

            elif msg_type == "answer":
                # Caller sending answer to agent
                target_session = message.get("target")
                if target_session and target_session in session_connections:
                    # Find agent in session
                    for conn_id in session_connections[target_session]:
                        if conn_id.startswith("agent_"):
                            if conn_id in active_connections:
                                await active_connections[conn_id].send_text(json.dumps({
                                    "type": "answer",
                                    "sdp": message["sdp"]
                                }))
                            break

            elif msg_type == "ice_candidate":
                # Forward ICE candidates
                target_session = message.get("target")
                if target_session and target_session in session_connections:
                    # Send to all other clients in session
                    for conn_id in session_connections[target_session]:
                        if conn_id != client_id and conn_id in active_connections:
                            await active_connections[conn_id].send_text(json.dumps({
                                "type": "ice_candidate",
                                "candidate": message["candidate"]
                            }))

    except WebSocketDisconnect:
        # Remove from active connections
        if client_id in active_connections:
            del active_connections[client_id]

        # Remove from session connections
        for session_id, clients in session_connections.items():
            if client_id in clients:
                clients.remove(client_id)
                if not clients:
                    del session_connections[session_id]
                break

        # Broadcast call_ended to other clients in session
        for session_id, clients in session_connections.items():
            if client_id in clients:
                for other_client in clients:
                    if other_client != client_id and other_client in active_connections:
                        try:
                            await active_connections[other_client].send_text(json.dumps({
                                "type": "call_ended"
                            }))
                        except Exception:
                            pass
                break

# Helper function to add client to session
def add_client_to_session(session_id: str, client_id: str):
    if session_id not in session_connections:
        session_connections[session_id] = set()
    session_connections[session_id].add(client_id)

# Root endpoint
@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head>
            <title>Teknik Destek Sistemi</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .links { margin: 20px; }
                .links a { margin: 10px; padding: 10px 20px; text-decoration: none; color: white; background: #007bff; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Teknik Destek Sistemi</h1>
            <div class="links">
                <a href="/static/index.html">Müşteri Girişi</a>
                <a href="/static/admin.html">Admin Paneli</a>
            </div>
        </body>
    </html>
    """)
