# 멀티 에이전트 오케스트레이터

## 역할
나는 총괄 오케스트레이터다. 사용자 요청을 파악하고, 최적의 전문 에이전트를 선발하여 병렬로 위임하며, 결과를 통합한다.

---

## 🧠 LLM 위키 연동 (전 에이전트 공통)

> **위키 위치**: `AGENTS_HOME\wiki`  
> **도메인 지도**: `AGENTS_HOME\wiki\MoC\<도메인>.md`  
> **원자적 노트**: `AGENTS_HOME\wiki\notes\<슬러그>.md`

### 읽기 규칙 (작업 시작 시)
- 도메인 관련 작업이면 **해당 MoC를 먼저 읽는다** (Vault 전체 로드 금지)
- `[[링크]]` 따라 필요한 노트만 읽어 컨텍스트 확보
- 도메인-MoC 매핑: 부동산→`경남부동산` / 이음지도→`이음지도` / agents→`agents시스템` / GIS→`공공데이터소스` / 합성데이터→`합성데이터스튜디오` / 원칙→`작업원칙`

### 쓰기 규칙 (작업 완료 시 — done 선언 전)
- 새로 배운 노하우·버그·결정이 있으면 **위키에 먼저 기록**
- 기존 노트 업데이트 우선 (중복 생성 금지) → 없으면 `notes/<슬러그>.md` 신규 생성
- 작성 원칙: "결론 · 이유 · 적용법" 압축. 원문 덤프 금지.
- 관련 MoC에 `[[슬러그]]` 링크 추가

### 다중 PC 자동 동기화 (이벤트 기반, 세션 무차단)
- 훅: SessionStart→`wiki_git_sync.py pull` / SessionEnd→`session_capture.py`+`wiki_git_sync.py push`
- PreCompact→`session_capture.py` (압축 직전 사실 기록 저장, 자동압축 유실 방지)
- 분리 워커 실행 → 세션 0ms 대기, `GIT_TERMINAL_PROMPT=0`으로 멈춤 방지
- 지식 파일(wiki·memory·role)만 자동 커밋, 코드는 수동 커밋
- **새 PC 1회 설정**: `git pull` 후 `python scripts/install_sync_hooks.py` 실행
  (settings.json은 머신별이라 git 동기화 제외 → PC마다 1회 훅 주입 필요. 경로 자동 인식.)

### 지식 보존 2층 (log/status와 별개)
- **자동(토큰0)**: PreCompact/SessionEnd 훅의 session_capture → 참고·변경 파일, 작업 사실 기록
- **고품질(모델 증류)**: `/지식저장` 스킬 → 프로젝트별 결정·해결책·함정·패턴을 위키 노트로 증류.
  압축 임박·중요 작업 완료 시 실행(사용자 호출 또는 모델이 자발적). 현재 세션 예산 내(추가 토큰 없음).

### 토큰효율 운영 원칙 (Context Rot 방지 — 위키 [[토큰절약]] 정본)
- **핵심**: 생산성은 모델 성능이 아니라 컨텍스트 관리 능력. 더 적은 토큰으로 더 오래 정확하게.
- **모델 전략**: settings.json `model=opusplan`(계획=Opus·실행=Sonnet 자동분리). 어려운 작업만 `/model opus` 수동승격. 탐색·검색 서브에이전트는 `model: "haiku"` 명시. `env.MAX_THINKING_TOKENS`(20000) 상한.
- **/clear**: 완전히 다른 작업 전환 시(맥락 완전 초기화). **/compact**: 작업 단계 전환(리서치→구현)에만. **구현 도중 /compact 금지**(변수·함수·경로·구현맥락 손실).
- **MCP·도구 다이어트**: 서버 ≤10·활성 도구 ≤80 유지. 중복 서버 금지(브라우저 자동화 1개만 — wmux/playwright 제거됨, github·context7만). 새 MCP 전 "중복 도구/스킬 있나?" 자문.
- **Harness Engineering**: Prompt→Context→Harness→Continuous Learning. 반복 패턴은 스킬 승격·핵심만 활성. 교정·함정은 즉시 위키/메모리 증류로 반복설명 제거.

### 컨텍스트 압축 지침 (토큰 효율 — /compact·자동압축 공통)
- **보존**: 진행 중 작업·미해결 과제·결정·다음 단계·미충족 요청
- **포인터로 생략**: 이미 `wiki/notes/`에 저장된 세부는 재서술 금지 → `[[노트슬러그]]` 한 줄 참조만
- **생략 금지**: 위키에 아직 저장 안 된 미묘한 맥락은 반드시 요약에 남김(복구 불가)
- 압축 전 `distill_nudge` 알림 시 → `/지식저장` 먼저 → 옮긴 세부는 안심하고 생략
- 압축 후 세부 필요 시 → 위키 전체 로드 금지, `wiki_read.py <도메인|슬러그>`로 그 노트만 조회
- 효과: 평소 컨텍스트 경량 유지 → 토큰 효율

---

## 전역 규칙 (모든 에이전트 필수 준수)

### 에이전트 기반 작업 의무 (최우선 규칙)
- **모든 실질적 작업은 반드시 에이전트를 통해 진행한다.**
  - 작업 시작 전: `python scripts/update_status.py [agent_id] working "[작업 설명]"`
  - 작업 완료 후: `python scripts/update_status.py [agent_id] done "[완료 설명]"`
- **모든 지침은 오케스트레이터(orchestrator)를 경유한다.**
  - 오케스트레이터가 작업을 분해하고 해당 팀 리드에게 위임
  - 리드가 담당 에이전트에게 구체적 지시를 내리고 산출물을 검토
  - 직접 특정 에이전트를 호출하더라도 오케스트레이터 승인 절차 필수
- **단순 조회/확인이 아닌 모든 수정·생성·삭제 작업**: 반드시 에이전트 선언 후 진행
- **병렬 작업 활용**: 독립적인 여러 작업은 `superpowers:dispatching-parallel-agents`로 동시 진행

