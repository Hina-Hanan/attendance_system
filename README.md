# Face Authentication Attendance System

A production-ready face authentication based attendance system with punch-in/punch-out functionality, admin dashboard, database storage, CSV export, and basic spoof prevention.

## 🎯 Features

- **User Registration**: Register users with 3-4 face images from different angles
- **Face Authentication**: Real-time face recognition using webcam
- **Attendance Management**: Punch-in and punch-out with automatic duration calculation
- **Spoof Prevention**: Basic liveness detection using head movement and blink detection
- **Admin Dashboard**: View total users, live attendance, and export data
- **CSV Export**: Download attendance records as CSV files
- **PostgreSQL Database**: Robust data storage with SQLAlchemy ORM

## 🏗️ System Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Face Recognition**: face_recognition library (dlib-based)
- **Image Processing**: OpenCV
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API**: RESTful API with automatic OpenAPI documentation

### Frontend
- **Framework**: React
- **HTTP Client**: Axios
- **UI**: Clean, minimal design with responsive layout

### Database Schema

#### Users Table
- `user_id` (UUID, Primary Key)
- `username` (String, Unique)
- `face_encodings` (Array of JSON strings - stores 128-dimensional face encodings)
- `created_at` (Timestamp)

#### Attendance Table
- `attendance_id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key)
- `punch_in_time` (Timestamp)
- `punch_out_time` (Timestamp)
- `total_duration` (String, format: HH:MM:SS)
- `date` (String, format: YYYY-MM-DD)
- `created_at` (Timestamp)

## 🔬 Face Recognition Model

### Model Used
The system uses the **face_recognition** library, which is built on top of **dlib's face recognition model**. This model:

- Uses HOG (Histogram of Oriented Gradients) for face detection
- Uses a deep learning model trained on millions of faces for encoding
- Generates 128-dimensional face encodings
- Provides high accuracy for face matching

### Encoding Process

1. **Image Preprocessing**:
   - Convert image to RGB format
   - Apply grayscale normalization
   - Apply histogram equalization for lighting variations

2. **Face Detection**:
   - Detect face locations in the image
   - Extract the first detected face (if multiple faces present)

3. **Encoding Generation**:
   - Generate 128-dimensional face encoding vector
   - Store encoding as JSON string in database

4. **Matching**:
   - Compare input face encoding with stored encodings
   - Calculate Euclidean distance
   - Match if distance is below threshold (default: 0.6)

### Training / Encoding Process

The system does **not require training**. The face_recognition library uses a pre-trained model. However, during registration:

1. User uploads 3-4 face images from different angles
2. Each image is processed and encoded
3. All encodings are stored for that user
4. During authentication, the system matches against all stored encodings

**Why multiple images?**
- Captures different angles and lighting conditions
- Improves matching accuracy
- Handles variations in facial expressions

## 🛡️ Spoof Prevention Logic

The system implements basic spoof prevention using:

### 1. Multiple Frame Verification
- Requires multiple video frames before authentication
- Prevents static image attacks
- Configurable via `SPOOF_CHECK_FRAMES` (default: 5 frames)

### 2. Head Movement Detection
- Tracks face position across frames
- Detects head movement (left/right/up/down)
- Requires minimum movement threshold (default: 0.1 normalized)
- Rejects static images that don't show movement

### 3. Eye Blink Detection (Simplified)
- Uses Haar Cascade classifier to detect eyes
- Analyzes eye region intensity
- Detects open/closed eye states
- Can be enhanced with dlib facial landmarks in production

### Limitations
- Current implementation is basic and suitable for low-security environments
- For production use, consider:
  - 3D face depth analysis
  - Advanced liveness detection (e.g., MediaPipe, TensorFlow Lite)
  - Challenge-response mechanisms
  - Anti-spoofing neural networks

## 📊 Accuracy Expectations

### Matching Accuracy
- **True Positive Rate**: ~95-98% under good lighting conditions
- **False Positive Rate**: <1% with threshold 0.6
- **Best Performance**: Well-lit environments, front-facing faces
- **Challenges**: 
  - Poor lighting conditions
  - Extreme angles (>45 degrees)
  - Significant appearance changes (glasses, beard, makeup)
  - Low-resolution images

### Known Failure Cases

1. **Lighting Issues**:
   - Very dark or very bright environments
   - Backlit faces
   - Uneven lighting

2. **Angle Variations**:
   - Faces turned >45 degrees
   - Extreme up/down angles

3. **Appearance Changes**:
   - New glasses or removal of glasses
   - Significant facial hair changes
   - Heavy makeup

4. **Image Quality**:
   - Blurry images
   - Low resolution (<100x100 pixels)
   - Motion blur

5. **Multiple Faces**:
   - System uses first detected face
   - May fail if wrong face is selected

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or use Docker)
- Webcam (for face authentication)

### Local Development Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd attendance
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional)
# Create .env file:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/attendance_db
```

