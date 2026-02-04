import face_recognition
import numpy as np
import cv2
from typing import List, Tuple, Optional
import json
from app.config import settings


def _decode_and_rgb(image_bytes: bytes) -> Optional[tuple]:
    """Decode image bytes to RGB. Returns (rgb_image, bgr_image) or None."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return None
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return (rgb_image, image)
    except Exception:
        return None


def encode_face_image(image_bytes: bytes, num_jitters: int = 1) -> Optional[np.ndarray]:
    """
    Encode a face from image bytes (original image, no preprocessing).
    Returns face encoding (128-dimensional vector) or None if no face found.
    """
    try:
        decoded = _decode_and_rgb(image_bytes)
        if decoded is None:
            return None
        rgb_image, _ = decoded
        face_locations = face_recognition.face_locations(rgb_image)
        if len(face_locations) == 0:
            return None
        face_encodings = face_recognition.face_encodings(
            rgb_image, face_locations, num_jitters=num_jitters
        )
        if len(face_encodings) == 0:
            return None
        return face_encodings[0]
    except Exception as e:
        print(f"Error encoding face: {e}")
        return None


def encode_face_image_enhanced(image_bytes: bytes, num_jitters: int = 1) -> Optional[np.ndarray]:
    """
    Enhanced face encoding with histogram equalization (helps in poor lighting).
    """
    try:
        decoded = _decode_and_rgb(image_bytes)
        if decoded is None:
            return None
        _, image = decoded
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        equalized = cv2.equalizeHist(gray)
        enhanced = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
        rgb_image = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        if len(face_locations) == 0:
            return None
        face_encodings = face_recognition.face_encodings(
            rgb_image, face_locations, num_jitters=num_jitters
        )
        if len(face_encodings) == 0:
            return None
        return face_encodings[0]
    except Exception as e:
        print(f"Error encoding face (enhanced): {e}")
        return None


def encode_face_image_robust(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Try to detect and encode a face: original image first, then enhanced.
    Uses more jitters for stable encoding. Reduces 'no face detected' and wrong-person matches.
    """
    num_jitters = getattr(settings, "FACE_ENCODING_NUM_JITTERS", 3)
    encoding = encode_face_image(image_bytes, num_jitters=num_jitters)
    if encoding is not None:
        return encoding
    return encode_face_image_enhanced(image_bytes, num_jitters=num_jitters)


def match_face(face_encoding: np.ndarray, stored_encodings: List[str], threshold: float = None) -> Tuple[bool, float]:
    """
    Match a face encoding against stored encodings.
    
    Args:
        face_encoding: The face encoding to match
        stored_encodings: List of stored encoding strings (JSON)
        threshold: Matching threshold (lower = stricter)
    
    Returns:
        Tuple of (is_match, best_distance)
    """
    if threshold is None:
        threshold = settings.FACE_MATCH_THRESHOLD
    
    if not stored_encodings:
        return False, float('inf')
    
    best_distance = float('inf')
    
    for stored_encoding_str in stored_encodings:
        try:
            stored_encoding = np.array(json.loads(stored_encoding_str))
            distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
            
            if distance < best_distance:
                best_distance = distance
        
        except Exception as e:
            print(f"Error matching encoding: {e}")
            continue
    
    is_match = best_distance <= threshold
    return is_match, best_distance


def check_duplicate_face(new_encoding: np.ndarray, all_stored_encodings: List[List[str]], threshold: float = None) -> bool:
    """
    Check if a face encoding already exists in the database.
    Used to prevent duplicate registrations.
    """
    if threshold is None:
        threshold = settings.FACE_MATCH_THRESHOLD
    
    for user_encodings in all_stored_encodings:
        is_match, _ = match_face(new_encoding, user_encodings, threshold)
        if is_match:
            return True
    
    return False


def encode_to_string(encoding: np.ndarray) -> str:
    """Convert numpy array encoding to JSON string for storage"""
    return json.dumps(encoding.tolist())


def string_to_encoding(encoding_str: str) -> np.ndarray:
    """Convert JSON string encoding back to numpy array"""
    return np.array(json.loads(encoding_str))