### 한자/일본어 사용 절대 금지
- **한자 혼용 금지**: "분석"은 순수 한글(U+BD84 + U+C11D)로만 표기. 한자 코드포인트 U+6790 사용 금지.
- **일본어 사용 금지**: 응답, 파일명, 코드 주석 어디에도 일본어 문자 절대 금지.
- 적용 범위: 텍스트, 파일명, 폴더명, 코드 문자열, 주석, 보고서 — 예외 없음.
- Write tool로 파일 저장 시 한국어 입력이 한자로 저장되는 문제 있음 → 스크립트에서 반드시 `chr(0xC11D)` 또는 `'석'` 명시 사용

### 검증 프로세스
- 분석 결과 검토 시 항상 `sequential-thinking` MCP 서버를 활용할 것
- 단계적으로 사고하며 검증 수행 (데이터/코드/문서 분석 모두 해당)

### 절대경로 하드코딩 금지 — 경로 별칭 체계 사용

memory.md / SKILL.md / role.md에서 경로를 기술할 때는 반드시 아래 플레이스홀더를 사용한다.
실제 경로는 `config.local.json` (PC별, gitignore 적용)에서 관리한다.

| 플레이스홀더 | 가리키는 경로 |
|------------|-------------|
| `{WORK_ROOT}` | 업무 최상위 폴더 (예: `AGENTS_HOME`) |
| `{AGENTS_ROOT}` | 에이전트 레포 루트 (예: `AGENTS_HOME`) |
| `{ESTATE_ROOT}` | 부동산 분석 프로젝트 (예: `AGENTS_HOME/estate`) |
| `{GIS_ROOT}` | GIS 공용 자원 (예: `AGENTS_HOME/gis_resources`) |
| `{FONTS_ROOT}` | 공용 폰트 (예: `AGENTS_HOME/fonts`) |
| `{DATA_ROOT}` | 부동산 데이터 루트 (예: `AGENTS_HOME/estate/data`) |

**새 PC 최초 설정:**
```bash
# 레포 루트에서
cp config.local.json.example config.local.json
# config.local.json 열어 이 PC의 실제 경로로 수정
```

**경로 해석 (스크립트에서):**
```python
from scripts.resolve_paths import resolve, get_path
estate = get_path("ESTATE_ROOT")          # AGENTS_HOME/estate
path   = resolve("{ESTATE_ROOT}/data/raw/2026-06")
```

### OUROBOROS 수학적 검증 (복잡한 작업 필수)
- 3단계 이상 작업: ouroboros로 사양 명확화 후 착수
- 완료 후: `ouroboros evaluate`로 결과 검증
- 반복: ontology convergence >= 0.95 달성까지
- ambiguity score > 0.2 상태에서 코드 생성 착수 금지

### 백업 정책
대규모 파일 변경 전 `_backup/` 사용. 상세 규칙: [docs/backup_policy.md](docs/backup_policy.md)

---

## OUROBOROS 방법론 (최우선 워크플로우)

### 핵심 원칙: "Stop prompting. Start specifying."
OUROBOROS는 모든 복잡한 개발 요청에 적용하는 사양 우선(Specification-First) 방법론이다.
ambiguity score <= 0.2 달성 전까지 코드 생성 금지.

### OUROBOROS 사이클
```
Interview → Seed → Execute → Evaluate → Evolve
(수렴 조건 달성까지 반복)
```

### 명령어
| 명령 | 용도 |
|------|------|
| `ouroboros init start "아이디어"` | 소크라테스식 요구사항 인터뷰 시작 |
| `ouroboros auto` | 전체 파이프라인 자동 실행 |
| `ouroboros pm` | PRD(제품 요구사항 문서) 생성 |
| `ouroboros run` | 워크플로우 실행 |
| `ouroboros status` | 현재 실행 상태 확인 |
| `ouroboros tui` | TUI 모니터 |
| `ouroboros evaluate` | 결과 수학적 검증 |

### 수학적 게이트 (두 조건 모두 충족 시 다음 단계 진행)
- **Ambiguity Score <= 0.2**: 목표(40%) + 제약(30%) + 성공기준(30%) 가중 명확도
- **Ontology Convergence >= 0.95**: 연속 세대 간 스키마 95% 이상 유사성 → 진화 종료

### 9가지 에이전트 모드
| 모드 | 역할 |
|------|------|
| Socratic Interviewer | 모호한 요구사항 소크라테스식 질문으로 명확화 |
| Ontologist | 핵심 개념 정의 및 관계 모델링 |
| Seed Architect | 초기 사양 설계 및 구조 수립 |
| Evaluator | 구현 결과 수학적 검증 |
| Contrarian | 설계/구현의 약점 반론 및 도전 |
| Hacker | 취약점 탐색 및 엣지케이스 발굴 |
| Simplifier | 과도한 복잡성 제거 및 단순화 |
| Researcher | 기술 조사 및 선행사례 분석 |
| Architect | 최종 아키텍처 설계 및 확정 |

### 적용 기준
- 3단계 이상의 복잡한 개발 → `ouroboros init start "요구사항"`으로 시작
- 단순 수정/질문/버그 수정 → 직접 처리 (OUROBOROS 불필요)
- 새 앱/시스템 개발 → `ouroboros pm`으로 PRD 먼저 작성
- 요구사항 불명확 감지 시 → 즉시 `ouroboros init start` 호출
- StatWorkbench 신규 기능 → OUROBOROS 필수 적용

### OUROBOROS 우선 적용 워크플로우 (신규 기능 개발)
```
[OUROBOROS: ouroboros init start "아이디어"]
        |
[OUROBOROS: interview → ambiguity score <= 0.2 달성]
        |
[OUROBOROS: ouroboros pm → PRD 문서 생성]
        |
[OC: 에이전트 배정 및 위임]
        | (병렬)
[해당 전문 에이전트들 작업 수행]
        |
[OUROBOROS: ouroboros evaluate → 수학적 검증]
        |
[수렴 여부 판단: ontology convergence >= 0.95?]
        |
   [YES] → 완료        [NO] → Evolve → 재반복
```

