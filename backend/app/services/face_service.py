from typing import List, Optional, Tuple
from uuid import UUID
import numpy as np
from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.face_recognition_utils import (
    encode_face_image_robust,
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
            
            # Encode all face images (robust: try original + enhanced, better encoding)
            encodings = []
            for idx, image_bytes in enumerate(face_images):
                encoding = encode_face_image_robust(image_bytes)
                if encoding is None:
                    return False, f"Failed to detect face in image {idx + 1}. Please ensure face is clearly visible.", None
                encodings.append(encoding)
            
            # Check for duplicate faces (prevent same person registering twice)
            # Use stricter threshold so siblings/similar faces aren't falsely rejected
            all_users = db.query(User).all()
            all_stored_encodings = [user.face_encodings for user in all_users]
            
            for encoding in encodings:
                if check_duplicate_face(encoding, all_stored_encodings, threshold=settings.FACE_DUPLICATE_CHECK_THRESHOLD):
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
        Uses stricter threshold and rejects ambiguous matches (two users too close).
        
        Returns:
            Tuple of (success, user_object, confidence_score, message)
        """
        try:
            face_encoding = encode_face_image_robust(face_image)
            if face_encoding is None:
                return False, None, 0.0, "No face detected. Ensure your face is clearly visible and well lit."
            
            users = db.query(User).all()
            if not users:
                return False, None, 0.0, "No users registered in system"
            
            auth_threshold = getattr(settings, "FACE_AUTH_THRESHOLD", settings.FACE_MATCH_THRESHOLD)
            ambiguity_margin = getattr(settings, "FACE_AUTH_AMBIGUITY_MARGIN", 0.08)
            
            # Get distance to every user (use auth threshold for match)
            distances = []
            for user in users:
                is_match, distance = match_face(face_encoding, user.face_encodings, threshold=auth_threshold)
                if is_match:
                    distances.append((distance, user))
            
            if not distances:
                return False, None, 0.0, "Face not recognized. Please register first."
            
            # Sort by distance (best first)
            distances.sort(key=lambda x: x[0])
            best_distance, best_user = distances[0]
            second_best_distance = distances[1][0] if len(distances) > 1 else float("inf")
            
            # Reject if two users are too close (ambiguous match)
            if second_best_distance - best_distance < ambiguity_margin:
                return False, None, 0.0, "Match unclear. Please try again in better lighting or move slightly."
            
            confidence = max(0.0, min(1.0, 1.0 - best_distance))
            return True, best_user, confidence, "Authentication successful"
        
        except Exception as e:
            return False, None, 0.0, f"Error authenticating face: {str(e)}"
