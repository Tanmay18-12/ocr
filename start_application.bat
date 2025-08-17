@echo off
echo Starting Document Processing Application...
echo.

echo Starting Backend Server...
start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && python app.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting Frontend Development Server...
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo Application is starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window...
pause > nul