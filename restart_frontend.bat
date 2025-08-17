@echo off
echo Restarting Frontend with Fixed Configuration...
echo.

cd frontend

echo Stopping any running React server...
taskkill /f /im node.exe 2>nul

echo.
echo Starting React development server...
npm start

pause