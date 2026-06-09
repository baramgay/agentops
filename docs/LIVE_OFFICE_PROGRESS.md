# 라이브 사무실 (metaverse.html) 개선 진행 상황

> 마지막 업데이트: 2026-05-29 (TRACK A~E 대규모 개선 + 버그 4건 수정 + 탭 간결화 + 감사 기반 추가 개선 진행 중) | 작성 PC: 사무실-데스크탑

다른 PC나 노트북에서 이어서 작업하려면 이 파일을 먼저 읽고 시작하세요.
작업 전 반드시 `git pull origin master` 실행.

---

## 현재 완료된 기능 목록

### 핵심 시스템
| 기능 | 완료일 | 비고 |
|------|--------|------|
| Phaser 3 픽셀아트 사무실 렌더링 | 2026-05-18 | 40×22 타일, 48px/tile |
| PALETTE 컬러 시스템 | 2026-05-18 | const PALETTE = {} (라인 310) |
| 복도 기반 이동 (computeWaypoints) | 2026-05-18 | 가로/세로만, 복도 경유 강제 |
| 카메라 줌/드래그 | 2026-05-18 | 마우스 휠 0.4~2.5x, 우클릭 드래그 |
| 에이전트 상태 폴링 | 2026-05-18 | 3초마다 agent_status.json 읽기 |

### 시각화
| 기능 | 완료일 | 비고 |
|------|--------|------|
| 픽셀아트 에이전트 캐릭터 (29명) | 2026-05-18 | 2.5x 스케일, 소품 포함 |
| 이름태그 (발 아래) | 2026-05-19 | py+26, origin(0.5,0), 말풍선 겹침 없음 |
| Task Strip (발 아래) | 2026-05-19 | py+56, working 중만 표시 |
| 상태 링 글로우 | 2026-05-18 | working pulsing |
| 파이프라인 베지에 아크 | 2026-05-18 | 활성 에이전트 간 흐름 |
| 미니맵 | 2026-05-19 | 사이드바 canvas, updateMinimap() |

### 공간 구성
| 구역 | 위치 | 완료일 |
|------|------|--------|
| EXECUTIVE FLOOR (4개 리드 사무실) | x=0-23, y=0-6 | 2026-05-19 |
| MEETING ROOM (회의실) | x=24-39, y=0-6 | 2026-05-19 |
| 주 복도 (베이지) | y=6 전체 | 2026-05-19 |
| DATA ANALYTICS 팀 | x=0-18, y=7-14 | 2026-05-18 |
| WEB DEV LAB | x=21-39, y=7-14 | 2026-05-18 |
| 중앙 복도 (x=19-20, 베이지) | x=19-20, y=7-14 | 2026-05-18 |
| 하단 복도 (베이지) | y=15 전체 | 2026-05-19 |
| TRAINING ROOM (교육실) | x=0-7, y=16-21 | 2026-05-19 |
| DESIGN STUDIO (디자인팀) | x=8-23, y=16-21 | 2026-05-19 |
| SERVER ROOM (서버실) | x=24-31, y=16-21 | 2026-05-19 |
| BREAK ROOM | x=32-39, y=16-21 | 2026-05-18 |

### 인터랙션
| 기능 | 완료일 | 비고 |
|------|--------|------|
| 에이전트 클릭 → 상세 패널 | 2026-05-18 | 픽셀 얼굴+소품, 채팅, MD 링크 |
| 채팅/지시 기능 | 2026-05-18 | localStorage 저장, Enter 전송 |
| role.md / memory.md 링크 | 2026-05-18 | 패널에서 바로 열기 |
| 패널 슬라이드 애니메이션 | 2026-05-19 | CSS transition |
| 집합 명령 버튼 | 2026-05-18 | callGathering() 연결 |
| 지시 E2E 실행 (말풍선+이동+상태+API) | 2026-05-19 | CHANGELOG_2026-05-19.md 참조 |
| 병렬 개발 파이프라인 | 2026-05-19 | DAG 위상 정렬, 6개 Phase |
| QA 품질 게이트 | 2026-05-19 | 체크리스트 기반 5점 만점 |
| 에이전트 협업 메모리 | 2026-05-19 | 핸드오프 + 동기화 포인트 |
| 활성 파이프라인 아크 강화 | 2026-05-19 | 금색 활성 경로, 스파크 효과 |
| QA 검토/대기 링 | 2026-05-19 | review=노랑, waiting=주황 펄스 |
| Phase 인디케이터 | 2026-05-19 | 사이드바 Phase 1/6 ~ 6/6 |

