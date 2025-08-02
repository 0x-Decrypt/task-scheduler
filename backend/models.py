from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4, UUID as PyUUID

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

# Custom UUID type for SQLite compatibility
class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return CHAR(36)
        else:
            return dialect.type_descriptor(UUID())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'sqlite':
            return str(value)
        else:
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, PyUUID):
                return PyUUID(value)
            return value


class ScheduleType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval" 
    ONCE = "once"
    STARTUP = "startup"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DISABLED = "disabled"


class TaskModel(Base):
    __tablename__ = "tasks"
    
    id = Column(GUID(), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    command = Column(Text, nullable=False)
    schedule_type = Column(String(50), nullable=False)
    schedule_config = Column(Text)  # JSON string
    enabled = Column(Boolean, default=True)
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    timeout = Column(Integer, default=3600)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskExecutionModel(Base):
    __tablename__ = "task_executions"
    
    id = Column(GUID(), primary_key=True, default=uuid4)
    task_id = Column(GUID(), nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    exit_code = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)
    error_message = Column(Text)


class TaskCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    command: str = Field(..., min_length=1)
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    enabled: bool = True
    notify_on_success: bool = False
    notify_on_failure: bool = True
    timeout: int = Field(default=3600, ge=1, le=86400)
    
    @validator('schedule_config')
    def validate_schedule_config(cls, v, values):
        schedule_type = values.get('schedule_type')
        if schedule_type == ScheduleType.CRON:
            if 'expression' not in v:
                raise ValueError("Cron schedule requires 'expression' field")
        elif schedule_type == ScheduleType.INTERVAL:
            if 'seconds' not in v and 'minutes' not in v and 'hours' not in v:
                raise ValueError("Interval schedule requires time unit")
        elif schedule_type == ScheduleType.ONCE:
            if 'run_date' not in v:
                raise ValueError("Once schedule requires 'run_date' field")
        return v


class TaskUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    command: Optional[str] = Field(None, min_length=1)
    schedule_type: Optional[ScheduleType] = None
    schedule_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    timeout: Optional[int] = Field(None, ge=1, le=86400)


class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    command: str
    schedule_type: str
    schedule_config: Dict[str, Any]
    enabled: bool
    notify_on_success: bool
    notify_on_failure: bool
    timeout: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskExecutionResponse(BaseModel):
    id: str
    task_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
