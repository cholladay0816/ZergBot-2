@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create the project virtual environment first. See README.md.
  exit /b 1
)
".venv\Scripts\python.exe" -m zergbot %*
