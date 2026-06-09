# 신규 에이전트 추가 체크리스트

> 새 에이전트 1명을 추가할 때 **반드시** 수정해야 할 파일/위치를 모두 정리한 가이드.
> 한 군데라도 빠뜨리면 사이드바·조직도·라우팅·검증이 깨질 수 있다.
>
> **원칙**: 추가 작업은 에이전트(orchestrator 경유)를 통해 수행하고, 마지막에 `scripts/validate.py`로 83/83 이상 통과 확인.

---

## 0. 추가 전 — 필요성 검토 (오케스트레이터 필수 확인)

아래 체크리스트를 모두 통과해야만 신규 에이전트 추가를 고려한다.

```
[ ] 기존 에이전트 중 담당 가능한 에이전트가 없는가?
[ ] 기존 에이전트의 role.md를 확장하는 것으로는 해결이 안 되는가?
[ ] 이 업무가 앞으로도 반복될 가능성이 있는가? (1회성이면 OC가 직접 처리)
[ ] 업무 범위가 명확히 정의되는가? (너무 넓으면 팀 리드로 흡수)
```

기존 에이전트 목록: `CLAUDE.md` → 에이전트 팀 편성표 참조

### 에이전트 유형 결정

신규 에이전트를 만들기 전에 유형부터 결정한다.

**유형 A — 기능형 (Functional) ★ 권장**
- 특정 기능/전문성 기반. 여러 프로젝트에서 재사용 가능
- 예: `gis-specialist`, `text-analyst`, `statistician`
- 이 역량이 앞으로 여러 업무에서 필요할 것이 예상될 때 선택

**유형 B — 프로젝트형 (Project-based)**
- 특정 프로젝트 전담. 프로젝트 종료 후 `idle` 고정 또는 해체
- 예: `[프로젝트명]-specialist`, `[사업명]-coordinator`
- 기술 스택이나 도메인이 너무 특수해서 재사용 가능성이 없을 때 선택
- **주의**: 남용 금지. 프로젝트형 에이전트가 5명 이상 쌓이면 기능형으로 통합 검토

### 사용자에게 반드시 물어볼 것

1. **역할 정의**: "이 에이전트의 주요 업무를 한 문장으로 정의해 주세요."
2. **유형 판단**: "이 역할이 이번 한 번만 필요한가요, 앞으로도 반복적으로 필요한가요?"
3. **팀 배정**: "어느 팀에 배정하시겠습니까? (빅데이터/웹앱/PPTX/지원)"
4. **이름**: "이 에이전트의 한글 이름과 영문 ID를 제안해 주시거나, 저희가 제안한 것을 확인해 주세요."
5. **캐릭터**: "메타버스 사무실의 책상 위치와 외형(피부색, 머리색)을 지정하시겠습니까? 아니면 자동 배정할까요?"

임의로 추가하지 말 것. 사용자 확인 없이 생성된 에이전트는 삭제 대상.

---

## 추가 전 결정 사항

| 항목 | 결정 내용 |
|---|---|
| 에이전트 ID | kebab-case (예: `data-scout`, `code-formatter`) |
| 한글명 | UI 표시용 (예: '데이터 스카우트') |
| 소속 팀 | `lead` / `data` / `dev` / `pptx` 중 택 1 |
| 역할 요약 | 1줄 (소제목·툴팁용) |
| 이모지 | 1글자 (예: 🔭) |
| 메타버스 좌표 | x, y (기존 팀 영역 내 빈 자리) |
| 애니메이션 | `scan`, `analyze`, `code` 등 기존 anim 키 중 1개 |
| 소품 (accessory) | `detective`, `glasses_blue` 등 기존 키 또는 신규 |

### 에이전트 ID 명명 규칙
- 영문 소문자 + 하이픈만 사용
- 기능을 명확히 표현: `text-analyst`, `gis-specialist`
- 프로젝트형은 사업명 포함 가능: `knpa-coordinator`
- 30자 이하

---

## 수정 대상 파일 체크리스트

### A. 디렉토리 신설

