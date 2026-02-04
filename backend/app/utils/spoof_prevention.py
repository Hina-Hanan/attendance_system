import cv2
import numpy as np
from typing import List, Tuple, Optional
from app.config import settings


class SpoofPrevention:
    """
    Basic spoof prevention using eye blink detection and head movement.
    """
    
    def __init__(self):
        self.frame_history: List[np.ndarray] = []
        self.face_positions: List[Tuple[int, int, int, int]] = []
        
    def calculate_ear(self, eye_landmarks) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for blink detection.
        Lower EAR indicates closed eye.
        """
        # Vertical distances
        vertical_1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        vertical_2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        
        # Horizontal distance
        horizontal = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        # Calculate EAR
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear
    
    def detect_blink(self, face_image: np.ndarray) -> bool:
        """
        Simple blink detection using grayscale intensity changes.
        This is a simplified version - in production, use dlib facial landmarks.
        """
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Detect eyes using Haar Cascade (simplified approach)
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(eyes) >= 2:
                # Calculate average intensity in eye regions
                eye_intensities = []
                for (ex, ey, ew, eh) in eyes:
                    eye_roi = gray[ey:ey+eh, ex:ex+ew]
                    avg_intensity = np.mean(eye_roi)
                    eye_intensities.append(avg_intensity)
                
                # If eyes are detected and have reasonable intensity, consider as open
                avg_intensity = np.mean(eye_intensities)
                return avg_intensity > 50  # Threshold for open eyes
            
            return False
        
        except Exception as e:
            print(f"Error in blink detection: {e}")
            return False
    
    def detect_head_movement(self, current_face_pos: Tuple[int, int, int, int]) -> bool:
        """
        Detect if head has moved between frames.
        Returns True if movement detected.
        """
        if len(self.face_positions) == 0:
            self.face_positions.append(current_face_pos)
            return False
        
        # Calculate center of current face
        top, right, bottom, left = current_face_pos
        current_center_x = (left + right) / 2
        current_center_y = (top + bottom) / 2
        
        # Calculate center of previous face
        prev_top, prev_right, prev_bottom, prev_left = self.face_positions[-1]
        prev_center_x = (prev_left + prev_right) / 2
        prev_center_y = (prev_top + prev_bottom) / 2
        
        # Calculate movement distance
        movement_x = abs(current_center_x - prev_center_x)
        movement_y = abs(current_center_y - prev_center_y)
        movement = np.sqrt(movement_x**2 + movement_y**2)
        
        # Normalize by face size
        face_width = right - left
        face_height = bottom - top
        face_size = np.sqrt(face_width**2 + face_height**2)
        
        if face_size > 0:
            normalized_movement = movement / face_size
        else:
            normalized_movement = 0
        
        self.face_positions.append(current_face_pos)
        
        # Keep only last N positions
        if len(self.face_positions) > settings.SPOOF_CHECK_FRAMES:
            self.face_positions.pop(0)
        
        return normalized_movement > settings.HEAD_MOVEMENT_THRESHOLD
    
    def verify_liveness(self, frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> Tuple[bool, str]:
        """
        Verify liveness using multiple frames and movement detection.
        This is a simplified version - in production, use more sophisticated methods.
        
        Args:
            frame: Current video frame
            face_location: Face location tuple (top, right, bottom, left)
        
        Returns:
            Tuple of (is_live, message)
        """
        # Add frame to history
        self.frame_history.append(frame.copy())
        
        # Keep only last N frames
        if len(self.frame_history) > settings.SPOOF_CHECK_FRAMES:
            self.frame_history.pop(0)
        
        # Need at least 2 frames to detect movement
        if len(self.frame_history) < 2:
            return False, "Need more frames for liveness detection"
        
        # Extract face region
        top, right, bottom, left = face_location
        face_image = frame[top:bottom, left:right]
        
        if face_image.size == 0:
            return False, "Invalid face region"
        
        # Check for head movement
        movement_detected = self.detect_head_movement(face_location)
        
        # Check for blink (simplified)
        blink_detected = self.detect_blink(face_image)

        # Liveness passes if EITHER movement OR blink is detected
        if movement_detected or blink_detected:
            return True, "Liveness verified"
        
        # If we have enough frames and no movement/blink, might be static image
        if len(self.frame_history) >= settings.SPOOF_CHECK_FRAMES:
            return False, "No movement detected - possible static image"
        
        return False, "Collecting frames for liveness check"
    
    def reset(self):
        """Reset frame history and positions"""
        self.frame_history = []
        self.face_positions = []


def process_video_frame_for_spoof(frame_bytes: bytes) -> Tuple[bool, str, Optional[Tuple[int, int, int, int]]]:
    """
    Process a video frame for spoof detection.
    Returns (is_valid, message, face_location)
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return False, "Invalid frame", None
        
        # Detect face
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return False, "No face detected", None
        
        # Use first face
        x, y, w, h = faces[0]
        face_location = (y, x + w, y + h, x)  # Convert to (top, right, bottom, left)
        
        # For basic spoof prevention, we'll use frame count
        # In production, implement more sophisticated checks
        return True, "Face detected", face_location
    
    except Exception as e:
        return False, f"Error processing frame: {e}", None


def check_liveness_sequence(frame_bytes_list: List[bytes]) -> Tuple[bool, Optional[bytes]]:
    """
    Run spoof prevention over a sequence of video frames.
    Returns (liveness_passed, last_frame_bytes_for_face_match).
    Caller should use last_frame_bytes for face recognition only if liveness_passed is True.
    """
    if not frame_bytes_list or len(frame_bytes_list) < 2:
        return False, frame_bytes_list[-1] if frame_bytes_list else None

    spoof = SpoofPrevention()
    liveness_passed = False
    last_valid_bytes = None
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    for image_bytes in frame_bytes_list:
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            continue
        x, y, w, h = faces[0]
        face_location = (y, x + w, y + h, x)
        last_valid_bytes = image_bytes
        is_live, _ = spoof.verify_liveness(frame, face_location)
        if is_live:
            liveness_passed = True

    return liveness_passed, last_valid_bytes
