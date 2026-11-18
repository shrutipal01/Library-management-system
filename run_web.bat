@echo off
title Library Management System - Web Edition
cls
echo ========================================================
echo   Launching Library Management System (Web Application)
echo ========================================================
echo.
echo Starting Backend API Server (Port 5000)...
start "LMS Backend" cmd /k "cd /d %~dp0backend && node --experimental-sqlite app.js"

echo Starting Frontend Dev Server (Port 5173)...
start "LMS Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo   Web Application is running!
echo   Frontend URL: http://localhost:5173
echo   Backend API:  http://localhost:5000/api
echo ========================================================
echo Opening your web browser in 3 seconds...
timeout /t 3 >nul
start http://localhost:5173
