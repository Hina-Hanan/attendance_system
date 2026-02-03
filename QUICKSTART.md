# Quick Start Guide

## Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Docker)

## Quick Setup (5 minutes)

### 1. Start Database (Docker)
```bash
docker-compose up -d db
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs on: http://localhost:8000
API Docs: http://localhost:8000/docs

### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```

Frontend runs on: http://localhost:3000

## Using Docker Compose (All Services)
```bash
docker-compose up
```

## First Steps

1. **Register a User**:
   - Go to "Register User" tab
   - Enter username
   - Upload 3-4 face images from different angles
   - Click "Register User"

2. **Authenticate & Punch In**:
   - Go to "Face Auth" tab
   - Click "Start Camera"
   - Click "Capture Image"
   - Click "Authenticate Face"
   - Click "Punch In"

3. **View Dashboard**:
   - See total users and today's attendance
   - Export CSV for records

## Troubleshooting

- **dlib installation fails**: Use conda or install cmake
- **Camera not working**: Check browser permissions
- **Database errors**: Ensure PostgreSQL is running

See README.md for detailed documentation.
