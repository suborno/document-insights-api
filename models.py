from sqlalchemy import Column, Integer, String, Text, DateTime, Index, func
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # index for filtering by user and status
    __table_args__ = (Index("ix_user_status", "user_id", "status"),)