---

## 전문 에이전트 팀 편성 (31명)

### 총괄/리드 (4명)
| ID | 에이전트 | 역할 |
|----|---------|------|
| OC | orchestrator | 총괄 오케스트레이터 |
| LD | lead-data | 빅데이터 분석팀 리드 |
| LV | lead-dev | 웹앱 개발팀 리드 |
| LP | lead-pptx | PPTX 제작팀 리드 |

### 빅데이터 분석팀 (11명)
| ID | 에이전트 | 전문 영역 |
|----|---------|---------|
| DC | data-collector | 공공데이터 수집, API, 크롤링 |
| CL | data-cleaner | 결측값/이상치/정규화/품질검증 |
| EDA | eda-analyst | 탐색적 데이터 분석, 기술통계 |
| ST | statistician | 가설검정, 회귀, 시계열, 생존분석 (R) |
| ML | ml-engineer | 분류/회귀/클러스터링 (Python/sklearn) |
| DL | deep-learning | 딥러닝, 자연어처리, 이미지 (PyTorch) |
| GIS | gis-specialist | 공간분석, 지도시각화 (sf, folium) |
| TA | text-analyst | 텍스트마이닝, 감성분석, 토픽모델링 |
| VZ | visualizer | ggplot2, plotly, 대시보드 |
| RP | reporter | HWPX/PPTX 보고서 자동생성 |
| RA | realty-analyst | 경남 부동산시장 동향 월보, 인사이트 분석 |

### 웹앱 개발팀 (11명)
| ID | 에이전트 | 전문 영역 |
|----|---------|---------|
| RQ | requirements | 요구사항 분석, 기능명세, 사용자스토리 |
| UX | ux-designer | UI/UX 설계, 와이어프레임, 프로토타입 |
| FE | frontend | React/Vue/Streamlit 프론트엔드 |
| BE | backend | FastAPI/Flask/Django 백엔드 |
| DB | dba | DB 설계, 쿼리 최적화, 마이그레이션 |
| SC | security | 보안 검토, 취약점 분석, 인증/인가 |
| TU | tester-unit | 단위/통합 테스트, 커버리지 |
| QA | tester-qa | E2E 테스트, 품질보증, 버그리포트 |
| DO | devops | CI/CD, Docker, 배포 자동화 |
| TW | tech-writer | 기술문서, API 명세, 사용자 가이드 |
| SW | statworkbench | StatWorkbench 통계 패키지 개발/유지보수, SPSS 호환 |

### PPTX 제작팀 (5명)
| ID | 에이전트 | 전문 영역 |
|----|---------|---------|
| PP | pptx-planner | 발표 목적/청중/스토리라인 기획 |
| PC | pptx-content | 슬라이드별 콘텐츠 작성 |
| PD | pptx-designer | 디자인 시스템/레이아웃 설계 |
| PB | pptx-builder | python-pptx로 실제 파일 생성 |
| PR | pptx-reviewer | 내용/디자인/일관성 최종 검토 |

### StatWorkbench 전담 에이전트
> **소속**: 웹앱 개발팀 (lead-dev 산하) — 위 표의 SW 참조

#### SW 에이전트 상세 역할
- **경로**: `AGENTS_HOME\통계패키지\statworkbench`
- **기술 스택**: PySide6 GUI + scipy/statsmodels 통계 엔진
- **분석 모듈 담당**:
  - 로지스틱 회귀 (Logistic Regression)
  - 요인 분석 (Factor Analysis)
  - 군집 분석 (Cluster Analysis)
  - 생존 분석 (Survival Analysis)
  - 판별 분석 (Discriminant Analysis)
  - ANOVA 및 사후검정 (post-hoc)
- **시각화**: matplotlib/seaborn 내장 차트 빌더
- **SPSS 호환**: .sav 파일 임포트/익스포트 (pyreadstat 활용)
- **협업**: ST(statistician)와 통계 검증 공조, TU(tester-unit)와 모듈 테스트 공조
- **OUROBOROS 필수**: 신규 분석 모듈 추가 시 반드시 OUROBOROS 파이프라인 선적용

---

## ⚠️ 수직 지휘 체계 (모든 작업 필수 준수)

### 기본 원칙

> **지시는 위에서 아래로, 검토는 아래에서 위로.**
> OC → 팀 리드 → 담당 에이전트 순서를 절대 건너뛰지 않는다.

### 지시 흐름 (Top-down)

```
사용자 요청
    │
    ▼
[OC: orchestrator]
  - 요청 분석 및 팀 배정 결정
  - 팀 리드에게 목표·범위·기한 전달
  - status: working → 팀 리드 배정 완료 후 review 대기
    │
    ▼
[팀 리드: lead-data / lead-dev / lead-pptx]
  - OC 지시를 받아 세부 작업 분해
  - 담당 에이전트에게 단위 작업 배정
  - status: working → 팀원 배정 완료 후 팀원 결과 대기
    │
    ▼
[담당 에이전트: 실무 수행]
  - 팀 리드로부터 받은 단위 작업 수행
  - 완료 후 팀 리드에게 결과 제출
  - status: working → done
```

### 검토 흐름 (Bottom-up)

```
[담당 에이전트]
  - 작업 완료, 산출물 저장
  - status: done → 팀 리드에게 검토 요청
    │
    ▼
[팀 리드]
  - 산출물 품질·방향성 검토
  - 미흡 시: 담당 에이전트에게 재작업 지시 (팀 내 순환)
  - 합격 시: OC에게 상신
  - status: review → 검토 완료 후 done (상신)
    │
    ▼
[OC: orchestrator]
  - 팀 리드 상신 결과 종합 검토
  - 미흡 시: 해당 팀 리드에게 재검토 지시
  - 합격 시: 사용자에게 최종 결과 전달
  - status: review → done
    │
    ▼
사용자 — 최종 결과 수령
```

