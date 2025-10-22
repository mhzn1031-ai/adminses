import os
import uuid
import asyncio
import logging
from typing import Dict, Optional

from aiortc import RTCPeerConnection, RTCSessionDescription, MediaRecorder

RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "./recordings")

logger = logging.getLogger("webrtc_handler")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# Import for DB recording
try:
    from app.db import engine
    from app.models import Recording
    from sqlmodel import Session
    from datetime import datetime
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Keep active recorders per key (session_id + role)
_active_recorders: Dict[str, Dict] = {}
# Structure: key -> {"pc": RTCPeerConnection, "rec": MediaRecorder, "file": path}

def _make_key(session_id: str, role: str) -> str:
    return f"{session_id or 'nosess'}::{role}"

async def handle_record_offer(sdp: str, sdp_type: str, session_id: Optional[str], role: str) -> Dict:
    """
    Create an aiortc RTCPeerConnection, set remote description from the client's offer,
    create an answer and start MediaRecorder to local file. Returns {'sdp': answer_sdp, 'type': 'answer'}.
    """
    key = _make_key(session_id, role)
    # cleanup if exists
    await stop_recording(session_id, role)

    pc = RTCPeerConnection()

    filename = f"{session_id or uuid.uuid4().hex}_{role}_{uuid.uuid4().hex}.webm"
    filepath = os.path.join(RECORDINGS_DIR, filename)
    # MediaRecorder using file (requires ffmpeg available)
    recorder = MediaRecorder(filepath, format="webm")

    @pc.on("track")
    async def on_track(track):
        logger.info("Recorder: received track %s for session=%s role=%s", track.kind, session_id, role)
        await recorder.addTrack(track)

        @track.on("ended")
        async def on_ended():
            logger.info("Recorder: track ended for session=%s role=%s", session_id, role)
            # track ended - nothing immediate here; recorder will be closed on stop_recording or pc close

    # set remote offer
    offer = RTCSessionDescription(sdp, sdp_type)
    await pc.setRemoteDescription(offer)
    # create answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # start recorder
    await recorder.start()

    # save to active recorders
    _active_recorders[key] = {"pc": pc, "rec": recorder, "file": filepath}
    logger.info("Recorder started for key=%s file=%s", key, filepath)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

async def stop_recording(session_id: Optional[str], role: str) -> Optional[Dict]:
    """
    Stop recorder for session_id+role if exists. Returns metadata dict with filepath and s3 url (if uploaded).
    """
    key = _make_key(session_id, role)
    entry = _active_recorders.pop(key, None)
    if not entry:
        return None
    pc: RTCPeerConnection = entry.get("pc")
    rec: MediaRecorder = entry.get("rec")
    filepath: str = entry.get("file")
    try:
        # stop recorder first
        if rec:
            await rec.stop()
        # close peer connection
        if pc:
            await pc.close()
    except Exception:
        logger.exception("Error stopping recorder for key=%s", key)

    # Get file size
    file_size = 0
    try:
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
    except Exception:
        pass
    
    # Save to DB
    if DB_AVAILABLE and session_id:
        try:
            with Session(engine) as db:
                recording = Recording(
                    session_id=session_id,
                    role=role,
                    file_path=filepath,
                    size=file_size
                )
                db.add(recording)
                db.commit()
                logger.info("Recording saved to DB: session=%s role=%s", session_id, role)
        except Exception:
            logger.exception("Failed to save recording to DB")

    return {"file": filepath, "size": file_size}