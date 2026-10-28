@echo off
setlocal
cd /d "%~dp0"
title Personal Expense Tracker

echo ==========================================
echo   Personal Expense Tracker - Website
echo ==========================================
echo.
echo Installing required packages...
where py >nul 2>nul
if %errorlevel%==0 (
    py -m pip install -r requirements.txt
    if errorlevel 1 goto install_error
    echo.
    echo Starting website at http://127.0.0.1:5000
    start "" http://127.0.0.1:5000
    py app.py
) else (
    where python >nul 2>nul
    if errorlevel 1 goto python_error
    python -m pip install -r requirements.txt
    if errorlevel 1 goto install_error
    echo.
    echo Starting website at http://127.0.0.1:5000
    start "" http://127.0.0.1:5000
    python app.py
)
echo.
echo The website has stopped. Press any key to close this window.
pause >nul
goto end

:python_error
echo Python was not found. Install Python 3.10 or newer and select Add Python to PATH.
pause
goto end

:install_error
echo Package installation failed. Check your internet connection and Python installation.
pause
:end
endlocal