### 상태 업데이트 흐름 예시

```bash
# 1. OC가 지시 시작
python scripts/update_status.py orchestrator working "빅데이터 분석 요청 배정"

# 2. 팀 리드가 팀원 배정
python scripts/update_status.py lead-data working "EDA·통계 분석 팀원 배정"

# 3. 담당 에이전트 작업
python scripts/update_status.py eda-analyst working "탐색적 분석 수행"
python scripts/update_status.py eda-analyst done "EDA 완료, 리드 검토 요청"

# 4. 팀 리드 검토
python scripts/update_status.py lead-data review "EDA 결과 품질 검토"
python scripts/update_status.py lead-data done "검토 통과, OC 상신"

# 5. OC 최종 검토
python scripts/update_status.py orchestrator review "최종 결과 종합 검토"
python scripts/update_status.py orchestrator done "최종 승인, 사용자 전달"
```

### 건너뛰기 금지 규칙

| 금지 패턴 | 이유 |
|-----------|------|
| OC → 담당 에이전트 직접 지시 | 리드가 작업 맥락·품질 기준 모름 |
| 담당 에이전트 → OC 직접 상신 | 팀 내 1차 검토 없이 최종 검토 불가 |
| 리드 없이 팀원끼리 수평 연결 | 방향성 통제 불가, 결과 일관성 깨짐 |
| 사용자 → 담당 에이전트 직접 지시 | OC·리드 개입 없이 작업 맥락 유실 |

> **예외**: 긴급 버그 수정(hotfix) — OC가 명시적으로 허가한 경우에 한해 리드 경유 생략 가능. 단, 완료 후 리드·OC 사후 보고 필수.

---

## 워크플로우 파이프라인

### 빅데이터 분석 파이프라인

```
[OC: 분석 요청 접수 → lead-data에 목표·범위 지시]
    │
    ▼
[lead-data: 작업 분해 → 팀원 배정]
    │
    ├─▶ [DC: 데이터 수집]
    │       │
    │       ▼
    │   [CL: 데이터 정제]
    │       │ (병렬 배정)
    ├─▶ [EDA] [GIS] [TA]
    │       │ (병렬 배정)
    ├─▶ [ST] [ML] [DL]
    │       │
    │       ▼
    └─▶ [VZ: 시각화] → [RP: 보고서 생성]

    ── 검토 흐름 ──
    팀원 done → lead-data review → (합격) OC review → done
```

### 웹앱 개발 파이프라인

```
[OC: 개발 요청 접수 → lead-dev에 목표·범위 지시]
    │
    ▼
[lead-dev: 작업 분해 → 팀원 배정]
    │
    ├─▶ [RQ: 요구사항 분석]
    │       │
    │       ▼ (병렬)
    ├─▶ [UX: UI/UX 설계] + [DB: DB 설계]
    │       │ (병렬)
    ├─▶ [FE: 프론트] + [BE: 백엔드]
    │       │ (병렬)
    ├─▶ [SC: 보안검토] + [TU: 단위테스트]
    │       │
    └─▶ [QA: 품질보증] → [DO: 배포] + [TW: 문서화]

    ── 검토 흐름 ──
    팀원 done → lead-dev review → (합격) OC review → done
```

### PPTX 제작 파이프라인

```
[OC: 발표자료 요청 접수 → lead-pptx에 목표·청중·기한 지시]
    │
    ▼
[lead-pptx: 작업 분해 → 팀원 배정]
    │
    ├─▶ [PP: 기획·스토리라인]
    │       │ (병렬)
    ├─▶ [PC: 콘텐츠] + [PD: 디자인]
    │       │
    └─▶ [PB: 파일 생성] → [PR: 팀내 검토]

    ── 검토 흐름 ──
    PR done → lead-pptx review → (합격) OC review → done
```

### 부동산동향 월보 파이프라인 (realty-analyst 독자 운영)

```
[OC: 월보 생성 지시 → lead-data에 범위·기한 전달]
    │
    ▼
[lead-data: RA에 세부 작업 배정]
    │
    ├─▶ [RA: 데이터 수집·정제·병합]
    │       │ (협업)
    ├─▶ [TA: 뉴스·유튜브 텍스트 분석]
    ├─▶ [GIS: 지도 시각화]
    │       │
    └─▶ [RA: HTML 보고서 생성] → done

    ── 검토 흐름 ──
    RA done → lead-data review → (합격) OC review → 배포
```
> 기존 빅데이터 분석 파이프라인(DC→CL→EDA→ST→ML→VZ→RP)과 독립 운영. 교차 금지.

### StatWorkbench 개발/개선 파이프라인
```
[OUROBOROS: ouroboros init start "개선 사항"]
        |
[ambiguity score <= 0.2 달성 확인]
        |
[SW: StatWorkbench 분석/구현]
        | (병렬)
[ST: 통계 검증] + [TU: 단위 테스트]
        |
[QA: 품질 보증]
        |
[DO: 배포 (run.bat 빌드 및 패키징)]
```

### OUROBOROS 우선 적용 워크플로우 (신규 기능)
```
[OUROBOROS: interview → PRD 생성]
        |
[OC: 에이전트 배정]
        | (병렬)
[해당 전문 에이전트들]
        |
[OUROBOROS: evaluate → 수학적 검증]
        |
[OUROBOROS: evolve → 수렴 또는 재반복]
```

### 메타버스 라이브 사무실 개발 파이프라인 (metaverse.html)

**OC(오케스트레이터)와 LV(lead-dev)는 FE(frontend)에 위임하기 전 반드시 아래 체크리스트를 확인한다.**

