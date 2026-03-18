#!/bin/bash
echo "🚀 Starting P2P Exception System"
python scripts/seed.py
uvicorn api.app:app --port 8000 --reload &
sleep 2
cd frontend && npm install --silent && npm start &
echo "✅ Frontend: http://localhost:3000 | API: http://localhost:8000"
trap "kill 0" INT
wait