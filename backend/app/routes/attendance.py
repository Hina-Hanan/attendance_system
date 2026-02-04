from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import AttendanceResponse
from app.models.user import User
from app.models.attendance import Attendance

router = APIRouter()


@router.get("/", response_model=List[AttendanceResponse])
def get_all_attendance(limit: int = 100, db: Session = Depends(get_db)):
    """Get all attendance records"""
    records = AttendanceService.get_all_attendance(db, limit)
    # Convert to response format with username
    result = []
    for record in records:
        result.append({
            "attendance_id": record.attendance_id,
            "user_id": record.user_id,
            "user_number": record.user.user_number if record.user else None,
            "username": record.user.username if record.user else "Unknown",
            "punch_in_time": record.punch_in_time,
            "punch_out_time": record.punch_out_time,
            "total_duration": record.total_duration,
            "date": record.date
        })
    return result


@router.get("/today", response_model=List[AttendanceResponse])
def get_today_attendance(db: Session = Depends(get_db)):
    """Get today's attendance records"""
    records = AttendanceService.get_today_attendance(db)
    result = []
    for record in records:
        result.append({
            "attendance_id": record.attendance_id,
            "user_id": record.user_id,
            "user_number": record.user.user_number if record.user else None,
            "username": record.user.username,
            "punch_in_time": record.punch_in_time,
            "punch_out_time": record.punch_out_time,
            "total_duration": record.total_duration,
            "date": record.date
        })
    return result


@router.get("/by-date", response_model=List[AttendanceResponse])
def get_attendance_by_date(date: str, limit: int = 500, db: Session = Depends(get_db)):
    """Get all attendance records for a specific date (YYYY-MM-DD)."""
    records = (
        db.query(Attendance)
        .join(User)
        .filter(Attendance.date == date)
        .order_by(Attendance.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for record in records:
        result.append({
            "attendance_id": record.attendance_id,
            "user_id": record.user_id,
            "user_number": record.user.user_number if record.user else None,
            "username": record.user.username if record.user else "Unknown",
            "punch_in_time": record.punch_in_time,
            "punch_out_time": record.punch_out_time,
            "total_duration": record.total_duration,
            "date": record.date
        })
    return result


@router.get("/user/{user_id}", response_model=List[AttendanceResponse])
def get_user_attendance(user_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """Get attendance records for a specific user"""
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return []
    
    records = AttendanceService.get_user_attendance(db, user_uuid, limit)
    # Load user for each record
    result = []
    for record in records:
        user = db.query(User).filter(User.user_id == record.user_id).first()
        result.append({
            "attendance_id": record.attendance_id,
            "user_id": record.user_id,
            "user_number": user.user_number if user else None,
            "username": user.username if user else "Unknown",
            "punch_in_time": record.punch_in_time,
            "punch_out_time": record.punch_out_time,
            "total_duration": record.total_duration,
            "date": record.date
        })
    return result


@router.get("/daily-summary")
def get_daily_summary(date: str, db: Session = Depends(get_db)):
    """Get per-user daily summary for a date (YYYY-MM-DD): sessions and total active duration."""
    if not date or len(date) != 10:
        return {"date": date, "summaries": []}
    summaries = AttendanceService.get_daily_summary(db, date)
    return {"date": date, "summaries": summaries}


@router.get("/user-number/{user_number}", response_model=List[AttendanceResponse])
def get_user_attendance_by_number(
    user_number: int,
    limit: int = 200,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get attendance records for a user by small User ID (user_number). Optionally filter by date (YYYY-MM-DD)."""
    user = db.query(User).filter(User.user_number == user_number).first()
    if not user:
        return []

    q = (
        db.query(Attendance)
        .join(User)
        .filter(Attendance.user_id == user.user_id)
    )
    if date:
        q = q.filter(Attendance.date == date)

    records = q.order_by(Attendance.created_at.desc()).limit(limit).all()

    result = []
    for record in records:
        result.append({
            "attendance_id": record.attendance_id,
            "user_id": record.user_id,
            "user_number": user.user_number,
            "username": user.username,
            "punch_in_time": record.punch_in_time,
            "punch_out_time": record.punch_out_time,
            "total_duration": record.total_duration,
            "date": record.date
        })
    return result
