from sqlalchemy import Column, DateTime, String, ForeignKey, Integer, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    punch_in_time = Column(DateTime(timezone=True), nullable=True)
    punch_out_time = Column(DateTime(timezone=True), nullable=True)
    total_duration = Column(String(20), nullable=True)  # Store as "HH:MM:SS" string
    date = Column(String(10), nullable=False, index=True)  # Store as "YYYY-MM-DD"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    user = relationship("User", backref="attendance_records")

    def __repr__(self):
        return f"<Attendance(attendance_id={self.attendance_id}, user_id={self.user_id}, date={self.date})>"
