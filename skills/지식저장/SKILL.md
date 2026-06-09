---
name: "지식저장"
description: "컨텍스트 압축 전 또는 작업 체크포인트에서, 이번 대화의 프로젝트별 중요 지식(결정·해결책·함정·패턴)을 옵시디언 위키에 증류해 저장. log/status와 별개의 고품질 지식 보존. Use when the user wants to save important knowledge before compaction, checkpoint project learnings, or says 지식저장/지식 정리/압축 전 저장."
user-invocable: true
argument-hint: "[프로젝트명 (생략 시 이번 대화에서 다룬 전체)]"
---

# 지식저장 — 프로젝트별 핵심 지식 증류 → 위키

컨텍스트가 압축되면 세부 맥락이 사라진다. 압축 전(또는 의미 있는 작업 마무리 시)
이번 대화에서 얻은 **재사용 가능한 지식**을 옵시디언 위키에 증류해 영구 보존한다.
기계적 log/status(session_capture)와 달리, 이건 **모델이 직접 판단해 증류**하는 고품질 층이다.

## 위키 위치
- Vault: `{AGENTS_ROOT}/wiki` (예: `AGENTS_HOME\wiki`)
- 도메인 지도: `wiki/MoC/<도메인>.md`
- 원자적 노트: `wiki/notes/<슬러그>.md`
- 헬퍼: `wiki/_tools/wiki_write.py` (create/append/link), `wiki_read.py` (조회)

## 실행 절차

### 1. 대상 식별
- 이번 대화에서 **실제로 작업한 프로젝트**를 추린다 (인자로 지정되면 그것만).
  도메인 예: 경남부동산 · 이음지도 · 합성데이터스튜디오 · 누리스탯 · agents시스템 · 공공데이터소스

### 2. "저장할 가치가 있는 것"만 선별 (핵심)
저장 대상 ✅:
- 해결한 **버그와 원인·해결법** (재발 방지 가치)
- 내린 **설계 결정과 이유** (나중에 "왜 이렇게 했지" 답)
- 발견한 **함정·제약·전제** (예: 코드38 필터, cp949 가드)
- 재사용할 **방법·패턴·명령어**
- 데이터 출처·경로·기준값

저장 안 함 ❌: 단순 작업 경과, 파일 나열, 일상적 진행(이건 session_capture가 이미 함)

### 3. 증류 원칙
- 원문 덤프 금지. **"결론 · 이유 · 적용법" 3요소**로 압축.
- 한자·일본어 금지(순수 한글).

### 4. 기존 노트와 병합 (중복 방지)
- 먼저 `wiki_read.py <도메인>`으로 관련 MoC·노트 확인.
- **이미 있으면 해당 노트 update**(append), 없으면 새 원자적 노트 생성 후 MoC에 링크.
- `python wiki/_tools/wiki_write.py append <슬러그> "<증류 내용>"`
- `python wiki/_tools/wiki_write.py create <슬러그> <type> <도메인> "<제목>" "<본문>"`
  (type: feedback|project|reference|method|decision)
- `python wiki/_tools/wiki_write.py link <도메인> <슬러그> "<설명>"`

### 5. 보고
- 저장/갱신한 노트 목록을 사용자에게 요약 보고.

## 주의
- **agents 시스템 필수**: 작업이므로 update_status 선언(orchestrator→리드→담당) 후 진행.
- 위키 파일은 SessionEnd 훅이 자동 git push하므로 별도 push 불필요.
- 토큰: 이 작업은 현재 세션 예산 내에서 수행(별도 API 호출 없음).
