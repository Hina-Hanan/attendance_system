from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.face_service import FaceService
from app.services.attendance_service import AttendanceService
from app.schemas.auth import FaceAuthResponse
from app.schemas.attendance import AttendancePunch
from typing import Tuple, Optional

router = APIRouter()


@router.post("/register", response_model=dict)
async def register_user(
    username: str = Form(...),
    files: list[UploadFile] = File(...),
    user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Register a new user with face images.
    Requires 3-4 face images from different angles.
    Optional: user_id (unique UUID) - if not provided, one is auto-generated.
    """
    if len(files) < 3 or len(files) > 4:
        raise HTTPException(
            status_code=400,
            detail="Please upload or capture between 3 and 4 face images"
        )
    
    # Read all image files
    face_images = []
    for file in files:
        ct = getattr(file, 'content_type', None) or ''
        if ct and not ct.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"File {getattr(file, 'filename', 'image')} is not an image"
            )
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="One or more image files are empty")
        face_images.append(image_bytes)
    
    # Parse optional user_id (UUID string)
    from uuid import UUID
    parsed_user_id = None
    if user_id and user_id.strip():
        try:
            parsed_user_id = UUID(user_id.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="user_id must be a valid UUID")
    
    # Register user
    success, message, user = FaceService.register_user_faces(
        db, username, face_images, user_id=parsed_user_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "user_id": str(user.user_id),
        "user_number": user.user_number,
        "username": user.username
    }


@router.post("/authenticate", response_model=FaceAuthResponse)
async def authenticate_face(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Authenticate a face and return user information.
    - Single image: face match only (no spoof check).
    - 3+ images: spoof prevention (liveness) is run first; then face match on last frame.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")

    # Read all images
    image_bytes_list = []
    for f in files:
        ct = getattr(f, "content_type", None) or ""
        if ct and not ct.startswith("image/"):
            raise HTTPException(status_code=400, detail="All files must be images")
        b = await f.read()
        if not b:
            raise HTTPException(status_code=400, detail="One or more image files are empty")
        image_bytes_list.append(b)

    # Single image: no spoof check (backward compatible)
    if len(image_bytes_list) == 1:
        image_bytes = image_bytes_list[0]
    else:
        # Multiple images: run spoof prevention (liveness)
        from app.utils.spoof_prevention import check_liveness_sequence

        if len(image_bytes_list) < 3:
            raise HTTPException(
                status_code=400,
                detail="For liveness check please provide at least 3 frames (capture a short sequence)."
            )
        liveness_passed, last_frame_bytes = check_liveness_sequence(image_bytes_list)
        if not liveness_passed or last_frame_bytes is None:
            return FaceAuthResponse(
                success=False,
                message="Liveness check failed. Please try again with a live face (move slightly or blink).",
                confidence=0.0,
            )
        image_bytes = last_frame_bytes

    # Face authentication
    success, user, confidence, message = FaceService.authenticate_face(db, image_bytes)

    if not success:
        return FaceAuthResponse(
            success=False,
            message=message,
            confidence=0.0,
        )

    return FaceAuthResponse(
        success=True,
        user_id=user.user_id,
        username=user.username,
        confidence=confidence,
        message=message,
    )


@router.post("/punch", response_model=dict)
async def punch_attendance(
    request: AttendancePunch,
    db: Session = Depends(get_db)
):
    """
    Punch in or punch out for attendance.
    Requires user_id and action ("punch_in" or "punch_out").
    """
    if request.action not in ["punch_in", "punch_out"]:
        raise HTTPException(
            status_code=400,
            detail="Action must be 'punch_in' or 'punch_out'"
        )
    
    if request.action == "punch_in":
        success, message, attendance = AttendanceService.punch_in(db, request.user_id)
    else:
        success, message, attendance = AttendanceService.punch_out(db, request.user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "attendance_id": str(attendance.attendance_id),
        "punch_in_time": attendance.punch_in_time.isoformat() if attendance.punch_in_time else None,
        "punch_out_time": attendance.punch_out_time.isoformat() if attendance.punch_out_time else None,
        "total_duration": attendance.total_duration
    }
