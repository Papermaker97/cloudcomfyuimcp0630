@echo off
chcp 65001 >nul
if "%~1"=="" (
  echo Drag the draft folder ^(repurpose^) onto this file, or run: upload.bat "folder path"
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0upload.ps1" -Folder "%~1"
pause
