from typing import Optional, List, Tuple
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.attendance import Attendance
from app.models.user import User
from uuid import UUID


class AttendanceService:
    """Service for attendance operations"""
    
    @staticmethod
    def calculate_duration(punch_in: datetime, punch_out: datetime) -> str:
        """Calculate duration between punch in and punch out in HH:MM:SS format"""
        if not punch_in or not punch_out:
            return "00:00:00"
        # Ensure both are timezone-aware so subtraction works (DB returns aware; we write aware)
        if punch_in.tzinfo is None:
            punch_in = punch_in.replace(tzinfo=timezone.utc)
        if punch_out.tzinfo is None:
            punch_out = punch_out.replace(tzinfo=timezone.utc)
        duration = punch_out - punch_in
        total_seconds = int(duration.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    def punch_in(db: Session, user_id: UUID) -> Tuple[bool, str, Optional[Attendance]]:
        """
        Record punch-in for a user.
        Returns (success, message, attendance_record)
        """
        try:
            today = date.today().isoformat()
            
            # Check if user already punched in today
            existing = db.query(Attendance).filter(
                and_(
                    Attendance.user_id == user_id,
                    Attendance.date == today,
                    Attendance.punch_in_time.isnot(None),
                    Attendance.punch_out_time.is_(None)
                )
            ).first()
            
            if existing:
                return False, "You have already punched in today. Please punch out first.", None
            
            # Create new attendance record (use timezone-aware UTC to match DateTime(timezone=True))
            attendance = Attendance(
                user_id=user_id,
                punch_in_time=datetime.now(timezone.utc),
                date=today
            )
            
            db.add(attendance)
            db.commit()
            db.refresh(attendance)
            
            return True, "Punch-in successful", attendance
        
        except Exception as e:
            db.rollback()
            return False, f"Error punching in: {str(e)}", None
    
    @staticmethod
    def punch_out(db: Session, user_id: UUID) -> Tuple[bool, str, Optional[Attendance]]:
        """
        Record punch-out for a user.
        Returns (success, message, attendance_record)
        """
        try:
            today = date.today().isoformat()
            
            # Find today's punch-in record
            attendance = db.query(Attendance).filter(
                and_(
                    Attendance.user_id == user_id,
                    Attendance.date == today,
                    Attendance.punch_in_time.isnot(None),
                    Attendance.punch_out_time.is_(None)
                )
            ).first()
            
            if not attendance:
                return False, "No punch-in found for today. Please punch in first.", None
            
            # Record punch-out (timezone-aware UTC to match DB and punch_in_time)
            attendance.punch_out_time = datetime.now(timezone.utc)
            attendance.total_duration = AttendanceService.calculate_duration(
                attendance.punch_in_time,
                attendance.punch_out_time
            )
            
            db.commit()
            db.refresh(attendance)
            
            return True, "Punch-out successful", attendance
        
        except Exception as e:
            db.rollback()
            return False, f"Error punching out: {str(e)}", None
    
    @staticmethod
    def get_all_attendance(db: Session, limit: int = 100) -> List[Attendance]:
        """Get all attendance records with user information"""
        return db.query(Attendance).join(User).order_by(Attendance.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_user_attendance(db: Session, user_id: UUID, limit: int = 100) -> List[Attendance]:
        """Get attendance records for a specific user"""
        return db.query(Attendance).filter(
            Attendance.user_id == user_id
        ).order_by(Attendance.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_today_attendance(db: Session) -> List[Attendance]:
        """Get all attendance records for today"""
        today = date.today().isoformat()
        return db.query(Attendance).join(User).filter(
            Attendance.date == today
        ).order_by(Attendance.created_at.desc()).all()
