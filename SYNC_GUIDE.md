# 멀티 PC 동기화 가이드

## 운영 PC 현황

| PC | machine_id | workspace_root | 비고 |
|----|-----------|----------------|------|
| 사무실 데스크탑 | 사무실-데스크탑 | D:/업무/agents | 메인 PC (가장 오래 사용) |
| 노트북 | 노트북-삼성 | D:/work/agents | 이동 작업용 |
| 사무실 PC 2호 | (설정 필요) | (설정 필요) | 보조 PC |

---

## 핵심 원칙

- **단순 덮어쓰기 금지**: 한쪽 PC의 memory.md가 더 풍부할 수 있으므로 항상 내용을 **병합**
- **마지막 push가 최신**: 병합 완료 후에는 가장 최근 push 기준으로 운용
- **index.html 공유**: 모든 PC에서 동일한 HTML을 사용하며, 에이전트 상태를 공유 반영
- **작업 전 반드시 pull**: 새로운 작업 시작 전 항상 최신 상태를 받아온 후 시작

---

## 동기화 대상

| 대상 | 경로 | 설명 |
|------|------|------|
| 에이전트 memory | agents/*/memory.md | 에이전트 경험 데이터 |
| 에이전트 role | agents/*/role.md | 에이전트 역할 정의 |
| 에이전트 상태 | agent_status.json | 실시간 작업 상태 |
| Claude 설정 | claude-config/ | .claude/ 설정 동기화용 |
| CLAUDE.md | CLAUDE.md | 오케스트레이터 지시문 |
| 대시보드 | index.html | 에이전트 현황판 |
| 스크립트 | scripts/*.py | 유틸리티 스크립트 |

---

## 신규 PC 설정 절차

### Step 1. 사전 요구사항
```bash
# GitHub CLI 설치
winget install GitHub.cli
gh auth login

# Python 3.8+ 필요
python --version
```

### Step 2. 저장소 클론
```bash
cd "D:/업무/agents"  # 또는 원하는 경로
git clone https://github.com/your-github-username/agent.git .
```

### Step 3. 로컬 설정
```bash
cp config.example.json config.local.json
# config.local.json 열어서 이 PC의 실제 경로로 수정
# machine_id, workspace_root, data_root, output_root 설정
```

### Step 4. 검증
```bash
python scripts/detect_paths.py
# 머신 ID, 워크스페이스 경로 확인
```

### Step 5. Claude 설정 가져오기
```bash
python scripts/sync_claude_config.py import
# claude-config/ 내용을 로컬 .claude/에 적용
```

---

## 평상시 운용 절차

### 작업 시작 전 (반드시)
```bash
git pull origin master
```
-> 다른 PC에서 업데이트된 memory.md, role.md 자동 반영

### 작업 완료 후
```bash
git add agents/[해당 에이전트]/memory.md
git commit -m "update: [에이전트명] memory.md - [추가된 경험 요약]"
git push origin master
```

### 자동 동기화 (GitHub Actions)
- **매일 오전 9시 KST**: GitHub Actions가 자동으로 `.sync_status` 갱신
- **push 즉시**: Actions 실행 -> 다른 PC에서 pull 시 최신 상태 수신
- **수동 강제**: GitHub Actions 탭 -> "Run workflow"

---

## 기존 PC 경험 통합 절차

> **이 PC에서 이미 분석/개발 작업을 해왔고, 그 경험을 에이전트 시스템에 반영하고 싶을 때 사용.**
> 사용자가 "SYNC_GUIDE.md 보고 진행해줘"라고 하면 이 섹션을 따른다.

### Step 1. 최신 구조 수신

```bash
cd [이 PC의 workspace_root]   # config.local.json 참조
git pull origin master
```

이 단계에서 다른 PC가 업데이트한 role.md, memory.md, 양식 파일, 스크립트를 모두 수신한다.

### Step 2. 로컬 경험 확인

이 PC의 `.claude/memory/` 디렉토리를 검토하여, 에이전트 memory.md에 반영할 경험을 식별한다.

```bash
ls .claude/memory/          # 또는 해당 프로젝트의 .claude/ 경로
```

### Step 3. 경험 분배 (어떤 에이전트에 넣을지)

| 이 PC의 경험 유형 | 대상 에이전트 memory.md |
|------------------|----------------------|
| 민간데이터(KT/KB/KCB) 수집 경험 | `data-collector/memory.md` |
| 전처리 경험 (코드 통일, 보정, 결측 처리) | `data-cleaner/memory.md` |
| 전처리 솔루션/자동화 도구 개발 | `lead-data/memory.md` |
| 탐색적 분석 인사이트 | `eda-analyst/memory.md` |
| 통계 분석 경험 | `statistician/memory.md` |
| ML/DL 모델링 경험 | `ml-engineer/memory.md` 또는 `deep-learning/memory.md` |
| 공간 분석/지도 시각화 | `gis-specialist/memory.md` |
| 텍스트 마이닝 경험 | `text-analyst/memory.md` |
| 차트/시각화 노하우 | `visualizer/memory.md` |
| 보고서 작성 경험 | `reporter/memory.md` |
| 프로젝트 전체 운영 경험 | `orchestrator/memory.md` |
| 웹앱 개발 경험 | `lead-dev/memory.md` |
| PPTX 제작 경험 | `lead-pptx/memory.md` |

### Step 4. memory.md에 경험 추가

각 에이전트의 기존 memory.md를 **읽은 뒤**, 중복되지 않는 새 경험만 추가한다.

추가 형식:
```markdown
## [작업명/주제]
- 수행 내용: [간략 설명]
- 사용 데이터: [데이터 출처/형태]
- 효과적이었던 방법: [기법/접근법]
- 주의사항: [다음번에 피해야 할 것]
```

**주의:**
- 기존 내용 삭제 금지 (다른 PC의 경험이 이미 들어있음)
- 중복 내용은 추가하지 않음
- 한자/일본어 사용 절대 금지

### Step 5. 빌드 및 push

```bash
python scripts/build_all.py
git add agents/*/memory.md index.html scripts/md_content.json
git commit -m "sync: [이 PC 이름] 경험 통합 - [요약]"
git push origin master
```

### Step 6. (선택) Claude 설정 내보내기

이 PC의 `.claude/` 설정을 repo에도 반영하고 싶으면:

```bash
python scripts/sync_claude_config.py export
git add claude-config/
git commit -m "sync: [이 PC] Claude 설정 내보내기"
git push origin master
```

---

## 작업 영역 분리 권장

동시 작업 시 충돌을 줄이기 위해 PC별 주 담당 영역을 정한다:

| 영역 | 권장 담당 PC | 이유 |
|------|-------------|------|
| role.md (구조 변경) | 사무실 데스크탑 | 시스템 설계 기준 PC |
| memory.md (실무 경험) | 작업한 PC | 실제 경험이 있는 PC에서 작성 |
| index.html / metaverse.html | 노트북 | UI 작업 전담 |
| docs/analysis-templates/ | 사무실 데스크탑 | 양식 관리 기준 PC |
| scripts/*.py | 둘 다 가능 | 충돌 시 기능 단위로 병합 |

**동시에 같은 파일 수정이 예상되면**: 한쪽이 먼저 push → 다른 쪽이 pull 후 작업.

---

## 완전자동 동기화 설정

### watchdog 기반 자동 동기화
```bash
# watchdog 설치 (선택사항 - 없어도 폴링 모드로 동작)
pip install watchdog

