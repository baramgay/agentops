---
type: method
domain: devops
updated: 2026-06-08
---

# CMD 배치파일 인코딩 규칙 (Korean Windows)

## 결론

한국어 Windows에서 .bat 파일은 **CP949 + CRLF** 조합으로 저장해야 CMD가 오류 없이 파싱한다.
Write 도구(UTF-8 LF)나 VSCode(UTF-8 BOM) 기본 저장으로는 파싱 오류 발생.

## 이유

- CMD.exe는 .bat 파일을 시스템 코드 페이지(Korean Windows = CP949)로 읽는다
- `chcp 65001`은 콘솔 I/O 코드 페이지만 바꾸고 파일 파싱 방식은 안 바뀐다
- UTF-8 한글 3바이트 시퀀스를 CP949로 읽으면 바이트 정렬이 깨져 이후 ASCII 명령어도 손상됨
  - `echo` → `'ho'` (앞 2바이트 CP949 문자로 소비)
  - `set PYTHON=` → `'THON'` (PY 손실)
  - `REM` 주석 한글이 실행 흐름에 유입
- LF-only 줄끝도 `do was unexpected at this time` 오류 유발 가능

## 적용법

```powershell
# 올바른 저장 방법: CP949 + CRLF
$lines = @('line1', 'line2', ...)
$crlfContent = [string]::Join("`r`n", $lines) + "`r`n"
$enc = [System.Text.Encoding]::GetEncoding(949)
[System.IO.File]::WriteAllBytes("path\to\file.bat", $enc.GetBytes($crlfContent))
```

## 금지 패턴

- Write 도구로 .bat 직접 저장 (UTF-8 LF)
- `Set-Content -Encoding OEM` (PowerShell here-string이 LF만 포함할 수 있음)
- .bat 파일 내 한글 REM 주석, 한글 echo, 한글 title — 안전하려면 전부 ASCII로
- `chcp 65001` + 한글 혼용 믿기 금지
