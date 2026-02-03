# Project Structure

```
face_attendance_system/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Database connection and session
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # User model (SQLAlchemy)
│   │   │   └── attendance.py      # Attendance model (SQLAlchemy)
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # User Pydantic schemas
│   │   │   ├── attendance.py      # Attendance Pydantic schemas
│   │   │   └── auth.py            # Authentication schemas
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py        # Router aggregation
│   │   │   ├── auth.py            # Authentication & registration endpoints
│   │   │   ├── users.py           # User management endpoints
│   │   │   ├── attendance.py      # Attendance endpoints
│   │   │   └── export.py          # CSV export endpoint
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── face_service.py    # Face recognition business logic
│   │   │   └── attendance_service.py  # Attendance business logic
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── face_recognition_utils.py  # Face encoding/matching utilities
│   │       └── spoof_prevention.py        # Spoof detection utilities
│   │
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Docker image for backend
│   ├── start.sh                   # Linux/Mac startup script
│   ├── start.bat                  # Windows startup script
│   └── .env.example               # Environment variables template
│
├── frontend/
│   ├── public/
│   │   └── index.html             # HTML template
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js       # Admin dashboard component
│   │   │   ├── AttendanceTable.js # Attendance table component
│   │   │   ├── UserRegistration.js # User registration form
│   │   │   └── FaceAuth.js        # Face authentication component
│   │   │
│   │   ├── pages/
│   │   │   └── Home.js            # Main page with tabs
│   │   │
│   │   ├── services/
│   │   │   └── api.js             # API client (axios)
│   │   │
│   │   ├── App.js                 # Root React component
│   │   ├── App.css                # App styles
│   │   ├── index.js               # React entry point
│   │   └── index.css              # Global styles
│   │
│   └── package.json               # Node.js dependencies
│
├── docker-compose.yml             # Docker Compose configuration
├── .gitignore                    # Git ignore rules
├── README.md                     # Comprehensive documentation
├── QUICKSTART.md                 # Quick start guide
└── PROJECT_STRUCTURE.md          # This file
```

## Key Components

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **face_recognition**: dlib-based face recognition library
- **OpenCV**: Image processing and computer vision
- **PostgreSQL**: Relational database

### Frontend
- **React**: UI framework
- **Axios**: HTTP client for API calls
- **Modern CSS**: Clean, responsive design

### Database
- **users**: Stores user information and face encodings
- **attendance**: Stores punch-in/punch-out records

## Data Flow

1. **Registration**: User uploads images → Face encoding → Store in database
2. **Authentication**: Capture image → Encode → Match against stored encodings → Return user
3. **Attendance**: Authenticate → Punch in/out → Store timestamp → Calculate duration
4. **Export**: Query attendance → Format as CSV → Download

## API Endpoints

- `/api/v1/auth/register` - User registration
- `/api/v1/auth/authenticate` - Face authentication
- `/api/v1/auth/punch` - Punch in/out
- `/api/v1/users/` - List users
- `/api/v1/attendance/` - List attendance
- `/api/v1/export/csv` - Export CSV
