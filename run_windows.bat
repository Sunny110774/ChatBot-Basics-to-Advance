@echo off
cd /d "%~dp0"

rem Find Python: try "python", then the "py" launcher that python.org installs
set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
  echo.
  echo Python is not installed on this computer.
  echo 1. Download Python 3.10 or newer from https://www.python.org/downloads/
  echo 2. On the first installer screen, tick "Add python.exe to PATH".
  echo 3. Close this window and double-click run_windows.bat again.
  echo Your key and workspace settings are already saved and will be reused.
  echo.
  pause
  exit /b 1
)

if exist ".env" goto run
echo First-time setup. Your settings are saved in a local .env file in this folder.
set /p KEY=Paste your Anthropic API key: 
set /p WS=Workspace ID starting wrkspc_ (press Enter to skip): 
(
  echo ANTHROPIC_API_KEY=%KEY%
  echo ANTHROPIC_WORKSPACE_ID=%WS%
  echo ANTHROPIC_MODEL=claude-sonnet-5-5
) > .env
:run

echo Installing or checking packages, please wait...
%PY% -m pip install -q -r requirements.txt
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000"
%PY% -m uvicorn app:app
pause
