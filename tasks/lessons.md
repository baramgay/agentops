# lessons.md

> AGENTS.md "Self-Improvement Loop" 규칙에 따른 패턴 기록
> 작성일: 2026-05-19

---

## 패턴 1: 사용자가 "진행과정을 md로 상세히 작성해줘"라고 요청하는 이유

### 상황
- 여러 파일(metaverse.html, api_server.py, 열기.bat)을 동시에 수정함
- 수정 후 변경 이력 문서가 부족했음
- 사용자가 추후 Claude Code로 작업 시 문제가 생길 수 있다고 지적함

### 교훈
- **모든 다중 파일 수정 후에는 반드시 CHANGELOG.md를 작성하라**
- 변경 전/후 코드를 line 번호와 함께 명시
- 각 파일의 역할, 변경 이유, 영향 범위를 기술
- 추후 Claude Code가 작업할 때 참고할 수 있도록 작성

### 실행 규칙
1. 3개 이상 파일을 수정하면 `docs/CHANGELOG_YYYYMMDD.md` 작성
2. 코드 변경 블록은 `파일:시작줄-끝줄` 형식으로 명시
3. API 엔드포인트 변경 시 명세 포함
4. JavaScript 함수 변경 시 호출 관계도 포함
5. `tasks/lessons.md`에 패턴 기록

---

## 패턴 2: file:// 프로토콜에서 파일시스템 쓰기 금지

### 상황
- metaverse.html을 `file://`로 열 때 `agent_status.json`에 직접 쓸 수 없음
- 브라우저 보안 정책상 로컬 파일 쓰기가 차단됨

### 교훈
- **브라우저에서 파일시스템에 쓰려면 반드시 HTTP 서버 + API 서버 구조를 사용하라**
- 정적 서버(port 8000)는 읽기 전용
- API 서버(port 8765)는 쓰기 담당
- CORS 설정을 `allow_origins=["*"]`로 허용

### 실행 규칙
1. 브라우저 기반 앱에서 상태 저장이 필요하면 FastAPI/Flask API 서버 분리
2. `열기.bat`에 API 서버 자동 시작 로직 포함
3. 오프라인 대응을 위해 localStorage에 먼저 쓰고, API는 비동기 sync

---

## 패턴 3: metaverse.html instruction panel 원본 기능 유지

### 상황
- 기존 instruction panel은 localStorage 저장만 하는 "기능"이었음
- 이를 실제로 실행하는 기능으로 변경하면서 원본 기능(localStorage persistence)을 보존해야 함

### 교훈
- **레거시 기능을 대체할 때는 원본 코드를 주석으로 표시하고, 기존 기능은 그대로 유지하라**
- `// 1. localStorage 저장 (기존 기능 유지)` 형태로 단계 구분
- 기존에 `localStorage`에 저장하던 코드는 그대로 두고, 아래에 실행 로직 추가

### 실행 규칙
1. 기존 기능 대체 시 원본 코드 라인 번호 주석
2. 새 기능은 새로운 단계 번호로 구분
3. 기존 localStorage key 형식(`agent_chat_${id}`) 유지

---

## 패턴 4: agent_status.json 동시 접근(race condition)

### 상황
- `fetchStatus()`가 3초마다 `agent_status.json`을 읽음
- API 서버(`POST /api/instruct`)가 같은 파일을 씀
- 파일 잠금(file locking)이 구현되지 않음

### 교훈
- **단일 JSON 파일을 여러 프로세스가 읽고 쓰면 데이터 손상 위험이 있다**
- FastAPI 단일 프로세스면 낮은 확률이지만, uvicorn 워커가 여러 개면 위험
- DB(SQLite)로 교체하거나, 파일 기반 잠금(flock) 필요

### 실행 규칙
1. 단순 JSON 파일 기반 상태 저장은 개발/데모용으로만 사용
2. 프로덕션에서는 SQLite + SQLAlchemy 사용
3. file locking이 필요하면 `portalocker` 또는 `fcntl` 사용

---

## 패턴 5: 한글 키워드 분석의 정확성

### 상황
- 사용자 지시를 한글 키워드로 분석하여 에이전트 행동 결정
- 키워드 중복("복귀"와 "돌아가" 모두 return) 처리
- if/elif 체인 순서가 중요함

