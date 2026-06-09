---
name: method-opus-plan-css-migration
type: method
domain: 작업원칙
updated: 2026-06-08
---

# Opus Plan + 병렬 탐색으로 대규모 CSS 통일 작업하는 패턴

## 결론

10개 이상 파일에 흩어진 CSS를 디자인시스템으로 통일할 때는
**Opus Plan mode → 병렬 탐색 에이전트 → 단계적 구현** 순서가 최적이다.

## 이유

- 파일이 많고 위반 패턴이 다양해 한 번에 파악 불가 → 탐색을 에이전트에 위임해 컨텍스트 절약
- 상태색(도착임박 빨강, 저상버스 초록 등) 보존 여부 등 판단이 필요한 결정이 많음 → Opus가 설계 단계에서 미리 정리
- 구현 순서(의존성) 잘못되면 CSS 변수 미정의 → 색상 사라짐 버그 → Phase 순서 사전 설계 필수

## 적용법 (표준 5단계)

### Step 1. 탐색 (Explore 에이전트, 병렬)
- 에이전트 1: 각 페이지 CSS 블록 현황 + 위반 항목 목록화
- 에이전트 2(선택): 기존 토큰 정의·진입점 파악
- 결과물: 페이지별 위반 표 + 보존 항목 목록

### Step 2. 설계 (Opus Plan 에이전트)
입력: 탐색 결과 전체 + 디자인 규칙(design.md MUST/MUST NOT)
출력:
- 토큰 추가 목록(Phase 0 선행 필수 항목)
- 금지색 대체 전략(CSS var vs Python 리터럴 구분)
- 상태색 보존 목록 + 예외 처리 방침
- Phase 순서(의존성 기준)

### Step 3. 계획 승인 후 Phase 순서대로 구현
```
Phase 0 → 1 → 2 → 3 → 4 → 5
(토큰확장) (메인앱) (저위험) (금지색) (헤더정책) (카드)
```
Phase 0(토큰)을 건너뛰면 이후 var(--xxx) 참조가 미정의 → 색상 누락.

### Step 4. 검증 grep (0건 확인 후 커밋)
```bash
rg -n "7c3aed|9333ea|4338ca|6d28d9" pages/ styles/ app.py
rg -n "Noto Sans KR" pages/ styles/ app.py
rg -n "linear-gradient\(160deg" pages/
rg -n "\.stApp\s*\{" pages/
```

### Step 5. pytest + 런타임 점검 후 커밋·push

## 핵심 함정 (이번 세션에서 발견)

**1. 진입점 2개 문제**
Streamlit 앱에서 `pages/*.py`와 `app.py`(메인)가 각각 다른 CSS 파일을 로드.
메인은 COMMON_CSS(:root 토큰 정의처)를 기본 로드하지 않아 CSS 변수 미적용.
해결: `st.markdown(COMMON_CSS, ...)` BASE_CSS 직전에 선주입.

**2. Python 리터럴에 CSS var() 불가**
`st.bar_chart(color="...")`, 연락처 배열 등 Python 값은 CSS var() 미지원.
이런 곳은 반드시 HEX 리터럴("#1D4ED8")로 직접 교체.
CSS 클래스 내부와 인라인 style="" 속성은 var() 사용 가능.

**3. 상태색 보존 판단 기준**
"기능적 의미 있음(상태 코딩) = 보존 / 단순 테마색 = 교체"
예) 배터리 그린 헤더 → 배터리 단계색과 연결된 기능색 → 보존
예) 고용 틸 헤더 → 단순 차별화 테마색 → 블루로 통일

**4. 다항목 카드 배열**
8개 기능 카드처럼 색상이 구분 목적인 경우, 퍼플/인디고 항목만 교체.
나머지(초록·주황·파랑 등 허용 hue)는 정보 구분을 위해 보존.

## 관련

- [[design-apple-hig-eum]] — 이음지도 구체 적용 세부(토큰·검증·대체 전략)
- [[project-eumjido-streamlit-ops]] — 이음지도 Streamlit 운영 주의사항
