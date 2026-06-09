---
name: reference-opendataloader-pdf
domain: 공공데이터소스
description: 대용량/복잡 PDF를 마크다운으로 고품질 변환하는 OpenDataLoaderPDF 설치·사용법
metadata: 
  node_type: memory
  type: reference
  originSessionId: 861f0f05-2bd9-4e05-be34-5db1c4e80be0
---

대용량·복잡 레이아웃 PDF를 마크다운/JSON으로 잘 변환하는 도구. 2026-06-02 설치 완료.

**설치된 환경:**
- 포터블 JRE: `C:\Users\username\tools\jdk-21.0.11+10-jre` (Temurin 21, 관리자권한 불필요. java가 PATH에 없을 때 사용)
- pip 패키지: `opendataloader-pdf` (Python 3.10+ 필요, 현재 3.14.5). Java 11+ 필수.

**사용법:**
```powershell
$env:JAVA_HOME = "C:\Users\username\tools\jdk-21.0.11+10-jre"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
python -c "import opendataloader_pdf; opendataloader_pdf.convert(input_path=[r'IN.pdf'], output_dir=r'OUT', format='markdown')"
```
출력: `OUT\<원본명>.md` + 추출 이미지들. (각 convert가 JVM 띄우므로 배치 권장)

**Java 미설치 시 포터블 재설치:** Adoptium API `https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse` 다운→Expand-Archive.

관련: [[reference-gaming-guideline]] (변환해 둔 가명정보 가이드라인)
