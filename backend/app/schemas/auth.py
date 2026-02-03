from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class FaceAuthRequest(BaseModel):
    face_image: bytes


class FaceAuthResponse(BaseModel):
    success: bool
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    confidence: Optional[float] = None
    message: str