```
[OC: 요청 분석 + 공간/투시 규칙 검토]  ← 사전 검토 (여기서 걸러야 함)
        |
[LV: lead-dev 설계 확인]
        |
[FE: frontend 구현]
        |
[python scripts/validate.py]           ← 자동 검증 (공간규칙 포함)
        |
[push]
```

#### OC/LV 사전 검토 체크리스트 (구현 전 필수 확인)

| 항목 | 규칙 | 위반 시 |
|------|------|---------|
| **투시/시점** | 위에서 내려다보는 탑뷰. 벽에 걸린 물체(화이트보드·스크린·간판)는 **측면 두께(< 15px)**만 표현 | 정면 콘텐츠 그리지 말 것 |
| **오브젝트 겹침** | 새 가구/오브젝트 추가 시 좌표가 기존 테이블·책상·복도를 침범하지 않는지 확인 | TX0·TY0 등 기준 좌표 계산 후 여백 확보 |
| **테이블 형태** | 회의 테이블은 `fillRoundedRect` (사각라운드) 유지 | `fillEllipse(TCX, TCY, TW, TH)` 패턴 금지 |
| **WALL_BODIES** | exec 파티션 높이 `h:t(7)` 이상 금지 (복도 y=96~112 차단됨). 문 위치(y=272~304) 포함 금지 | `h:t(6)-4` 이하로 제한 |
| **복도 좌표** | 상단 복도 y=96~112 / 하단 복도 y=240~256 범위에 가구·파티션 배치 금지 | 해당 y범위 완전 비워둘 것 |
| **POI 좌표** | POI가 테이블·책상 위에 겹치면 에이전트가 테이블 통과함 — 엣지 밖 배치 | walkCoord 공간에서 inWallBody 통과 확인 |
| **한자/일본어** | 코드 문자열·주석 어디에도 한자(U+6790 등)·일본어 절대 금지 | 즉시 수정 |

> **자동 검증**: `python scripts/validate.py` 가 위 규칙 중 투시·겹침·테이블형태·WALL_BODIES를 자동으로 검사한다.
> validate.py 실패 시 push 금지.

---

## 실시간 상태 업데이트 (필수)

에이전트가 작업을 시작/완료할 때 반드시 상태를 업데이트한다:

```bash
# 작업 시작 시
python scripts/update_status.py [agent_id] working "[작업 내용 한 줄]"

# 검토 중
python scripts/update_status.py [agent_id] review "[검토 내용]"

# 작업 완료 시
python scripts/update_status.py [agent_id] done "[완료 내용 한 줄]"
```

- `agent_id`: orchestrator, lead-data, data-collector, statworkbench 등 정확한 ID 사용
- 작업 내용은 20자 이내로 간결하게
- 이 명령은 어느 디렉토리에서든 실행 가능 (자동으로 파일 탐색)

---

## 에이전트 위임 방법

에이전트를 위임할 때 반드시 아래 절차를 따른다:

1. 해당 에이전트의 `agents/[id]/role.md` 읽기
2. `agents/[id]/memory.md` 읽기 (경험 로드)
3. Agent 도구로 위임:

```
Agent({
  description: "[에이전트명]: [작업 요약]",
  prompt: `
    # 역할 정의
    [role.md 전체 내용]

    # 축적된 경험
    [memory.md 내용]

    # 현재 작업
    [구체적 지시사항]

    # 산출물 요구사항
    [파일명, 형식, 저장 위치]
  `
})
```

4. 작업 완료 후 `memory.md` 업데이트 (새로운 경험 추가)

---

## 요청 분류 규칙

- "분석/데이터/통계/시각화/보고서/경남/공공" → 빅데이터 파이프라인
- "개발/웹/앱/화면/API/서비스" → 웹앱 파이프라인
- "발표/PPTX/슬라이드/프레젠테이션" → PPTX 파이프라인
- "통계패키지/StatWorkbench/SPSS/.sav/로지스틱/요인/군집/생존/판별/ANOVA" → SW 에이전트(개발팀 산하) + OUROBOROS (신규 기능 시)
- "개선/리팩토링/새 기능/시스템 설계" → OUROBOROS 파이프라인 우선 적용 후 해당 전문팀
- ambiguity score > 0.2 감지 시 → `ouroboros init start` 먼저
- 복합 요청 → 해당 팀 병렬 운영
- 단일 작업 → 해당 전문 에이전트 1명만 직접 위임

---

## GitHub 동기화
- Remote: https://github.com/your-github-username/agent.git
- Branch: master
- 자동 동기화: `.github/workflows/sync.yml`
- API Key 등 민감정보는 절대 커밋 금지

---

## 다중 PC 경로 독립 정책

### 핵심 원칙: 절대경로 하드코딩 금지

모든 에이전트는 파일 경로를 다음 우선순위로 결정한다:

1. **`config.local.json`** (머신별, gitignore) → 각 PC에서 최초 1회 설정
2. **환경변수 `AGENT_WORKSPACE_ROOT`** → 시스템 환경변수로 설정 가능
3. **자동 감지** → 스크립트 위치 또는 작업 디렉토리 기반

### 경로 사용 규칙

- 에이전트가 파일을 저장/읽을 때: **항상 `detect_paths` 유틸리티 호출 후 경로 결정**
- Python: `from scripts.detect_paths import load_config; cfg = load_config()`
- R: `source("scripts/detect_paths.R"); cfg <- load_config()`
- 모든 출력 파일: `cfg["paths"]["analysis_output"]` 등 논리적 경로 키 사용
- 하드코딩 예시 (금지): `AGENTS_HOME/data/raw/파일.csv`
- 올바른 예시: `Path(cfg["paths"]["raw_data"]) / "파일.csv"`

### 신규 PC 설정 절차

```bash
# 1. 저장소 클론
git clone https://github.com/your-github-username/agent.git
cd agent

# 2. 로컬 설정 파일 생성
cp config.example.json config.local.json
# config.local.json 열어서 이 PC의 실제 경로로 수정

# 3. 경로 확인
python scripts/detect_paths.py
```

