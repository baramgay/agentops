# 개발 파이프라인 가이드

> DAG 기반 병렬 개발 워크플로우 + QA 게이트 + 에이전트 협업 메모리
> 작성일: 2026-05-19

---

## 개요

개발팀(10명)의 작업을 DAG(방향성 비순환 그래프) 구조로 관리하여 **병렬 처리**를 극대화하고, **각 단계별 QA 게이트**를 통해 품질을 보장합니다. 에이전트 간 산출물은 **협업 메모리**를 통해 전달됩니다.

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           병렬 개발 파이프라인                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1        Phase 2          Phase 3          Phase 4              │
│  ┌─────────┐   ┌──────────┐    ┌──────────┐    ┌─────────────┐       │
│  │requirements│ │ux-designer│    │frontend  │    │security     │       │
│  │          │   │          │    │          │    │             │       │
│  └────┬────┘   └────┬─────┘    └────┬─────┘    └──────┬──────┘       │
│       │             │               │                  │              │
│       ▼             ▼               ▼                  ▼              │
│  QA Gate 1     QA Gate 2      QA Gate 3         QA Gate 4             │
│  (lead-dev)    (lead-dev)     (tester-unit)     (tester-qa)           │
│                                                                         │
│       │             │               │                  │              │
│       ▼             ▼               ▼                  ▼              │
│            ┌──────────┐    ┌──────────┐    ┌─────────────┐           │
│            │dba       │    │backend   │    │tester-unit  │           │
│            │          │    │          │    │             │           │
│            └──────────┘    └──────────┘    └─────────────┘           │
│                                                                         │
│  Phase 5              Phase 6                                          │
│  ┌─────────────┐     ┌──────────────┐                                 │
│  │tester-qa    │     │devops        │                                 │
│  │             │     │              │                                 │
│  └──────┬──────┘     └──────┬───────┘                                 │
│         │                    │                                         │
│         ▼                    ▼                                         │
│  QA Gate 5            QA Gate 6                                        │
│  (lead-dev)           (lead-dev)                                       │
│         │                    │                                         │
│         └────────┬───────────┘                                         │
│                  ▼                                                     │
│           ┌──────────────┐                                             │
│           │tech-writer   │                                             │
│           │              │                                             │
│           └──────────────┘                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 파이프라인 단계

| Phase | 에이전트 | 병렬 | 작업 내용 | QA 검토자 |
|---|---|---|---|---|
| 1 | requirements | ✗ | 요구사항 분석 및 기능 정의 | lead-dev |
| 2 | ux-designer, dba | ✓ | UI/UX 설계, DB 스키마 설계 | lead-dev |
| 3 | frontend, backend | ✓ | 프론트엔드/백엔드 개발 | tester-unit |
| 4 | security, tester-unit | ✓ | 보안 검토, 단위 테스트 | tester-qa |
| 5 | tester-qa | ✗ | 통합 QA, E2E 테스트 | lead-dev |
| 6 | devops, tech-writer | ✓ | 배포, 문서 작성 | lead-dev |

---

## 사용법

### 1. 파이프라인 실행

```bash
# 전체 파이프라인 실행 (개발팀)
cd /mnt/d/업무/agents
python3 scripts/run_pipeline.py dev

# DRY-RUN (계획만 확인)
python3 scripts/run_pipeline.py dev --dry-run

# 특정 Phase만 실행
python3 scripts/run_pipeline.py dev --phase 2

# QA 게이트 없이 실행
python3 scripts/run_pipeline.py dev --no-qa-gate
```

### 2. QA 게이트 수동 실행

```bash
# Phase 2 QA 검증
python3 scripts/qa_gate.py --phase 2 --team dev

# 개별 에이전트 QA
python3 scripts/qa_gate.py --agent frontend

# 자동 통과 (데모용)
python3 scripts/qa_gate.py --agent frontend --auto-pass
```

### 3. 에이전트 협업 메모리

```bash
# 산출물 핸드오프 기록
python3 scripts/agent_collab.py handoff \
  --from requirements --to ux-designer \
  --artifact "docs/requirements.md" \
  --type "document" \
  --desc "라이브 사무실 기능 확장 요구사항"

# 동기화 포인트 생성 (Phase 3 대기)
python3 scripts/agent_collab.py sync \
  --phase 3 --team dev \
  --agents frontend backend

# 동기화 완료 표시
python3 scripts/agent_collab.py sync \
  --phase 3 --team dev --complete frontend

# 전체 협업 메모리 요약
python3 scripts/agent_collab.py list
```

---

## 품질 기준