### 교훈
- **한글 키워드 매핑은 명확한 우선순위를 가진 if/elif 체인으로 구현하라**
- 키워드 목록은 배열로 정의하여 관리 (`['복귀','돌아가','데스크','자리']`)
- `.some(k => lower.includes(k))` 패턴 사용
- 프론트엔드와 백엔드의 키워드 목록은 반드시 동기화

### 실행 규칙
1. 키워드 분석 로직은 프론트/백 모두 동일한 순서로 유지
2. 새 키워드 추가 시 양쪽 모두 수정
3. 키워드 충돌 가능성 확인 (예: "작업"과 "검토"가 동시에 포함되지 않도록)

---

## 패턴 6: Phaser 3 sprite 상태 동기화

### 상황
- `sp.status` 변경 후 `sp.label`, `sp.nameTag`, `sp.taskStrip` 색상도 함께 변경해야 함
- 색상 매핑 테이블이 여러 곳에 흩어져 있음

### 교훈
- **상태 변경 시 관련된 모든 시각적 요소를 한 번에 업데이트하는 헬퍼 함수를 만들어라**
- `updateTaskStrip(sp)` 함수로 taskStrip 업데이트 중앙화
- 색상 테이블은 상수로 정의하고 재사용

### 실행 규칙
1. 상태 변경 함수 내에서 `updateTaskStrip(sp)` 호출
2. 색상 매핑 테이블은 단일 상수 객체로 관리
3. `showBubble(sp, text, status)`에서도 상태 기반 테두리 색상 적용

---

## 패턴 7: POI 좌표 스케일링 (/3)

### 상황
- POI_LIST의 좌표는 원본 타일맵 좌표(픽셀 기준)
- Phaser 3 에이전트 스프라이트 좌표는 /3 스케일링된 좌표 사용
- `startWalkTo(sp, targetX, targetY, poi)` 호출 시 좌표 변환 필요

### 교훈
- **POI 좌표를 에이전트 좌표계로 변환할 때는 항상 /3 스케일링을 적용하라**
- `loungePoi.x / 3, loungePoi.y / 3` 패턴
- `startWalkTo` 난수 시드 없음 - 호출 시 변환 완료된 좌표 전달

### 실행 규칙
1. POI_LIST 좌표 사용 시 `/3` 변환 필수
2. `baseX`, `baseY`는 이미 스케일링된 값
3. `startWalkTo` 2,3번 인자는 스케일링된 좌표

---

## 패턴 8: 에이전트 패널 중복 이벤트 바인딩 방지

### 상황
- `openAgentPanel()`이 여러 번 호출될 때 `sendBtn.onclick`이 중복 등록될 수 있음
- `_bound` 플래그로 중복 방지

### 교훈
- **동적으로 이벤트 리스너를 등록할 때는 중복 방지 플래그를 사용하라**
- `sendBtn._bound = true` 패턴
- 또는 `removeEventListener` + `addEventListener` 쌍 사용

### 실행 규칙
1. 동적 이벤트 바인딩 시 플래그 속성으로 중복 방지
2. 패널이 닫힐 때 플래그 초기화 고려
3. `sendBtn.onclick` 대신 `addEventListener` 사용 시 반드시 `removeEventListener`로 정리

---

## 패턴 9: 오프라인-온라인 하이브리드 아키텍처

### 상황
- API 서버가 꺼져 있어도 metaverse.html은 localStorage로 작동해야 함
- fetch 실패 시에도 UI가 깨지지 않아야 함

### 교훈
- **네트워크 호출은 항상 .catch()로 오프라인 상황을 처리하라**
- `fetch(...).then(...).catch(err => console.warn('[API] offline:', err))`
- UI 업데이트는 fetch 이전에 수행하여 네트워크 지연에 영향 없음

### 실행 규칙
1. fetch 호출은 항상 catch 블록 포함
2. UI 업데이트는 fetch 이전에 수행
3. API 응답은 콘솔 로그만, UI는 이미 갱신된 상태

---

## 패턴 10: `.venv` 경로 크로스 플랫폼 호환

### 상황
- Windows에서는 `.venv\Scripts\python.exe`
- Linux/Mac에서는 `.venv/bin/python`
- `열기.bat`은 Windows 전용이므로 상관없지만, 문서에서는 모두 언급 필요

