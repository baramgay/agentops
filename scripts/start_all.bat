@echo off
chcp 65001 >nul
title Your Organization 에이전트 시스템 — 전체 서버 기동
cd /d "%~dp0.."

echo ============================================
echo  Your Organization 에이전트 시스템 기동
echo ============================================
echo.

:: ── 포트 충돌 감지 ─────────────────────────────────────
echo [사전 확인] 포트 사용 여부 확인 중...
netstat -ano 2>nul | findstr ":8000 " | findstr "LISTENING" >nul
if %ERRORLEVEL% == 0 (
    echo [경고] 포트 8000이 이미 사용 중입니다.
    echo        기존 프로세스를 종료하거나 다른 포트를 사용하세요.
    echo.
)
netstat -ano 2>nul | findstr ":8765 " | findstr "LISTENING" >nul
if %ERRORLEVEL% == 0 (
    echo [경고] 포트 8765가 이미 사용 중입니다.
    echo        기존 프로세스를 종료하거나 다른 포트를 사용하세요.
    echo.
)

:: ── 가상환경 확인 ───────────────────────────────────────
if not exist ".venv\Scripts\python.exe" (
    echo [경고] .venv 가상환경이 없습니다.
    echo        python -m venv .venv 후 pip install -r scripts\requirements.txt 실행 필요
    echo.
)

echo [1/2] HTTP 서버 시작 (포트 8000)...
start "HTTP :8000" cmd /k "chcp 65001 >nul && title HTTP 서버 :8000 && cd /d %~dp0.. && python -m http.server 8000 && pause"

timeout /t 1 /nobreak >nul

echo [2/2] FastAPI API 서버 시작 (포트 8765)...
start "API :8765" cmd /k "chcp 65001 >nul && title FastAPI :8765 && cd /d %~dp0.. && .venv\Scripts\python.exe scripts\api_server.py && pause"

:: ── 서버 기동 대기 후 브라우저 열기 ────────────────────
echo.
echo 서버 기동 완료!
echo   HTTP  : http://localhost:8000
echo   API   : http://localhost:8765
echo   대시보드: http://localhost:8000/index.html
echo   메타버스: http://localhost:8000/metaverse.html
echo.
timeout /t 2 /nobreak >nul
echo 브라우저를 자동으로 열겠습니다...
start "" "http://localhost:8000/index.html"
echo.
echo 이 창을 닫아도 서버는 계속 실행됩니다.
echo.
pause