# 자동 동기화 시작
python scripts/auto_sync.py

# 드라이런 (실제 git 명령 실행 안 함)
python scripts/auto_sync.py --dry-run

# pull 간격 변경 (기본 1800초 = 30분)
python scripts/auto_sync.py --interval 600
```

### Windows 작업 스케줄러 등록
1. `scripts/auto_sync.bat` 실행하여 테스트
2. 작업 스케줄러 -> 새 작업 만들기
   - 트리거: 로그인 시
   - 동작: `scripts/auto_sync.bat` 실행
   - 조건: 네트워크 사용 가능 시만

### 동작 방식
- 파일 변경 감지 -> 30초 디바운스 -> 자동 git add/commit/push
- 30분마다 자동 git pull (충돌 시 양쪽 보존)
- 감시 대상: agents/*/*.md, agent_status.json, claude-config/

---

## .claude 설정 동기화

### 내보내기 (현재 PC -> repo)
```bash
python scripts/sync_claude_config.py export
git add claude-config/
git commit -m "sync: Claude 설정 내보내기"
git push origin master
```

### 가져오기 (repo -> 현재 PC)
```bash
git pull origin master
python scripts/sync_claude_config.py import
```

### 동기화 대상
- `CLAUDE.md` - 전역 지시문
- `memory/*.md` - 프로젝트 memory 파일
- `skills/` - 커스텀 스킬

### 제외 대상
- `settings.json` - 머신별 설정
- API 키, 토큰 등 민감정보
- 서드파티 MCP 설정

---

## memory.md 업데이트 기준

에이전트 작업 완료 후 해당 에이전트의 memory.md에 추가할 내용:

```markdown
## [YYYY-MM-DD] [작업명]
- 수행 내용: [간략 설명]
- 사용 데이터: [데이터 출처/형태]
- 효과적이었던 방법: [기법/접근법]
- 주의사항: [다음번에 피해야 할 것]
- 재사용 가능 코드: [있다면 파일 경로]
```

---

## 초기 1회: 두 PC memory.md 병합 절차

### Step 1. 사무실 PC에서 push
```bash
cd [사무실 PC 에이전트 경로]
git add agents/*/memory.md
git commit -m "sync: 사무실 PC memory.md 업데이트"
git push origin master
```

### Step 2. 다른 PC에서 pull 후 병합
```bash
git pull origin master
```
충돌(conflict) 발생 시 -> 아래 병합 규칙 적용

### Step 3. memory.md 병합 규칙

| 상황 | 처리 방법 |
|------|---------|
| 양쪽에 같은 내용 | 하나만 유지 (중복 제거) |
| 한쪽에만 있는 경험 | 무조건 보존 (더 풍부한 쪽 우선) |
| 수치/날짜가 다른 경우 | 더 최신 정보 채택 |
| 방법론이 다른 경우 | 양쪽 모두 보존 (두 방법 모두 유효) |

### Step 4. 병합 완료 후 push
```bash
git add agents/*/memory.md
git commit -m "merge: 양 PC memory.md 통합 병합 완료"
git push origin master
```

---

## 충돌(Conflict) 발생 시 해결

```bash
# 충돌 파일 확인
git status

# 충돌 마커 확인 (<<<<<<< HEAD 부분)
# 수동으로 편집하여 두 내용 병합

# 병합 완료 후
git add [충돌파일]
git commit -m "merge: memory.md 충돌 해결"
git push origin master
```

**충돌 마커 처리 원칙:**
- `<<<<<<< HEAD`: 현재 PC의 내용
- `>>>>>>> origin/master`: 다른 PC의 내용
- -> **두 내용을 모두 보존**하여 병합 (삭제 금지)

---

## index.html 공유 — 대시보드 MD 에디터 동기화 필수

> **[중요] memory.md를 수정해도 대시보드에 자동 반영되지 않는다.**
> index.html에 MD 내용이 하드코딩되어 있으므로, 반드시 아래 빌드를 실행해야 한다.

### memory.md/role.md 수정 후 필수 절차

```bash
# 1. 빌드 스크립트 실행 (MD 파일 → index.html 자동 주입)
cd "D:/업무/agents"   # 또는 이 PC의 workspace_root
python scripts/build_md_content.py

# 2. 커밋 & 푸시
git add index.html scripts/md_content.json
git commit -m "sync: MD_CONTENT 에이전트 memory 반영"
git push origin master
```

### 확인 방법
대시보드 → "MD 에디터" 탭 → 에이전트 선택 → memory.md 탭
내용이 "(내용 없음)"이면 빌드 스크립트를 실행하지 않은 것이다.

### 구조 설명
- `agents/*/memory.md` — 실제 원본 파일 (Claude가 여기를 수정)
- `scripts/md_content.json` — 위 파일들을 JSON으로 묶은 캐시
- `index.html` 내 `const MD_CONTENT = {...}` — 대시보드가 읽는 하드코딩 값
- 3개가 항상 동기화되어야 한다. `build_md_content.py`가 이를 한 번에 처리한다.

---

## git remote URL 설정 (HTTPS 권장)

모든 PC에서 HTTPS를 사용해야 SSH 퍼미션 오류 없이 push가 가능하다.

```bash
# remote URL 확인
git remote -v

