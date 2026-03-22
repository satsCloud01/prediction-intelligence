#!/bin/bash
echo "Starting PredictionIntelligence..."

# Backend (port 8008)
cd "$(dirname "$0")/backend"
PYTHONPATH=src .venv/bin/uvicorn predictor.main:app --reload --port 8031 &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID) at http://localhost:8031"

# Frontend (port 5180)
cd "../frontend"
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID) at http://localhost:5180"

echo ""
echo "PredictionIntelligence is running!"
echo "  Frontend : http://localhost:5180"
echo "  API Docs : http://localhost:8031/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
