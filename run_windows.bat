@echo off
cd /d "%~dp0"

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

python -m pip install -q -r requirements.txt
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8000"
python -m uvicorn app:app --reload
pause
