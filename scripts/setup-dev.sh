#!/bin/bash
# Development setup script

set -e

echo "Setting up Internal File Sharing System for development..."

# Backend setup
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Backend setup complete!"

# Frontend setup
cd ../frontend

echo ""
echo "Setting up frontend..."

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

echo "Frontend setup complete!"

cd ..

echo ""
echo "Development setup complete!"
echo ""
echo "To run the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "To run the frontend:"
echo "  cd frontend"
echo "  npm run dev"
