from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    event_name = Column(String(200), nullable=False)
    issue_date = Column(String(20), nullable=False)
    status = Column(String(30), default="pending")
    total = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")


class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    recipient_name = Column(String(300))
    email = Column(String(300))
    status = Column(String(20), default="pending")
    error_message = Column(Text)
    file_path = Column(String(500))
    job = relationship("Job", back_populates="certificates")