### 교훈
- **가상환경 경로는 플랫폼별로 다르므로, 문서에서 모두 명시하라**
- Windows 배치: `.venv\Scripts\python.exe scripts\api_server.py`
- Linux/Mac: `.venv/bin/python scripts/api_server.py`
- 또는 `uv run` 사용으로 통일

### 실행 규칙
1. 문서에서 Python 실행 경로는 플랫폼별로 명시
2. `uv run`을 권장하여 플랫폼 차이 추상화
3. `열기.bat`은 Windows 전용이므로 Linux용 `열기.sh`도 고려

---

## 패턴 11: push/pull 시 remote 변경사항 취합정리 (merge)

### 상황
- push 시 remote에 로컬에 없는 커밋이 있어 rejected됨
- `git pull --rebase`로 해결하려 했으나 `index.html` 충돌 발생
- `git checkout --theirs`로 단순 교체 → 다른 PC 업데이트 완전히 버림
- 단순 교체는 취합정리(merge)가 아님. 양쪽 변경사항을 통합해야 함

### 교훈
- **push/pull 전 반드시 `git fetch origin`으로 remote 상태를 확인하라**
- **충돌 해결은 단순 교체(`--theirs`/`--ours`)가 아닌 취합정리(merge)여야 함**
- **양쪽 변경사항을 모두 검토하고, 의미적으로 통합 후 충돌 마커 제거**
- **여러 PC에서 작업 시 push 전 항상 remote sync 확인**

### 실행 규칙
1. push 전: `git fetch origin && git log HEAD..origin/master --oneline`로 remote 커밋 확인
2. divergent branches 시: `git pull --rebase` 또는 `git pull --no-rebase` 명시적 선택
3. 충돌 해결 절차 (취합정리):
   ```bash
   git diff --name-only --diff-filter=U  # 충돌 파일 목록
   
   # 각 파일별로 양쪽 변경사항 확인
   git diff --theirs <file>              # remote 변경 내용
   git diff --ours <file>                # local 변경 내용
   
   # 파일 열어서 충돌 마커(<<<<<<< ======= >>>>>>>) 기준으로 취합정리
   # - 양쪽 모두 필요한 내용은 병합
   # - 충돌하는 부분은 의미적으로 수정
   # - 충돌 마커 제거
   
   git add <file>
   GIT_EDITOR=true git rebase --continue
   ```
4. **절대 `git checkout --theirs` 또는 `git checkout --ours`로 단순 교체 금지**
5. 복잡한 충돌 시 merge tool 사용: `git mergetool` 또는 `code --wait <file>`
6. 충돌 파일이 핵심 변경 대상이 아니더라도 diff로 내용 확인 후 취합정리

---

## 패턴 12: index.html MD 에디터 탭 중복 생성 반복 문제

### 상황
- Kimi Code가 index.html에 MD 에디터 탭/CSS를 추가할 때마다
  `id="tab-editor"` div와 `/* ── MD 에디터 ── */` CSS 블록을 중복 생성함
- 현재까지 2번 반복 (634줄씩 증가)
- 중복 탭 버튼도 3개로 늘어남

### 교훈
- **index.html 수정 전 반드시 중복 여부 확인하라**
- `id="tab-editor"` div는 1개만 존재해야 함
- CSS `/* ── MD 에디터 ── */` 블록은 1개만 존재해야 함
- `switchTab('editor')` 탭 버튼은 1개만 존재해야 함 (JS 내부 호출 제외)

### 실행 규칙
1. index.html 수정 전:
   ```bash
   grep -c 'id="tab-editor"' index.html        # → 1이어야 함
   grep -c "switchTab('editor')" index.html    # → nav에서 1이어야 함
   grep -c '/* ── MD 에디터 ── */' index.html  # → 1이어야 함
   ```
2. 이미 존재하는 섹션은 교체(replace)하라, 추가(append)하지 말라
3. 중복이 발견되면 Claude Code에 삭제 요청 (2번 반복됨)

---

## 패턴 13: PALETTE.corridor 색상 덮어쓰기 문제

