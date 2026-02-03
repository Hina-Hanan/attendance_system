#!/bin/bash

# Start script for backend
echo "Starting Face Attendance System Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