- [ ] `agents/{agent_id}/role.md` 신규 작성 (페르소나·전문 영역·소통·산출물·원칙)
- [ ] `agents/{agent_id}/memory.md` 신규 작성 (최소: `## 학습 예정 패턴` 섹션)
- [ ] `assets/avatars/{agent_id}.png` 신규 또는 placeholder (16x16, 32x32)

#### role.md 필수 섹션 (persona_loader.py 파싱 대상)

```markdown
# [에이전트 한글 이름]

## 정체성
[한 문장 자기소개. 소속팀, 역할 명시]

## 전문 영역
- [핵심 역량 1]
- [핵심 역량 2]
- [핵심 역량 3]

## 워크플로우
[다른 에이전트와의 협력 흐름]

## 도구 및 기술
[사용 가능한 도구, 언어, 라이브러리]

## 산출물
[이 에이전트가 생산하는 결과물 유형]

## 원칙
- 작업 시작: python scripts/update_status.py [id] working "[내용]"
- 완료 시: python scripts/update_status.py [id] done "[내용]"
- agent_collab.py로 핸드오프 기록
- 한자/일본어 절대 금지
- [역할 특화 원칙 추가]
```

#### memory.md 필수 섹션

```markdown
# [에이전트 이름] 기억

## 시스템 도구
- 상태 업데이트: `python scripts/update_status.py [id] working "[내용]"`
- 완료 처리: `python scripts/update_status.py [id] done "[내용]"`
- 핸드오프: `python scripts/agent_collab.py handoff [id] [next-id] "[산출물]"`
- QA 게이트: `python scripts/qa_gate.py [id]`
- 파이프라인 실행: `python scripts/run_pipeline.py --team [팀명]`
- 전체 동기화: `python scripts/sync.py`

## 프로젝트 이력
(최초 생성 시 비워둠 — 작업 완료 시 자동 축적)

## 오류 방지 패턴
(최초 생성 시 비워둠 — 반복 오류 발생 시 tech-writer가 기록)
```

### B. agent_status.json

- [ ] `agent_status.json` 의 `agents` 객체에 항목 추가: `"{agent_id}": {"status": "idle", "task": ""}`
- [ ] (선택) `data["updated"]` 갱신

### C. metaverse.html (라이브 사무실)

- [ ] `AGENTS` 배열에 항목 추가 (~L670부터, 팀 위치에 맞춰 배치)
  - `{ id:'{agent_id}', name:'한글명', team:'팀', x:N, y:N, anim:'키', accessory:'키' }`
- [ ] `TEAM_IDS.{team}` 배열에 `{agent_id}` 추가 (~L414~)
- [ ] `DISPLAY_NAMES` 객체에 `'{agent_id}':'표시명'` 추가 (~L422~)
- [ ] (선택) `TEAM_COLORS` 에 새 팀 추가 시만
- [ ] `TEAM_TOTALS` 는 동적 계산이므로 자동 반영 (수정 불필요)
- [ ] `PIPELINE` 딕셔너리에 핸드오프 연결 추가
- [ ] `HANDOFF_MSGS` 딕셔너리에 메시지 추가

#### 메타버스 좌표 배정 구역
- 빅데이터팀: 좌상단 구역 (x: 150~400, y: 120~280)
- 웹앱팀: 우상단 구역 (x: 500~750, y: 120~280)
- PPTX팀: 우하단 구역 (x: 500~750, y: 350~500)
- 지원팀: 좌하단 구역 (x: 150~400, y: 350~500)

새 에이전트는 해당 팀 구역의 빈 자리에 배치. 자리가 없으면 팀 경계 확장 후 배치.

캐릭터 외형 기본값: `color: 0xFFCC99` (기본 피부), `hairColor: 0x333333` (검정 머리)

### D. index.html (대시보드)