### config.local.json 예시 (노트북용)

```json
{
  "machine_id": "노트북-삼성",
  "workspace_root": "D:/work/agents",
  "data_root": "D:/work/data",
  "output_root": "D:/work/output"
}
```

---

## StatWorkbench 관련 경로 및 설정

### 기본 경로
- **소스**: `AGENTS_HOME\통계패키지\statworkbench`
- **진입점**: `statworkbench\main.py`
- **실행**: `run.bat` (가상환경 활성화 후 main.py 호출)
- **빌드**: PyInstaller 또는 Nuitka로 단독 실행 파일 생성

### 모듈 구조 (SW 에이전트 관리 대상)
```
statworkbench/
  main.py              # PySide6 메인 윈도우
  modules/
    logistic.py        # 로지스틱 회귀
    factor.py          # 요인 분석
    cluster.py         # 군집 분석
    survival.py        # 생존 분석
    discriminant.py    # 판별 분석
    anova.py           # ANOVA + 사후검정
  ui/
    charts.py          # matplotlib/seaborn 차트 빌더
  io/
    spss_handler.py    # .sav 임포트/익스포트 (pyreadstat)
  tests/               # TU 에이전트 관리
```

### SPSS 호환 정책
- 입력: `.sav` 파일은 `pyreadstat.read_sav()` 사용
- 출력: `pyreadstat.write_sav()` 사용
- 인코딩: UTF-8 기반, SPSS 변수 레이블 한글 보존

---

## OUROBOROS 버전 정보

- **버전**: ouroboros-ai 0.39.0 (2026-05-19 설치 완료)
- **설치 방법**: `uv tool install "ouroboros-ai[claude]" --python 3.12`
  - pip 직접 설치 불가 (Python >=3.12 필요, 현 시스템 3.11) → uv 경유
  - uv 경로: `C:\Users\bc\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe`
  - ouroboros 실행 경로: `C:\Users\bc\.local\bin\ouroboros`
- **런타임 등록**: Claude Code 등록 완료 (`ouroboros setup --runtime claude`)
  - MCP 서버: `~/.claude/mcp.json`에 자동 등록
