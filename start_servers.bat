@echo off
echo Starting Traceable Media Verification System...

start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo Servers started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
pause
