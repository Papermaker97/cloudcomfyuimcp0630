@echo off
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-login.ps1"
pause
