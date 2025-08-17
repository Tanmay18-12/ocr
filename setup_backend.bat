@echo off
echo Setting up Flask Backend...
echo.

cd backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Backend setup complete!
echo.
echo To start the backend:
echo   cd backend
echo   venv\Scripts\activate
echo   python app.py
echo.
pause