---

## 2026-05-28 TRACK A~E 대규모 개선

| 트랙 | 내용 | 상태 |
|------|------|------|
| Track A | role.md 8개 에이전트 대폭 보강 (43~64줄 → 177~231줄) | ✅ 완료 |
| Track B | UI/UX 개선: CSS 트랜지션, 토스트 알림, SLA 애니메이션, 단축키 | ✅ 완료 |
| Track C | 매뉴얼 탭 v4.0 전면 재작성 (11개 섹션) | ✅ 완료 |
| Track D | GitHub Actions weekly_report.yml 추가 (매주 월 09:00 KST) | ✅ 완료 |
| Track E | validate.py role.md 최소 라인 체크 추가 (83개 체크로 확장) | ✅ 완료 |

### 2026-05-28 버그 4건 수정
| 항목 | 수정 내용 |
|------|-----------|
| 메모리 검색 파라미터 | q → query 수정 |
| 타임스탬프 | Z → +00:00 UTC 변환 |
| monthly_report.py 인코딩 | utf-8-sig 통일 |
| BroadcastChannel close() | 타이밍 수정 |

## 2026-05-29 탭 간결화 + 추가 개선

| 항목 | 내용 |
|------|------|
| 탭 약어 | 긴 탭 제목 → 약어+간결화 |
| 이슈 미니차트 | 제거 (성능 개선) |
| API_BASE 상수화 | index.html 내 URL 상수 처리 |
| metaverse 품질 | console.log 정리, 패널 강화 |
| api_server 강화 | 타임존 명시, 환경변수 설정화 |

> 현재 진행 중: 감사 기반 추가 개선 (API 상수화, metaverse 품질, api_server 강화)

## 2026-05-19 Claude Code 종합 개선 (Track A~E / 이전 버전)

| 트랙 | 내용 | 상태 |
|------|------|------|
| Track A | 팀 바닥 색상 밝게 (모던 오피스) | ✅ data 0x1E4A7A, dev 0x1E4A28, pptx 0x2E1A5A |
| Track B | 에이전트 이동 최소화 | ✅ POI 이동 2%↓, 데스크 체류 40-180s |
| Track C | 사이드바 파이프라인·완료 섹션 | ✅ 파이프라인 현황 + 최근 완료 3개 |
| Track D | 회의실 테이블 통과 금지 강화 | ✅ meetingZone(x≥24) 복도 경유 강제 |
| Track E | 대시보드 상태 도트 + 5초 폴링 | ✅ 29개 에이전트 카드 실시간 dot |

### 추가 개선 (2026-05-19)
| 항목 | 내용 |
|------|------|
| 이름태그 위치 | 머리 위 → 발 아래(py+26), 말풍선과 완전 분리 |
| 디자인팀 통일 | PPTX팀 → 디자인팀 (metaverse + index 동시) |
| 작업 중인 에이전트 | Kimi 버전 유지 + a.id 누락 수정 + 흰색 폰트 |
| 에이전트 패널 실시간 | 패널 열려 있는 동안 3초마다 status/task 갱신 |
| 미니맵 존 색상 | 새 PALETTE 반영 + 하층 4개 구역 분리 표시 |
| agent_status.json | UTF-8 재인코딩 (garbled 태스크 정리) |
| index.html body 태그 | 누락 복원 (화면 안 나오던 버그 수정) |
| 집합 명령 테두리 | 섹션 컨테이너 border 추가 |
| 로그 공간 | min-height 260px, max-height 420px |
| 회의실 테이블 | 고급 월넛 + 의자 14개 (fillRoundedRect) |
| 서버실 | 리뷰룸 대체, 서버랙 + 네트워크 장비 |
| 소품-라벨 겹침 | 교육실·대시보드·서버실·커피카운터 y+18 |

## 2026-05-19 Kimi Code 업데이트 반영
- race condition 방지 + CORS 보안 + QA 실검증 (scripts/)
- 활성 에이전트 스트립 세로폭 개선 (flex column, scroll)
- 에이전트 반응 채팅 패널 저장 (instructAgent → localStorage)
- memory.md 8개 에이전트 귀촌지 분석 경험 추가

---

## 알려진 버그 / 제한사항

