#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p "../logs"

# Kill any processes already running on ports 8000 and 3000
lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || true

echo "Starting the backend server..."
echo "Open a new terminal and run:"
echo "cd $(pwd)/backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Starting the frontend server..."
echo "Open a new terminal and run:"
echo "cd $(pwd)/frontend && npm start"
echo ""
echo "Once started, access the application at:"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
