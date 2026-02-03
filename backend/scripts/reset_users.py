"""
One-time script: Delete all users and their attendance so you can start fresh.

Run from the backend folder WITH THE VENV ACTIVE (or use venv's Python):

  Option 1 - venv activated:
    .\venv\Scripts\activate
    python -m scripts.reset_users

  Option 2 - venv not activated (Windows):
    .\venv\Scripts\python.exe -m scripts.reset_users
"""
import sys
from pathlib import Path

# Ensure backend/app is on path when run as python -m scripts.reset_users
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

try:
    from app.database import SessionLocal
    from app.models.attendance import Attendance
    from app.models.user import User
except ModuleNotFoundError as e:
    print("Error: Dependencies not found. Run this script using the backend venv:")
    print("  .\\venv\\Scripts\\python.exe -m scripts.reset_users")
    print("Or activate the venv first: .\\venv\\Scripts\\activate")
    sys.exit(1)


def main():
    db = SessionLocal()
    try:
        deleted_attendance = db.query(Attendance).delete()
        deleted_users = db.query(User).delete()
        db.commit()
        print(f"Deleted {deleted_attendance} attendance record(s) and {deleted_users} user(s).")
        print("You can register again; new users will get User ID 1, 2, 3...")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
