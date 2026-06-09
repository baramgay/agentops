@echo off
chcp 949 >nul
cd /d "%~dp0"
title Agent System

echo ============================================
echo   泲ͼ Ʈ ý
echo ============================================
echo.

echo [1/4] ȯ Ȯ ...
if not exist ".venv\Scripts\python.exe" goto setup_venv
goto check_api

:setup_venv
echo     ȯ   -  1ȸ...
python -m venv .venv
if errorlevel 1 goto err_python
.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if errorlevel 1 goto err_pip
echo     ȯ غ Ϸ.
goto check_api

:err_python
echo [] Python 3.9 ̻ ʿմϴ.
pause
exit /b 1

:err_pip
echo [] Ű ġ ߽ϴ.
pause
exit /b 1

:check_api
echo [2/4] API  Ȯ - Ʈ 8765...
netstat -ano 2>nul | findstr ":8765 " | findstr "LISTENING" >nul
if not errorlevel 1 goto api_running
echo     API   ...
start "Agent API 8765" /MIN .venv\Scripts\python.exe -m uvicorn scripts.api_server:app --port 8765 --workers 1 --log-level warning
timeout /t 3 /nobreak >nul
goto check_http
:api_running
echo     ̹  .

:check_http
echo [3/4] HTTP  Ȯ - Ʈ 8000...
netstat -ano 2>nul | findstr ":8000 " | findstr "LISTENING" >nul
if not errorlevel 1 goto http_running
echo     HTTP   ...
start "Agent HTTP 8000" /MIN python -m http.server 8000
timeout /t 2 /nobreak >nul
goto open_browser
:http_running
echo     ̹  .

:open_browser
echo [4/4]  ...
timeout /t 1 /nobreak >nul
start "" "http://localhost:8000/index.html"

echo.
echo   ú : http://localhost:8000/index.html
echo   Ÿ : http://localhost:8000/metaverse.html
echo   API  : http://localhost:8765/api/health
echo.
echo     ּȭ â  ˴ϴ.
echo.
pause
