@echo off
python scripts/seed.py
start "API" cmd /k "uvicorn api.app:app --port 8000 --reload"
timeout /t 3
start "Frontend" cmd /k "cd frontend && npm install && npm start"
echo Frontend: http://localhost:3000 API: http://localhost:8000