#### 3. Database Setup

**Option A: Using Docker (Recommended)**

```bash
docker-compose up -d db
```

**Option B: Local PostgreSQL**

```bash
# Create database
createdb attendance_db

# Or using psql:
psql -U postgres
CREATE DATABASE attendance_db;
```

#### 4. Run Backend

```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

#### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will be available at: `http://localhost:3000`

### Using Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000 (if configured)
# Database: localhost:5432
```

## 📡 API Endpoints

### Authentication & Registration

- `POST /api/v1/auth/register` - Register new user with face images
  - Form data: `username` (string), `files` (3-4 image files)
  
- `POST /api/v1/auth/authenticate` - Authenticate face
  - Form data: `file` (image file)
  - Returns: user info and confidence score

- `POST /api/v1/auth/punch` - Punch in/out
  - Body: `{"user_id": "uuid", "action": "punch_in" | "punch_out"}`

### Users

- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{user_id}` - Get specific user
- `GET /api/v1/users/count/total` - Get total user count

### Attendance

- `GET /api/v1/attendance/` - Get all attendance records
- `GET /api/v1/attendance/today` - Get today's attendance
- `GET /api/v1/attendance/user/{user_id}` - Get user's attendance

### Export

- `GET /api/v1/export/csv` - Export attendance as CSV
  - Query params: `start_date`, `end_date` (optional, format: YYYY-MM-DD)

## 🚢 Deployment

### Render / Railway / EC2 Deployment

#### Backend Deployment

1. **Set Environment Variables**:
   ```
   DATABASE_URL=<your-postgresql-connection-string>
   SECRET_KEY=<your-secret-key>
   CORS_ORIGINS=["https://your-frontend-domain.com"]
   ```

2. **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Command**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Requirements**:
   - Python 3.11 runtime
   - PostgreSQL addon/service
   - Buildpacks may need system dependencies (dlib, cmake)

#### Frontend Deployment

1. **Set Environment Variables**:
   ```
   REACT_APP_API_URL=https://your-backend-api.com/api/v1
   ```

2. **Build**:
   ```bash
   npm run build
   ```

3. **Serve**:
   - Use static hosting (Vercel, Netlify, S3 + CloudFront)
   - Or serve `build/` directory with nginx/apache

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Considerations

1. **Security**:
   - Change `SECRET_KEY` in production
   - Use HTTPS for all connections
   - Implement rate limiting
   - Add authentication/authorization for admin endpoints

2. **Performance**:
   - Use connection pooling for database
   - Implement caching for frequently accessed data
   - Consider CDN for frontend assets

3. **Monitoring**:
   - Add logging (e.g., Python logging, Sentry)
   - Monitor API response times
   - Track authentication success/failure rates

4. **Database**:
   - Regular backups
   - Index optimization
   - Connection pool tuning

## 🧪 Testing

### Sample API Requests

#### Register User (using curl)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -F "username=john_doe" \
  -F "files=@face1.jpg" \
  -F "files=@face2.jpg" \
  -F "files=@face3.jpg"
```

#### Authenticate Face

```bash
curl -X POST "http://localhost:8000/api/v1/auth/authenticate" \
  -F "file=@test_face.jpg"
```

#### Punch In

```bash
curl -X POST "http://localhost:8000/api/v1/auth/punch" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "uuid-here", "action": "punch_in"}'
```

## 📝 Configuration

Edit `backend/app/config.py` or use environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `FACE_MATCH_THRESHOLD`: Face matching threshold (lower = stricter)
- `MIN_FACE_IMAGES_REQUIRED`: Minimum images for registration (default: 3)
- `MAX_FACE_IMAGES_REQUIRED`: Maximum images for registration (default: 4)
- `SPOOF_CHECK_FRAMES`: Number of frames for spoof detection (default: 5)
- `CORS_ORIGINS`: Allowed CORS origins

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🐛 Troubleshooting

### Common Issues

1. **dlib installation fails (especially on Windows)**:
   - **Windows**: See [backend/WINDOWS_SETUP.md](backend/WINDOWS_SETUP.md). You need **CMake** (add to PATH) and **Visual Studio Build Tools** with "Desktop development with C++", then run `pip install -r requirements.txt` again.
   - **Linux/Mac**: Install cmake and build tools (`apt install cmake` / `brew install cmake`).
   - **Alternative**: Use Conda: `conda install -c conda-forge dlib`, then `pip install -r requirements.txt`.

2. **Camera not working**:
   - Check browser permissions
   - Use HTTPS for production (required for camera access)

3. **Database connection errors**:
   - Verify PostgreSQL is running
   - Check connection string format
   - Ensure database exists

4. **Face not detected**:
   - Ensure good lighting
   - Face should be front-facing
   - Check image quality

## 📞 Support

For issues and questions, please open an issue on the repository.

---

**Built with ❤️ using FastAPI, React, and face_recognition**