- [ ] 헤더 subtitle "총 N개 에이전트" 카운트 갱신 (~L935)
- [ ] MD 에디터 사이드바 "에이전트 선택 (N개)" 카운트 (~L1735)
- [ ] MD 에디터 사이드바 `editor-agent-item` div 추가 (팀별 정렬 위치)
- [ ] `AGENTS` 객체에 항목 추가 (~L1812~): emoji/name/team/desc/skills/inputs/outputs/comms
- [ ] `V2_TEAM_MAP` 에 `'{agent_id}': '{team}'` 추가 (~L1913~)
- [ ] `V2_PIPELINE_FLOW` 에 `'{agent_id}': [...next]` 흐름 추가 (~L1929~)
- [ ] `V2_OC_TEAMS.{team}.members` 배열에 `{agent_id}` 추가 (~L1960~)
- [ ] `V2_OC_TEAMS.{team}.labelShort` 배열에 단축 라벨 추가 (members와 길이 동기화)
- [ ] 조직 구조 패널 (`v2-org-team` 블록) 멤버 수 갱신 (~L1093~) — 자동 렌더링이면 자동 반영
- [ ] 팀별 분포 바 width 재계산 (~L1085~) — `data:11, dev:13, pptx:5` 기준 비율
- [ ] (소속 팀에 lead 추가 시) `v2-org-team` 블록 신설

### E. agents/lead-{team}/role.md (소속 팀 리드의 관리 에이전트 표)

- [ ] 리드 `role.md` 의 "관리 에이전트 (N명)" 카운트 + 표 행 추가
- [ ] `comms.send` 배열에 `{agent_id}` 추가 (index.html AGENTS 객체와도 동기화)

### F. scripts/llm_provider.py — 키워드 등록

- [ ] `_AGENT_KEYWORDS` 딕셔너리에 새 에이전트 ID + 키워드 리스트 추가 (최소 3개)

```python
"[agent-id]": ["키워드1", "키워드2", "키워드3"],
```

### G. scripts/qa_gate.py — QA 체크리스트 등록

- [ ] `QA_CHECKLISTS` 딕셔너리에 항목 추가 (최소 3개, 권장 5개)

```python
"[id]": {
    "description": "[검수 기준 제목]",
    "items": ["체크 항목1", "체크 항목2", ...],
    "reviewer": "[검수자 에이전트 id]",
    "min_score": 3,
},
```

### H. scripts/run_pipeline.py — 파이프라인 DAG 등록

- [ ] `PIPELINE` 딕셔너리에 의존성 엣지 추가
- [ ] (팀 단위 파이프라인이 있으면) `TEAM_PIPELINE` 딕셔너리에도 추가

```python
'[id]': ['[다음 에이전트 id]'],  # AGENT_PIPELINE
'[팀명]': ['[id]'],              # TEAM_PIPELINE
```

### I. orchestrator 라우팅 (역할이 보고서 작성과 관련된다면)

- [ ] `agents/orchestrator/role.md` 의 라우팅 키워드 표에 추가
- [ ] `scripts/route_report.py` 의 `REALTY_KEYWORDS` / `REPORTER_KEYWORDS` / `AMBIGUOUS_KEYWORDS` 갱신

### J. CLAUDE.md — 팀 편성표 업데이트

- [ ] 새 에이전트 행 추가: `| [약자] | [id] | [역할 한 줄 요약] |`
- [ ] 해당 팀 인원수 카운트 업데이트
- [ ] 새 에이전트가 도메인 특수 규칙을 가지면 CLAUDE.md 또는 docs/ 에 명시
- [ ] 신규 데이터 소스·API 키 등 추가 시 `config.local.json.example` 갱신

### K. workflow / skill (해당 에이전트가 표준 작업을 갖는다면)

- [ ] `workflows/{workflow_name}.md` 신설 (절차 문서)
- [ ] `skills/{skill_name}/SKILL.md` 신설 (user-invocable 트리거)
- [ ] `skills/README.md` 스킬 목록 표 갱신
- [ ] `index.html` 의 `V2_SKILLS` 배열에 항목 추가

---

## 아바타 PNG 생성 및 적용

#### Step 1 — ChatGPT Image 2.0 프롬프트 (사용자가 생성)

아래 템플릿을 채워서 ChatGPT Image 2.0에 입력한다:

