from sqlmodel import SQLModel, Field
from datetime import datetime

class AdminUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    hashed_password: str
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CallSession(SQLModel, table=True):
    """Call session metadata"""
    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, unique=True)
    caller_id: str = Field(index=True)
    caller_name: str
    agent_id: str | None = Field(default=None, index=True)
    status: str = Field(default="pending")  # pending, accepted, rejected, ended
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = Field(default=None)
    duration: int | None = Field(default=None)  # seconds

class Recording(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: str | None = Field(default=None, index=True)
    role: str | None = Field(default=None)
    file_path: str | None = Field(default=None)
    size: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)