from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import pandas as pd
import io
from app.database import get_db
from app.services.attendance_service import AttendanceService
from app.models.attendance import Attendance
from app.models.user import User

router = APIRouter()


@router.get("/csv")
def export_attendance_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export attendance data to CSV.
    Optional query parameters: start_date and end_date (YYYY-MM-DD format)
    """
    try:
        # Get all attendance records
        query = db.query(Attendance).join(User)
        
        # Filter by date range if provided
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        records = query.order_by(Attendance.date.desc(), Attendance.created_at.desc()).all()
        
        # Prepare data for CSV
        data = []
        for record in records:
            data.append({
                "user_number": record.user.user_number if record.user and record.user.user_number is not None else "",
                "user_id": str(record.user_id),
                "username": record.user.username,
                "date": record.date,
                "punch_in": record.punch_in_time.isoformat() if record.punch_in_time else "",
                "punch_out": record.punch_out_time.isoformat() if record.punch_out_time else "",
                "total_duration": record.total_duration or "00:00:00"
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Convert to CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"attendance_export_{timestamp}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")
