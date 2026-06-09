@echo off
title Agent Auto Sync
cd /d "%~dp0.."
echo [Agent Auto Sync] 시작...
echo 종료하려면 Ctrl+C를 누르세요.
echo.
python scripts/auto_sync.py %*
pause
