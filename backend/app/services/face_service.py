from typing import List, Optional, Tuple
from uuid import UUID
import numpy as np
from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.face_recognition_utils import (
    encode_face_image_enhanced,
    match_face,
    check_duplicate_face,
    encode_to_string
)
from app.config import settings


class FaceService:
    """Service for face recognition operations"""
    
    @staticmethod
    def register_user_faces(
        db: Session,
        username: str,
        face_images: List[bytes],
        user_id: Optional[UUID] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user with multiple face images.
        Optional user_id: if provided, must be unique; otherwise auto-generated.
        
        Returns:
            Tuple of (success, message, user_object)
        """
        try:
            # Validate number of images
            if len(face_images) < settings.MIN_FACE_IMAGES_REQUIRED:
                return False, f"At least {settings.MIN_FACE_IMAGES_REQUIRED} face images required", None
            
            if len(face_images) > settings.MAX_FACE_IMAGES_REQUIRED:
                return False, f"Maximum {settings.MAX_FACE_IMAGES_REQUIRED} face images allowed", None
            
            # Assign next user_number (small ID 1, 2, 3... in registration order)
            from sqlalchemy import func
            next_number = db.query(func.coalesce(func.max(User.user_number), 0)).scalar() + 1
            
            # If user_id provided, check it's unique
            if user_id is not None:
                existing = db.query(User).filter(User.user_id == user_id).first()
                if existing:
                    return False, "This user_id is already in use. Choose a different one or leave empty to auto-generate.", None
            
            # Encode all face images
            encodings = []
            for idx, image_bytes in enumerate(face_images):
                encoding = encode_face_image_enhanced(image_bytes)
                if encoding is None:
                    return False, f"Failed to detect face in image {idx + 1}. Please ensure face is clearly visible.", None
                encodings.append(encoding)
            
            # Check for duplicate faces (prevent same person registering twice)
            all_users = db.query(User).all()
            all_stored_encodings = [user.face_encodings for user in all_users]
            
            for encoding in encodings:
                if check_duplicate_face(encoding, all_stored_encodings):
                    return False, "This face is already registered. Please use a different person.", None
            
            # Convert encodings to strings for storage
            encoding_strings = [encode_to_string(enc) for enc in encodings]
            
            # Create user (with optional user_id and auto user_number)
            user = User(
                username=username,
                face_encodings=encoding_strings,
                user_number=next_number
            )
            if user_id is not None:
                user.user_id = user_id
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return True, f"User registered successfully with {len(encodings)} face images", user
        
        except Exception as e:
            db.rollback()
            return False, f"Error registering user: {str(e)}", None
    
    @staticmethod
    def authenticate_face(db: Session, face_image: bytes) -> Tuple[bool, Optional[User], float, str]:
        """
        Authenticate a face against registered users.
        
        Returns:
            Tuple of (success, user_object, confidence_score, message)
        """
        try:
            # Encode the face
            face_encoding = encode_face_image_enhanced(face_image)
            if face_encoding is None:
                return False, None, 0.0, "No face detected in image"
            
            # Get all users
            users = db.query(User).all()
            
            if not users:
                return False, None, 0.0, "No users registered in system"
            
            # Match against all users
            best_match = None
            best_distance = float('inf')
            
            for user in users:
                is_match, distance = match_face(face_encoding, user.face_encodings)
                if is_match and distance < best_distance:
                    best_match = user
                    best_distance = distance
            
            if best_match:
                # Convert distance to confidence (lower distance = higher confidence)
                confidence = max(0.0, min(1.0, 1.0 - best_distance))
                return True, best_match, confidence, f"Authentication successful"
            else:
                return False, None, 0.0, "Face not recognized. Please register first."
        
        except Exception as e:
            return False, None, 0.0, f"Error authenticating face: {str(e)}"
