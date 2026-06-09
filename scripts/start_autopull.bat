@echo off
REM 로그인 시 자동 git pull — 다중 PC 동기화용
cd /d AGENTS_HOME
git pull origin master --no-rebase --quiet
if %errorlevel% equ 0 (
    python scripts\build_html.py --quiet 2>nul
    echo [autopull] %date% %time% - pull 완료 >> logs\autopull.log
) else (
    echo [autopull] %date% %time% - pull 실패 >> logs\autopull.log
)