| 항목 | 상태 | 우선순위 |
|------|------|---------|
| 에이전트 충돌 회피 없음 (같은 위치 겹침 가능) | 미해결 | 낮음 |
| 모바일/터치 미지원 | 미해결 | 낮음 |
| agent_status.json 쓰기 API 없음 (읽기 전용) | 구조적 한계 | — |
| MD 파일 수정은 로컬에서만 가능 (브라우저 보안) | 구조적 한계 | — |
| TV 슬라이드 % 2 버그 | ✅ 2026-05-29 수정 | — |
| ambient 레이어 중복 | ✅ 2026-05-29 통합 | — |
| 핀치줌 증분 계산 오류 | ✅ 2026-05-29 수정 | — |
| agentPanel 사이드바 겹침 (left 미조정) | ✅ 2026-05-29 수정 (364px) | — |
| 날짜 자정 미갱신 | ✅ 2026-05-29 수정 | — |

---

## 다음 PC에서 이어서 할 작업

### 즉시 확인 필요
1. `git pull origin master` 후 `python -m http.server 8000` (agents 폴더에서)
2. `http://localhost:8000/metaverse.html` 브라우저 열기
3. `http://localhost:8000/index.html` 대시보드 확인
4. F12 콘솔 에러 없는지 확인
5. 팀 공간 색상이 밝고 구분되는지 확인 (데이터=파란, 개발=초록, 디자인=보라)
6. 에이전트 클릭 → 패널에 현재 status/task 표시 및 3초마다 갱신 확인
7. 미니맵 하층 4구역 구분 색상 확인

### 추가 개선 후보 (미시작)
- [ ] 터치/모바일 핀치줌 지원
- [ ] 에이전트 간 충돌 회피 (타일 기반)
- [ ] 작업 현황 히트맵 시각화
- [ ] 소리 효과 (상태 변경 시 효과음)
- [ ] index.html과 더 깊은 연동 (드래그로 작업 할당 등)
- [ ] 다크/라이트 테마 전환 (PALETTE 동적 변경)

---

## 현재 시스템 현황 (2026-05-29 기준)

| 항목 | 수치 |
|------|------|
| 에이전트 수 | 33명 |
| validate.py 검증 체크 수 | 83개 이상 |
| GitHub Actions | daily_report.yml, rotate.yml, sync.yml, validate.yml, weekly_report.yml |
| role.md 최소 라인 기준 | 80줄 이상 |

---

## 주요 코드 위치 참조

```
metaverse.html (~3053줄)
├── const PALETTE = {}           라인 ~310    색상 시스템
├── const AGENTS = [...]         라인 ~312    에이전트 29명 정의
├── const POI_LIST = [...]       라인 ~279    방문 가능 지점
├── class MainScene
│   ├── create()                 라인 ~467    초기화
│   ├── drawFloor()              라인 ~573    바닥 렌더링
│   ├── drawWalls()              라인 ~663    벽/문 렌더링
│   ├── drawFurniture()          라인 ~753    가구 렌더링
│   ├── drawSignage()            라인 ~1205   구역 표지판
│   ├── createAgent()            라인 ~1560   에이전트 생성
│   ├── computeWaypoints()       라인 ~2222   복도 기반 경로 계산
│   ├── startWalkTo()            라인 ~2271   이동 시작
│   ├── pickNextIdleBehavior()   라인 ~2261   유휴 행동 결정
│   ├── fetchStatus()            라인 ~2664   agent_status.json 폴링
│   ├── updateMinimap()          라인 ~?      미니맵 갱신
│   ├── refreshAgentPanel()      라인 ~2450   패널 UI 갱신
│   ├── drawAccessoryOnCanvas()  라인 ~2513   패널 얼굴 소품 렌더링
│   └── update(time, dt)         라인 ~2762   매 프레임 갱신
└── window.callGathering()       라인 ~맨끝  집합 명령
```

---

## 동기화 규칙

- **작업 시작 전**: `git pull origin master`
- **작업 완료 후**: `git add metaverse.html docs/LIVE_OFFICE_PROGRESS.md && git commit -m "..." && git push origin master`
- **config.local.json은 절대 push 금지** (PC별 로컬 경로)
- **이 파일을 수정할 때**: 날짜와 작성 PC 업데이트 필수

---

## PC별 설정

| PC | machine_id | git user.email | 로컬 경로 |
|----|-----------|----------------|----------|
| 사무실 데스크탑 | 사무실-데스크탑 | your-email@example.com | D:/업무/agents |
| 노트북 | 노트북-삼성 | your-email@example.com | D:/work/agents (설정 필요) |
