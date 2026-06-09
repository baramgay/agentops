---
name: design-apple-hig-eum
type: method
domain: 이음지도
updated: 2026-06-08
---

# 이음지도 Apple HIG 디자인시스템 적용 방법

## 결론

이음지도 전 페이지에 Apple HIG 기반 단일 디자인시스템을 통일 적용했다(2026-06-08, commit 7fb989b).
핵심 원칙: **단일 진실 소스(`styles/base.py`)**, **CSS 토큰 변수 전면화**, **상태색 절대 보존**.

## 이유

- 페이지마다 하드코딩된 hex, 퍼플/인디고(`#7c3aed` 등), 다색 그라디언트, `Noto Sans KR` 잔재가 산재
- 시각 일관성 부재 → 장애인 사용자 혼란 및 접근성 저하
- design.md(Apple HIG 15섹션) 신설 후 AI 안내 페이지만 먼저 적용, 나머지 9개 페이지+메인은 미적용 상태

## 파일 구조 (진입점 2개 주의)

| 진입점 | CSS 파일 | 대상 |
|---|---|---|
| `pages/*.py` | `styles/base.py` COMMON_CSS | 9개 서브 페이지 |
| `app.py` (메인) | `styles/app_css.py` BASE_CSS | 메인 허브 페이지 |

**중요**: app.py는 COMMON_CSS(:root 토큰 정의처)를 기본으로 로드하지 않으므로,
`st.markdown(COMMON_CSS, ...)` 선주입 후 BASE_CSS를 로드해야 토큰이 메인에도 적용된다.

## CSS 토큰 (styles/base.py :root)

```css
--blue-600:#2563EB; --blue-700:#1D4ED8; --blue-900:#1E3A8A;
--green-600:#16A34A; --green-700:#15803D;
--amber-600:#D97706; --red-600:#DC2626;
--teal-600:#0891B2; --teal-700:#0E7490;
--surface-base:#F4F6FB; --surface-raised:#FFFFFF;
--sidebar-bg:#0F2744; --sidebar-text:#CBD5E1; --sidebar-heading:#93C5FD;
--font-sans:'Pretendard','Apple SD Gothic Neo',...
```

## 적용 규칙 (MUST / MUST NOT)

**MUST:**
- 헤더: `linear-gradient(135deg, var(--blue-700) 0%, var(--blue-900) 100%)`
- 배경: `var(--surface-base)` (`.stApp` 하드코딩 금지)
- 폰트: `var(--font-sans)` (Pretendard — Noto Sans KR 금지)
- 사이드바: base.py 전역 규칙 1회 정의(`--sidebar-bg`), 각 페이지에서 중복 선언 금지

**MUST NOT:**
- 퍼플/인디고 계열: `#7c3aed`, `#9333ea`, `#4338ca`, `#6d28d9`, `#4c1d95`, `#5b21b6`
- 다색 그라디언트(`linear-gradient(160deg, #1a1f2e 0%, #16213e 100%)` 등 사이드바 구형 패턴)
- `Noto Sans KR` 폰트 참조 (pages/styles 범위)

**상태색 절대 보존 (기능적 의미):**
- 저상버스·충전기 초록: `#16A34A` (= `--green-600`)
- 도착 임박 빨강: `#DC2626` (= `--red-600`)
- 배터리 단계색: 초록→앰버→빨강 (9_배터리_범위.py)
- 차트 다중 구분색 (시각화 구분 필요)

## 퍼플 대체 전략

| 용도 | 기존 | 대체 |
|---|---|---|
| 단일 강조·헤더·카드 보더 | `#7c3aed` | `var(--blue-600)` |
| 복지시설 카테고리 배지 | `#ede9fe/#5b21b6` | `var(--blue-50)/var(--blue-700)` |
| KPI 카드 `purple` 클래스 | `#7c3aed` | `var(--teal-700)` |
| 음향신호기 차트 | `#7c3aed` | `"#0E7490"` (Python 리터럴) |
| AI 안내 카드 | `#9333ea` | `"#1D4ED8"` |
| 고용 카드 | `#4338ca` | `"#0E7490"` |

**Python 차트 리터럴 주의**: `st.bar_chart(color=...)` 인자는 CSS var 불가 → 반드시 HEX 리터럴로 교체.

## 9_배터리 헤더 예외

배터리 페이지 헤더는 **그린 유지** (`var(--green-600)`).
헤더·안전반경 원·충전기 마커까지 전부 그린으로 묶인 기능적 색 코딩이므로 블루 통일 금지.

## 검증 grep (적용 후 모두 0건이어야 함)

```bash
rg -n "7c3aed|9333ea|4338ca|6d28d9|4c1d95|5b21b6" pages/ styles/ app.py
rg -n "Noto Sans KR" pages/ styles/ app.py
rg -n "linear-gradient\(160deg" pages/
rg -n "\.stApp\s*\{" pages/
```

## 스킬

`/apply-apple-design` 스킬로 이 체크리스트를 자동화 가능.
참고: [[project-eumjido-streamlit-ops]], [[design.md 위치: webapp/design.md]]
