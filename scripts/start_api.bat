@echo off
cd /d AGENTS_HOME
pip install fastapi uvicorn websockets --quiet

REM 오늘 보고서 알림 (백그라운드)
start /min "" python scripts\notify_report.py

REM FastAPI WebSocket 서버 시작
python scripts\api_server.py
pause