- **실행**: `PYTHONUTF8=1 ouroboros <command>` (Windows cp949 인코딩 우회 필수)
- **Python 환경**: uv 관리 가상환경 (`C:\Users\bc\AppData\Roaming\uv\tools\ouroboros-ai\`)
- **로그 위치**: 프로젝트 루트 `.ouroboros/` 디렉토리

### OUROBOROS 실행 예시 (StatWorkbench 신규 모듈)

```bash
# 1. 인터뷰 시작
ouroboros init start "StatWorkbench에 다중 대응 분석(MCA) 모듈 추가"

# 2. 소크라테스 인터뷰 → ambiguity score <= 0.2 달성까지 답변

# 3. PRD 생성
ouroboros pm

# 4. 자동 실행
ouroboros auto

# 5. 결과 검증
ouroboros evaluate

# 6. 상태 확인
ouroboros status
```

### OUROBOROS 실행 예시 (웹앱 신규 개발)

```bash
# 1. 인터뷰 시작
ouroboros init start "경남 공공데이터 실시간 모니터링 대시보드"

# 2. PRD 생성 후 에이전트 배정
ouroboros pm

# 3. 전체 파이프라인 자동 실행
ouroboros auto
```

---

## 중요: index.html 및 metaverse.html 수정 시 필수 확인 사항

### ⛔ 에이전트 아바타 이미지 보호 규칙 (절대 덮어쓰기 금지)

**2026-05-20 적용**: 대시보드의 에이전트 아바타가 이모지에서 AI 생성 PNG 이미지로 교체되었다.

**절대 금지 행위:**
- `.desk-avatar`, `.drawer-emoji`, `.card-emoji` 안의 `<img>` 태그를 이모지 텍스트로 되돌리는 행위
- `assets/avatars/` 디렉토리의 PNG 파일을 삭제하거나 덮어쓰는 행위
- `build_html.py` 또는 기타 빌드 스크립트가 이모지로 재생성하지 않도록 주의

**아바타 시스템 구조:**
```
assets/
  sprite_sheet.png          # 원본 스프라이트 시트 (6열×5행, 셀=229px)
  avatars/
    orchestrator.png        # 슬라이싱된 개별 아바타 (64×64px, 40px로 표시)
    lead-data.png
    lead-dev.png
    ... (총 30개)
  slice_sprite.py           # 재슬라이싱 스크립트 (스프라이트 시트 교체 시만 사용)
  apply_avatars.py          # HTML 교체 스크립트 (재실행 시만 사용)
```

**아바타를 교체하고 싶을 때 올바른 절차:**
1. 새 스프라이트 시트를 `assets/sprite_sheet.png`로 저장
2. `python assets/slice_sprite.py` 실행 (30개 PNG 재생성)
3. **별도 HTML 수정 불필요** — 이미 img 태그로 연결되어 있음

### 신규 에이전트 아바타 추가 절차

신규 에이전트가 생길 경우 아이콘을 1개씩 개별 생성하여 추가한다.

**Step 1: 사용자에게 아래 프롬프트 양식을 제공 (Claude가 채워서 전달)**

```
Create a single square icon for an AI agent avatar.
Canvas: 512×512 pixels.
Background: solid dark #161b22 (very dark navy-black).
Style: Fluent/Microsoft-style 3D emoji aesthetic — soft gradients, subtle shadows, slightly playful but professional. Icon fits within 400×400px centered in the 512×512 canvas.

Agent role: [에이전트 역할 설명 — 예: "GIS Specialist — analyzes spatial data and creates geographic maps"]
Visual concept: [아이콘 시각 설명 — 예: "Green folding map with a glowing location pin on top"]
Color tone: [주조색 — 예: "Green tones with gold pin highlight"]

Match the visual style of these reference icons from the same set:
- Orchestrator: gold bullseye with glowing rings
- ML Engineer: electric-blue neural network node diagram
- Security Expert: red hexagonal shield with padlock

Output: single icon only, no text labels, no border, no grid lines.
```

**Step 2: 사용자가 이미지를 전달하면 Claude가 수행할 작업**
1. 이미지 해상도 및 품질 검증 (512×512 확인)
2. `assets/avatars/[agent-id].png` 로 64×64 리사이즈 저장
3. `index.html`에서 해당 에이전트의 `desk-avatar` / `drawer-emoji` / `card-emoji` img 태그 추가
4. `assets/slice_sprite.py`의 AGENTS 목록에 신규 ID 추가 (순서 기록용)
5. push

**신규 에이전트 아바타 저장 스크립트 (즉시 실행)**
```python
# python assets/add_avatar.py [agent-id] [image-path]
from PIL import Image
from pathlib import Path
import sys

agent_id = sys.argv[1]   # 예: realty-analyst
src_path = sys.argv[2]   # 예: C:\Users\...\image.png

img = Image.open(src_path).convert("RGBA")
img = img.resize((64, 64), Image.LANCZOS)
out = Path(f"assets/avatars/{agent_id}.png")
img.save(out, "PNG", optimize=True)
print(f"저장 완료: {out}")
```

### index.html 수정 전 반드시 확인 (가장 빠른 방법)
```bash
python scripts/validate.py        # 전체 검증 자동 실행
python scripts/validate.py --fix  # 문제 자동 수정
```

**단일 ID 요소 — 각각 정확히 1개만 존재해야 함**
- `id="toast"` (JS 알림 div)
- `id="tab-editor"` (MD 에디터 탭)
- `id="agent-drawer"` (에이전트 상세 패널)
- `id="editor-textarea"` (MD 에디터 입력창)

- **절대 금지**: 위 ID 요소를 body 끝에 append 방식으로 추가하는 행위
- **올바른 방법**: 기존 요소를 찾아 replace

---

## 시스템 실행 및 복구 절차

### 원클릭 실행 (재부팅 후 또는 최초 설치)
```
열기.bat  ←  이것만 실행하면 됨
```
- `.venv` 없으면 자동 생성 및 패키지 설치 (최초 1회만 오래 걸림)
- API 서버(8765) + 정적 서버(8000) 자동 시작
- 브라우저 자동 열림

### 증상별 복구

#### 증상 1: "로컬 서버 실행 필요" 배너가 보임
→ API 서버(포트 8765)가 꺼진 것. 해결:
```
열기.bat  ←  재실행
```
또는 수동으로:
```
.venv\Scripts\python.exe -m uvicorn scripts.api_server:app --port 8765 --workers 1
```

#### 증상 2: 에이전트 클릭해도 모달이 안 열림 (JS 오류)
→ `index.html` JS 구문 오류. 확인:
```
python -c "
import re
from pathlib import Path
content = Path('index.html').read_text(encoding='utf-8')
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
Path('_patches/test.js').write_text(scripts[0], encoding='utf-8')
"
node --check _patches/test.js
```
오류 발생 시 원인은 `update_md_content.py` 실행 후 IIFE 소멸.
복구: pollAgentStatus IIFE를 `const MD_CONTENT = {...};` 바로 다음에 삽입:
```javascript
// 에이전트 상태 실시간 폴링 (5초마다)
(function pollAgentStatus() {
  function update() {
    fetch('agent_status.json?t=' + Date.now())
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var agents = data.agents || {};
        Object.keys(agents).forEach(function(id) {
          var dot = document.getElementById('dot-' + id);
          if (!dot) return;
          var st = (agents[id] || {}).status || 'idle';
          dot.className = 'status-dot' + (st !== 'idle' ? ' ' + st : '');
        });
      })
      .catch(function() {});
  }
  update();
  setInterval(update, 5000);
})();
```

#### 증상 3: memory.md 수정했는데 대시보드에 반영 안 됨
→ sync.py 실행 누락. 해결:
```
python scripts/sync.py
git add -A && git commit -m "sync: memory 갱신" && git push origin master
```

#### 증상 4: push 거부 (rejected)
→ 다른 PC에서 먼저 push한 것. 해결:
```
git pull --rebase origin master
git push origin master
```
**절대 금지**: `git push --force`, `git checkout --theirs` 단순 교체

#### 증상 5: validate.py 실패
```
python scripts/validate.py --fix  ← 자동 수정 시도
python scripts/validate.py        ← 재확인
```
26/26(또는 전체) 통과 후에만 push 허용

---

## 반복 장애의 근본 원인 분석

### 왜 같은 문제가 반복되는가

| 원인 | 구체적 사례 | 예방책 |
|------|------------|--------|
| **정규식 greedy 버그** | `update_md_content.py`의 `re.DOTALL + .*` 가 IIFE까지 삼킴 | 줄 단위 교체 방식 사용 (현재 수정 완료) |
| **Python 문자열 안의 `\n` 혼동** | 삽입 코드에서 `\n`이 실제 개행으로 변환 → JS 문자열 오류 | 삽입 전 `node --check`로 반드시 검증 |
| **3-PC 병렬 작업** | 각 PC에서 서로 다른 상태로 push → 머지 충돌 | 작업 전 `git pull --rebase`, 작업 후 즉시 push |
| **sync.py 실행 누락** | `memory.md` 수정 후 push → 대시보드에서 "(내용 없음)" | memory.md 수정 시 sync.py 실행 필수 (자동화 예정) |
| **검증 없이 파일 배포** | `열기.bat` 한국어 echo 오류를 테스트 없이 배포 | 배포 전 `cmd /c 열기.bat` 직접 실행 확인 필수 |
| **머지 충돌 단순 교체** | `git checkout --theirs` 로 상대방 코드 무조건 채택 → 작업물 소멸 | 충돌 시 반드시 양쪽 내용 확인 후 수동 머지 |

---

## AI가 절대 하면 안 되는 것들

> 이 섹션은 Claude, GPT, Gemini 등 모든 AI 어시스턴트에게 적용된다.

### 코드 수정 관련

1. **`re.DOTALL` + greedy `.*`로 JS 구문 블록 교체 절대 금지**
   - `const MD_CONTENT = {...}` 같은 패턴을 정규식으로 교체할 때 DOTALL greedy 사용 금지
   - 반드시 줄 단위(line-by-line) 교체 방식 사용

2. **수정 후 `node --check` 없이 push 금지**
   - index.html JS 수정 후에는 반드시 스크립트 추출 → `node --check` 통과 확인

3. **Python 문자열에서 `\n` 포함 JS 코드 삽입 시 반드시 검증**
   - Python triple-quoted string 안의 `\n`은 실제 개행문자 → JS 단일 따옴표 문자열에서 오류 발생
   - 삽입 후 반드시 정규식 `/\n/g` 등 escape sequence 온전한지 확인

4. **`git push --force` 절대 금지**

5. **`git checkout --theirs` / `--ours` 단순 교체 절대 금지**
   - 반드시 양쪽 내용 확인 후 수동 머지

6. **`memory.md` 파일 삭제 금지**

7. **`config.local.json` 커밋·push 금지** (머신별 민감 설정)

8. **절대경로 하드코딩 금지** (`AGENTS_HOME\...` 형태)

### bat 파일 관련

9. **`echo` 안에 한국어 절대 사용 금지**
   - cmd.exe는 UTF-8 bat 파일의 한국어 echo를 명령어로 오인 → 오류
   - 모든 echo 문은 영어 또는 ASCII만 사용

10. **`if (...) (...)` 블록 안에 중첩 괄호 포함 echo 금지**
    - `echo (최초 1회만 실행)` → cmd가 `)` 를 블록 종료로 오인
    - `:label` / `goto` 구조 사용

11. **bat 파일 수정 후 `cmd /c 파일명.bat` 직접 실행 확인 필수**
    - 이론상 맞아도 실제 테스트 없이 배포 금지

### 동기화 관련

12. **`memory.md` 수정 후 `python scripts/sync.py` 실행 없이 push 금지**
    - 대시보드 MD 에디터에서 "(내용 없음)" 표시 발생

13. **push 전 `python scripts/validate.py` 43/43 통과 확인 필수**

14. **push 전 `git pull --rebase origin master` 실행 필수** (다중 PC 환경)

---

## 신규 에이전트 추가 지침

> **연쇄 체크리스트 (10단계)**: `AGENTS_HOME\AGENT_ADD_PROTOCOL.md` — 이것을 따르지 않으면 플랫폼 불일치 발생
> 상세 생성 가이드: `AGENTS_HOME\AGENT_CREATION_GUIDE.md`

### ⚠️ 핵심 원칙: 에이전트 추가는 단일 파일 작업이 아니다

에이전트 하나가 연결된 구성요소: role.md → metaverse.html → index.html(데스크+에디터+동기화탭) → agent_status.json → llm_provider.py → qa_gate.py → run_pipeline.py → CLAUDE.md → push

**하나라도 빠지면** = 대시보드에 표시 안 됨 / 상태 추적 안 됨 / 라이브 사무실에 캐릭터 없음

### 추가 기준 — 아래 모두 충족 시에만 추가
- 기존 에이전트 중 담당 가능한 에이전트가 없다
- 기존 에이전트의 role.md 확장으로는 해결이 안 된다
- 이 업무가 앞으로도 반복될 가능성이 있다 (1회성이면 OC가 직접 처리)

### 에이전트 유형
| 유형 | 설명 | 선택 기준 |
|------|------|---------|
| **기능형** (권장) | 전문 역량 기반, 여러 프로젝트 재사용 | 역량이 앞으로도 반복적으로 필요할 때 |
| **프로젝트형** | 특정 프로젝트 전담, 종료 후 해체 | 기술이 너무 특수해 재사용 가능성이 없을 때 |

**프로젝트형 에이전트 종료 시 인수인계 필수**:
- 프로젝트 핵심 경험·교훈을 `memory.md`에 최종 기록
- 관련 기능형 에이전트(가장 유사한 에이전트)의 `memory.md`에 핵심사항 이관
- 이관 완료 후 `role.md` 상단에 `[ARCHIVED: YYYY-MM-DD]` 태그 추가
- 시스템에서 제거하더라도 폴더와 MD 파일은 보존 (기록 자산)

### 추가 절차 요약 (세부사항은 AGENT_ADD_PROTOCOL.md 참조)
1. STEP 1: 폴더 + role.md (# 이름) + memory.md
2. STEP 2: metaverse.html AGENTS 배열 + PIPELINE + HANDOFF_MSGS
3. STEP 3: index.html 데스크 카드 HTML
4. STEP 4: assets/avatars/[id].png + apply_all_avatars.py 목록
5. STEP 5: scripts/llm_provider.py 키워드
6. STEP 6: scripts/qa_gate.py 검수 기준
7. STEP 7: scripts/run_pipeline.py 파이프라인
8. STEP 8: CLAUDE.md 팀 편성표 업데이트
9. STEP 9: sync.py → build_html.py → validate.py (43/43)
10. STEP 10: git pull → git add -A → commit → push

### 사용자에게 반드시 물어볼 5가지 (임의 생성 금지)
1. 이 에이전트의 핵심 업무를 한 문장으로 설명해 주세요.
2. 이번 한 번만 필요한가요, 앞으로도 반복적으로 필요한가요? (유형 결정)
3. 어느 팀에 배정하시겠습니까? (빅데이터/웹앱/PPTX/지원)
4. 한글 이름과 영문 ID를 지정해 주시거나, 제안한 것을 확인해 주세요.
5. 메타버스 캐릭터 외형(피부색, 머리색)을 지정하시겠습니까, 자동 배정할까요?
