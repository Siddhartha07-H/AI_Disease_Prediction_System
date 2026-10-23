@echo off
title HealthAI - Server Launcher
color 0A

echo ====================================================================
echo        HealthAI - Disease Prediction System Launcher
echo ====================================================================
echo.
echo Choose how you want to run the website:
echo.
echo  [1] Open on ALL Devices on Same Wi-Fi (Phones, Laptops, Tablets)
echo  [2] Create a FREE Worldwide Public Link (Open on ANY Device Anywhere)
echo  [3] Run on Local PC only (127.0.0.1:8000)
echo.
set /p choice="Enter your choice (1, 2, or 3): "

if "%choice%"=="1" goto wifi
if "%choice%"=="2" goto public
if "%choice%"=="3" goto local
goto wifi

:wifi
echo.
echo --------------------------------------------------------------------
echo Starting server for your Local Network (Wi-Fi)...
echo --------------------------------------------------------------------
for /f "tokens=4" %%a in ('route print^|find " 0.0.0.0"') do (
    set LOCAL_IP=%%a
    goto ip_found
)
:ip_found
echo.
echo [SUCCESS] Your server is accessible on any device on the same Wi-Fi at:
echo           http://%LOCAL_IP%:8000
echo.
echo Press Ctrl+C in this window anytime to stop the server.
echo.
.\.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
goto end

:public
echo.
echo --------------------------------------------------------------------
echo Starting server and creating a Worldwide Public HTTPS Link...
echo --------------------------------------------------------------------
start "HealthAI Backend" cmd /k ".\.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo Waiting for backend to start...
timeout /t 3 >nul
echo.
echo Launching public tunnel (Pinggy / Localhost.run)...
echo Copy the HTTPS link displayed below and open it on ANY phone or computer!
echo.
ssh -p 443 -R0:localhost:8000 a.pinggy.io
goto end

:local
echo.
echo Starting local server on http://127.0.0.1:8000 ...
.\.venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
goto end

:end
pause
