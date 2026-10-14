@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv
.venv\Scripts\python.exe -c "import ultralytics, PIL, numpy" 2>nul
if errorlevel 1 .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
if not exist frontend\dist\index.html (
  call npm --prefix frontend install
  call npm --prefix frontend run build
)
.venv\Scripts\python.exe server.py %*
