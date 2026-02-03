from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
from app.database import Base


class User(Base):
    # Use a non-reserved table name to avoid conflicts with
    # built-in PostgreSQL types on some managed providers.
    __tablename__ = "app_users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_number = Column(Integer, unique=True, nullable=True, index=True)  # Small ID 1, 2, 3... (order of registration)
    username = Column(String(100), nullable=False, index=True)  # No longer unique: same name allowed
    face_encodings = Column(ARRAY(Text), nullable=False)  # Store multiple encodings as JSON strings
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"