### 상황
- metaverse.html의 `PALETTE.corridor` 값을 베이지(0xD4C4A0)로 수정함
- 그러나 Kimi Code가 drawFloor/drawWalls를 재작성할 때마다 원래 값(0x1E2530)으로 복원됨
- 검증 스크립트 없이 push하면 다음 세션에서 다시 되돌아옴

### 교훈
- **복도 베이지 색상은 PALETTE 상수에서 설정되며, 변경 후 반드시 검증해야 함**
- `PALETTE.corridor: 0xD4C4A0` (밝은 베이지)
- `PALETTE.corridor2: 0xC8BA94`
- `PALETTE.corridor_line: 0xBFB090`

### 실행 규칙
1. metaverse.html 수정 후 항상 확인:
   ```bash
   grep "corridor:" metaverse.html  # 0xD4C4A0 이어야 함
   ```
2. drawFloor 전체 교체 시 PALETTE.corridor 값 보존 필수
3. PALETTE 블록은 파일 상단(~310줄)에 위치

---

## 패턴 14: index.html 단일 ID 요소 중복 생성 반복

### 상황
- `id="toast"` div가 8개까지 누적됨 (1개만 필요)
- 기존에도 `id="tab-editor"`, CSS `/* ── MD 에디터 ── */` 중복 2~3회 발생
- 공통 원인: HTML 파일 내 기존 요소 확인 없이 body 끝에 append

### 단일 ID 요소 목록 (각각 정확히 1개만 존재해야 함)
| 요소 | 위치 |
|------|------|
| `id="toast"` | body 끝, JS 알림용 |
| `id="tab-editor"` | 탭 콘텐츠 div |
| `id="agent-drawer"` | 에이전트 상세 드로어 |
| `id="drawer-overlay"` | 드로어 오버레이 |

### 실행 규칙
1. index.html 수정 전 반드시:
   ```bash
   python scripts/validate.py       # 자동 감지
   python scripts/validate.py --fix # 자동 수정
   ```
2. 새 HTML 요소 추가 시: append 금지 → 기존 요소 replace
3. `id=` 속성이 있는 모든 요소는 페이지 전체에서 유일해야 함 (HTML 명세)

---

## 패턴 15: 이름태그 가독성 부족

### 상황
- 에이전트 이름이 캐릭터 머리 위에 표시되나 폰트가 작고 배경 없이 흐릿함
- strokeThickness가 낮아 배경 구분이 안 됨

### 해결
- label fontSize: '13px' (현재), strokeThickness: 4
- label 배경: backgroundColor 또는 stroke 강화
- py - 34 위치(머리 위)에서 충분한 대비 필요

### 실행 규칙
1. 이름태그 수정 시 `createAgent()`의 label text style 참조
2. stroke '#000000', strokeThickness 최소 4 유지
3. color는 팀 컬러 대신 '#E6EDF3' (밝은 흰색) 권장 (가독성 우선)

---

## 패턴 16: `git pull` 미흡 — fetch 없이 status만 보고 "최신" 오판

### 상황
- 사용자가 "pull 해줘"라고 요청
- `git status`만 보고 "Your branch is up to date with 'origin/master'"라고 답변
- 실제로는 `git fetch origin`을 실행하지 않아 원격에 9개의 새 커밋이 있는 줄 몰랐음
- 사용자가 두 번째로 지적한 후에야 fetch → 차이 확인 → pull 진행

### 교훈
- **`git status`의 "up to date"는 로컬 캐시 기준이며 fetch 전에는 신뢰할 수 없음**
- "pull 해줘" = 반드시 `git fetch origin` 먼저 실행 후 실제 차이 확인
- `git fetch --all --prune` 습관화

### 실행 규칙 (pull 요청 시 절차)
1. **반드시 먼저 fetch:**
   ```bash
   git fetch origin
   # 또는
   git fetch --all --prune
   ```
2. **차이 확인:**
   ```bash
   git log HEAD..origin/master --oneline   # 내가 없는 커밋
   git log origin/master..HEAD --oneline   # 원격이 없는 커밋
   ```
3. **파일 단위 diff 확인:**
   ```bash
   git diff origin/master --stat
   ```
4. 그 후 pull 또는 rebase 결정
5. **절대 `git status`만 보고 "최신"이라고 답변 금지**
