@echo off
echo Starting Backend Server...
cd backend
call backend_env\Scripts\activate
python app.py
pause