from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)


class UserResponse(BaseModel):
    user_id: UUID
    user_number: Optional[int] = None  # Small ID (1, 2, 3...) for unique identification
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    face_images: List[bytes] = Field(..., min_items=3, max_items=4)
