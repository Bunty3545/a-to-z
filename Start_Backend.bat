@echo off
title Audit Telemetry Backend Server
echo ====================================================
echo  Starting Real-Time Audit Telemetry Backend...
echo  Node.js + Express + Socket.io (Port 4000)
echo ====================================================
echo.
cd /d "%~dp0backend"
node server.js
pause