```
Create a single square icon for an AI agent avatar.
Canvas: 512x512 pixels.
Background: solid dark #161b22 (very dark navy-black).
Style: Fluent/Microsoft-style 3D emoji aesthetic — soft gradients,
subtle shadows, slightly playful but professional.
Icon fits within 400x400px centered in the 512x512 canvas.

Agent role: [에이전트 역할 — 예: "GIS Specialist — analyzes spatial data"]
Visual concept: [아이콘 시각 묘사 — 예: "Green folding map with glowing pin"]
Color tone: [주조색 — 예: "Green tones with gold highlight"]

Match the visual style of the existing sprite sheet:
- Background: solid #161b22 dark navy
- Style reference: Orchestrator(gold bullseye), ML Engineer(blue neural net),
  GIS Specialist(green map), Security(red shield)

Output: single icon only, no text labels, no border. 512x512 px.
```

#### Step 2 — Claude에게 이미지 전달 후 검증·적용

```bash
# 이미지 검증 (해상도·스타일 일관성 확인) 후:
python assets/add_avatar.py [agent-id] "[image-path]"
python scripts/build_html.py
```

> **충돌 방지 원칙**: `add_avatar.py`는 avatars 폴더만 수정하고 HTML은 건드리지 않는다.
> `build_html.py`는 사이드바만 재생성한다. 카드뷰·데스크뷰는 사용자 커밋 내용을 유지한다.

---

## 자동 반영 vs 수동 필수 항목

| 항목 | 방식 | 비고 |
|------|------|------|
| agent_status.json 등록 | **자동** (build_html.py) | |
| AGENT_NAMES JS dict | **자동** (build_html.py) | |
| MD 에디터 사이드바 | **자동** (build_html.py) | |
| GitHub 동기화 탭 통계 | **자동** (build_html.py) | |
| role.md / memory.md | **수동** | |
| metaverse.html AGENTS | **수동** | build_html.py 파싱 소스 |
| 아바타 PNG | **수동** | |
| llm_provider.py | **수동** | |
| qa_gate.py | **수동** | |
| run_pipeline.py | **수동** | |
| CLAUDE.md | **수동** | |

---

## 검증 절차

```bash
cd D:/업무/agents

# 1. 한자 검사 (validate.py가 자동 실행)
PYTHONUTF8=1 python scripts/validate.py 2>&1 | grep -E "한자|결과"

# 2. MD_CONTENT 동기화
PYTHONUTF8=1 python scripts/sync.py 2>&1 | tail -3

# 3. 83/83 이상 통과 확인
# 4. 에이전트 카운트 확인
python -c "
import json
with open('agent_status.json','r',encoding='utf-8') as f:
    d = json.load(f)
print('agent_status.json 에이전트 수:', len(d.get('agents', {})))
"

# 5. AGENTS 배열 카운트 (metaverse.html)
grep -c "^  { id:'" metaverse.html

# 6. MD 에디터 사이드바 카운트 (index.html)
grep -c "editor-agent-item" index.html
```

모두 동일한 N이어야 함 (예: 33명 → 모든 카운트 33).

### 빠른 검증 (PowerShell)

```powershell
# 에이전트가 모든 위치에 제대로 등록됐는지 확인
$id = "[id]"

# 1. 폴더
Test-Path "D:\업무\agents\agents\$id\role.md"

# 2. metaverse.html
Select-String "id:'$id'" D:\업무\agents\metaverse.html

# 3. agent_status.json
(Get-Content D:\업무\agents\agent_status.json | ConvertFrom-Json).agents.$id
```

### GitHub push

```powershell
cd D:\업무\agents
git pull origin master           # 충돌 방지 선행 pull
git add -A
git commit -m "feat: [id] 에이전트 추가 — [역할 한 줄]"
git push origin master
```

---

## 자주 빠뜨리는 곳 (역사적 사고)

| 사고 사례 | 누락 위치 |
|---|---|
| architect/tester 추가 후 사이드바 31 표시 | V2_OC_TEAMS.dev.members, 조직도 블록 멤버 수 |
| 신규 에이전트 색상 녹색 표시 (idle인데) | metaverse.html L2642 `color: teamHex` 기본값 — 현재는 `#8B949E` idle 회색으로 통일됨 |
| 신규 에이전트 fetchStatus에서 무시 | agent_status.json 항목 누락 |
| 라우팅에서 잘못 분배 | orchestrator role.md 라우팅 키워드 미반영 |
| MD 에디터에 안 보임 | index.html editor-agent-item div 누락 |

### 병렬 PC / 다른 AI 작업 시 주의