# git@github.com: 으로 시작하면 SSH -- 아래로 HTTPS 전환
git remote set-url origin https://github.com/your-github-username/agent.git
```

노트북 포함 모든 작업 PC에서 동일하게 적용할 것.

---

## 신규 PC / 노트북 시작 시 Claude 프롬프트

새 PC나 노트북에서 Claude Code를 열 때 아래를 붙여넣어 파악시켜라.

```
agents repo 작업 전 다음 사항을 먼저 파악해줘.

1. git remote이 HTTPS인지 확인:
     git remote -v
   git@github.com: 으로 시작하면 전환 필요:
     git remote set-url origin https://github.com/your-github-username/agent.git

2. SYNC_GUIDE.md 읽기 (워크플로우 변경사항 있음)

3. memory.md 수정 후 필수 절차 -- 대시보드에 반영 안 되면 이 하나를 놓친 것:
     python scripts/sync.py
   실행 후 커밋 & 푸시:
     git add index.html scripts/md_content.json && git commit && git push

4. 대시보드 확인: MD 에디터 탭 -> 에이전트 선택 -> memory.md 탭
   "(내용 없음)" 이면 위 스크립트를 실행하지 않은 것

## 현재 주요 프로젝트 상태 (2026-05-19 기준)

- 귀촌지 분석 (gnreturn): 6단계 완료, HTML 보고서 양식 교정 완료
  - gen_report.py: C:/Users/빅데이터(user)/gen_report.py (데스크 PC)
  - SDC placeholder IV-1, IV-2 진입 완료 (실지 방문 시 데이터 체우면 됨)
  - SDC 참고파일: D:/업무/02_분석과제/2026/분석_귀촌지/data/sdc/

- agents repo 스크립트 환경:
  - scripts/sync.py -- 노트북이 추가한 통합 sync (권장)
  - scripts/build_md_content.py -- 데스크 PC 개선 버전 (update_md_content.py도 동일 기능)
  - 통일 기준: scripts/sync.py 권장

작업 시작 전 반드시 git pull origin master 먼저.
```

---

## 금지 사항

- `git push --force` (강제 push 금지 - 다른 PC 작업 덮어쓰기 위험)
- 작업 전 pull 생략 (충돌 증가)
- memory.md 삭제 (경험 데이터 손실)
- config.local.json push (머신별 경로 정보 유출)
- 절대경로 하드코딩 (다중 PC 호환성 파괴)