### 요구사항 분석 (requirements)
- 기능 요구사항이 5W1H로 명확히 기술
- 비기능 요구사항(성능, 보안, 확장성) 정의
- 유즈케이스 다이어그램 또는 사용자 스토리 작성
- 수용/거부 기준 명확 정의
- 이해관계자 승인 서명

### UI/UX 설계 (ux-designer)
- 와이어프레임이 모든 주요 화면 커버
- 디자인 시스템(색상, 타이포그래피, 컴포넌트) 정의
- 사용자 흐름(UX flow) 명확 표현
- 반응형/적응형 디자인 고려
- 접근성(a11y) 가이드라인 반영

### DB 설계 (dba)
- ER 다이어그램 작성
- 정규화 3NF 이상 적용
- 인덱스 전략 문서화
- 백업/복구 전략 정의
- 마이그레이션 스크립트 버전 관리

### 프론트엔드 (frontend)
- 코드 리뷰 1회 이상 통과
- 단위 테스트 커버리지 70% 이상
- 린트 오류 0건
- 크로스 브라우저 테스트 완료
- Lighthouse 점수 80점 이상

### 백엔드 (backend)
- API 문서(Swagger/OpenAPI) 작성
- 단위 테스트 커버리지 70% 이상
- 에러 핸들링 및 로깅 구현
- DB 쿼리 성능 EXPLAIN 검증
- 보안 취약점 스캔 통과

### 보안 (security)
- OWASP Top 10 점검표 완료
- 인증/인가 로직 pentest 통과
- CORS 및 CSP 정책 적절 설정
- 민감 데이터 암호화 적용
- 보안 이슈 트래킹 문서화

### 단위 테스트 (tester-unit)
- 테스트 케이스 요구사항 기반 작성
- 모든 테스트 CI 통과
- 모킹(mock) 적절 사용
- 경계값 및 예외 케이스 커버
- 테스트 커버리지 리포트 생성

### 통합 QA (tester-qa)
- E2E 시나리오 사용자 스토리 기반 작성
- 회귀 테스트 자동화
- 버그 심각도 분류 명확
- 성능/부하 테스트 완료
- 릴리즈 노트 작성

---

## 파일 구조

```
scripts/
├── run_pipeline.py    # DAG 파이프라인 실행기
├── qa_gate.py         # QA 품질 게이트
├── agent_collab.py    # 에이전트 협업 메모리
└── update_status.py   # 단일 에이전트 상태 업데이트 (기존)

agent_status.json      # 런타임 상태 (자동 생성)
agent_collab.json      # 협업 메모리 (자동 생성)
```

---

## 라이브 사무실 시각화

### 반영된 기능
1. **활성 파이프라인 아크**: working 상태 변경 시 금색 데이터 흐름 생성
2. **완료 트리거**: done 상태 시 다음 단계로 스파크 + 컨페티
3. **QA 검토 링**: review 상태 에이전트 주변 노란색 링 (펄스)
4. **대기 링**: waiting 상태 에이전트 주변 주황색 링
5. **Phase 인디케이터**: 사이드바에 현재 Phase 및 진행률 표시

### metaverse.html 수정 위치
| 기능 | 라인 | 설명 |
|---|---|---|
| qaRingGfx | 534 | QA 링 graphics 레이어 |
| spawnFlow active | 2724-2743 | 활성 경로 금색, 10개 파티클 |
| update QA 링 | 2855-2875 | review/waiting 상태 링 |
| update 파이프라인 아크 | 2882-2920 | 활성 경로 두께/알파 증가 |
| fetchStatus spawnFlow | 2820-2822 | working 시 다음 단계 아크 |
| fetchStatus done 트리거 | 2823-2831 | done 시 다음 단계 스파크 |
| flow 렌더링 강화 | 3052-3070 | 활성 흐름 꼬리 효과 |
| Phase 인디케이터 HTML | 218-229 | 사이드바 UI |
| Phase 계산 JS | 2850-2870 | fetchStatus 내 phase 업데이트 |

---

## 알려진 제한사항

1. **QA 자동화 한계**: 현재 `--auto-pass` 없이는 체크리스트를 수동으로 채점해야 함. 실제 CI/CD 연동 시 자동 점수 계산 필요.
2. **동기화 포인트**: `agent_collab.py sync`는 메모리 기반이므로 프로세스 재시작 시 초기화됨. SQLite 연동 고려.
3. **파이프라인 롤백**: QA 불통과 시 자동 롤백은 미구현. 수동으로 `update_status.py`로 상태 변경 필요.
4. **race condition**: `agent_status.json` 동시 접근 문제는 여전히 존재. 프로덕션 시 SQLite로 마이그레이션 권장.
