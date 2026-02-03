from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AttendanceCreate(BaseModel):
    user_id: UUID
    punch_in_time: Optional[datetime] = None
    punch_out_time: Optional[datetime] = None


class AttendanceResponse(BaseModel):
    attendance_id: UUID
    user_id: UUID
    user_number: Optional[int] = None  # Small ID (1, 2, 3...) for unique identification
    username: str
    punch_in_time: Optional[datetime]
    punch_out_time: Optional[datetime]
    total_duration: Optional[str]
    date: str

    class Config:
        from_attributes = True


class AttendancePunch(BaseModel):
    user_id: UUID
    action: str  # "punch_in" or "punch_out"
