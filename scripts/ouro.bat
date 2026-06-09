@echo off
REM OUROBOROS 래퍼 — 한글 Windows 환경 (CP949) 인코딩 오류 방지
set NO_COLOR=1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
ouroboros %*