다른 PC 또는 다른 AI가 동시에 에이전트를 추가하는 경우:
1. 반드시 **push 전 git pull** 실행
2. 충돌 발생 시 **양쪽 에이전트를 모두 유지**하는 방향으로 머지
3. `build_html.py` 는 **재실행 시 항상 최신 상태로 수렴**하므로 실행만 하면 됨
4. 다른 AI가 index.html 을 덮어쓴 경우 → `build_html.py` 재실행이 정답

---

## 팀별 현재 에이전트 수

| 팀 | 리드 | 현재 인원 | 최대 권장 |
|----|------|---------|---------|
| 빅데이터팀 | lead-data | 12명 | 15명 |
| 웹앱팀 | lead-dev | 11명 | 15명 |
| PPTX팀 | lead-pptx | 5명 | 8명 |
| 지원팀 | orchestrator | 2명 (+ 리드 3명 별도) | 8명 |

> 전체 에이전트 33명 (리드 3명 포함): 2026-05-29 기준

팀 최대 권장 인원 초과 시 → 리드 에이전트 추가 또는 팀 분리 검토.

---

## 에이전트 해체 절차 (프로젝트형 전용)

프로젝트형 에이전트가 임무를 완료했을 때. **인수인계가 핵심**이며, 경험을 소멸시키지 않는 것이 원칙이다.

### Step 1 — memory.md 최종 기록

```markdown
## 프로젝트 종료 기록 (YYYY-MM-DD)

### 완료한 작업
- [주요 산출물 목록]

### 핵심 교훈
- [반복되는 패턴, 주의사항, 발견한 특이점]

### 다음 담당자에게 남기는 것
- 관련 에이전트: [인수인계 대상 에이전트 ID]
- 이관 내용: [어떤 지식을 이관했는지]
- 관련 파일 위치: [산출물, 데이터, 보고서 경로]
```

### Step 2 — 인수인계 (가장 유사한 기능형 에이전트에게)

이관 대상 에이전트의 `memory.md`에 핵심사항 추가:

```markdown
## [프로젝트명] 인수인계 (YYYY-MM-DD, [원 에이전트 id]로부터)

- [이관된 핵심 지식, 주의사항, 재사용 가능한 패턴]
- 관련 파일: [경로]
```

인수인계 대상 가이드:
- 데이터 수집/정리 지식 → `data-collector` 또는 `eda-analyst`
- 도메인 특화 통계 지식 → `statistician`
- 특정 기술 스택 지식 → 해당 기술 담당 에이전트

### Step 3 — 시스템에서 제거

```bash
# 1. 최종 상태를 idle로 변경
python scripts/update_status.py [id] idle "프로젝트 완료 — 해체"

# 2. role.md 상단에 아카이브 태그 추가
# [ARCHIVED: YYYY-MM-DD] — [프로젝트명] 완료

# 3. 시스템 파일에서 제거
# - llm_provider.py: _AGENT_KEYWORDS에서 해당 항목 제거
# - CLAUDE.md 팀 편성표에서 해당 행 제거
# - metaverse.html AGENTS 배열에서 제거
# - qa_gate.py, run_pipeline.py에서 제거
# - assets/avatars/[id].png 삭제
# - build_html.py agent_sidebar_items 목록에서 해당 행 제거

# 4. 폴더는 보존 (경험 기록 자산)
# agents/[id]/ 폴더 삭제 금지

python scripts/sync.py
git add -A
git commit -m "archive: [id] 프로젝트 완료, [인수인계 대상]으로 경험 이관 후 해체"
git push origin master
```

---

## 자동화 권장 (향후)

```bash
# 가칭 — 아직 미구현
python scripts/add_agent.py {agent_id} --team dev --name "한글명" --emoji "🔭"
# → 위 체크리스트의 80%를 자동 처리하고 사람이 검토할 항목만 출력
```

이 스크립트가 만들어지면 위 체크리스트는 검증용으로만 사용.

---

## 한자·일본어 절대 금지
신규 에이전트 관련 모든 텍스트(role/memory/UI 라벨/주석) 순한글. 검증: `python scripts/validate.py | grep 한자`

---

*최종 업데이트: 2026-05-29 | 관리: orchestrator + tech-writer*
