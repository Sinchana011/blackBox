# backend/models.py
import datetime
import enum
import uuid

from sqlalchemy import Column, String, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID

from database import Base

class ScanStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_url = Column(String, index=True, nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
class RawFinding(Base):
    __tablename__ = "raw_findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(UUID(as_uuid=True), index=True)
    tool_source = Column(String, nullable=False)
    name = Column(String, nullable=False)
    severity = Column(String)
    url = Column(String)
    evidence = Column(String)


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(UUID(as_uuid=True), index=True)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)