# CHANGELOG

## 2026-06-04 (페이퍼클립·이슈·GitHub 양방향 연동 대폭 업그레이드)
### Phase 1 — 이슈 코어 정합성
- metaverse.html: 이슈 패널을 stale localStorage → /api/issues 서버 fetch로 전환
- index.html: 깨진 syncGitHubIssues(구버전 localStorage 오염) 제거
- sync.yml: 트리거 경로 status.json → agent_status.json 수정
### Phase 2 — 페이퍼클립 ↔ 이슈 연동
- /api/instruct: create_issue·priority 옵션 — 지시 시 GNI 이슈 자동 생성·연결(in_progress),
  task에 (GNI-N) 삽입 → working/review/done 전환 시 자동전이
- index.html 지시 모달·metaverse 지시 패널: '이슈로 등록' 체크박스 + 우선순위
### Phase 3 — GitHub Issues 양방향 동기화 (서버+PAT)
- scripts/github_sync.py(신규): urllib 기반, GNI ↔ GitHub Issues 양방향(last-write-wins),
  gni-id 마커·github_number 링크, status→state+labels 매핑
- /api/github/status, /api/github/sync 엔드포인트 (토큰값 미노출, asyncio.to_thread)
- config(example/local.example): github 섹션. config.local.json은 gitignore(토큰 안전)
- validate.py: PAT 커밋 방지 체크(92체크)
### Phase 4 — UI·문서 마감
- 이슈 상세 패널: github_number 있으면 GitHub 링크
- sync 탭: GitHub 연동 상태 카드 + PAT 설정 가이드
- metaverse: 지시→이슈 생성 시 말풍선·로그 피드백

## 2026-05-29 (6차 전방위 개선)
### 기능 추가
- index.html: Overview 탭 fresh 데이터 fetch, 모바일 반응형 CSS (480/768px)
- index.html: 초기 로딩 오버레이 (진행바 포함)
- index.html: 텍스트 ellipsis 처리 (v2-log-text, card-desc, modal-task-text)
- metaverse.html: disperseAgents 좌표 수정, agentPanel 스크롤
- scripts: requirements.txt 보완, POI 다양화, WS heartbeat

### 스크립트 개선
- llm_provider.py: mock 반응 다양화 (done 액션 추가, 에이전트별 개성 접두어)
- llm_provider.py: 키워드 랜덤 선택으로 반응 다양성 향상
- start_all.bat: 포트 충돌 감지(8000/8765), 가상환경 확인, 브라우저 자동 열기
- validate.yml: tee 로그 + GITHUB_STEP_SUMMARY 결과 요약 출력

## 2026-05-29 (5차 개선)
### 기능 추가
- /api/git-status 엔드포인트 신규 (브랜치/커밋/미커밋/ahead-behind)
- scripts/generate_reports_index.py 신규 (reports 자동 목록화)
- renderSync() 실질적 시스템 상태 대시보드로 확장
- metaverse: 팀 구역 한글 레이블 8개, 터치 탭으로 패널 열기
- validate.py 89개 체크로 확장

## 2026-05-29 (원격 개선)
### 기능 추가
- metaverse: 걷기 애니메이션 개선 (발 움직임, 속도 38)
- metaverse: TV 슬라이드 5초, 팀 회의 쿨다운 5분
- api_server: /api/approval rejected 시 review 유지 버그 수정
- api_server: /api/agents/{id} HTTPException 404 수정

## 2026-05-29
### 개선
- index.html: API_BASE 상수화, 소통 구조 실시간화
- metaverse.html: 품질 개선 (console.log 정리, 패널 강화)
- api_server.py: 타임존 명시, 환경변수 설정화
- docs 정비: LIVE_OFFICE_PROGRESS.md 업데이트, adding_new_agent.md 최신화, CHANGELOG.md 생성

### 탭 간결화
- index.html 탭 약어+간결화 적용
- 이슈 미니차트 제거 (성능 개선)

### 버그 수정 (metaverse.html)
- TV 슬라이드 % 2 버그 제거
- ambient 레이어 통합
- 핀치줌 증분 계산 수정
- agentPanel left 364px (사이드바 겹침 수정)
- 날짜 자정 미갱신 수정

---

## 2026-05-28
### 기능 추가
- role.md 8개 에이전트 대폭 보강 (43~64줄 → 177~231줄)
- GitHub Actions weekly_report.yml 추가 (매주 월 09:00 KST)
- validate.py role.md 최소 라인 체크 추가 (83개 체크로 확장)
- 매뉴얼 탭 v4.0 전면 재작성 (11개 섹션)
- UI/UX 개선: CSS 트랜지션, 토스트 알림, SLA 애니메이션, 단축키

### 버그 수정
- 메모리 검색 파라미터 q → query 수정
- 타임스탬프 Z → +00:00 UTC 변환
- monthly_report.py 인코딩 utf-8-sig 통일
- BroadcastChannel close() 타이밍 수정

---

## 2026-05-19
### 기능 추가 (Track A~E)
- Track A: 팀 바닥 색상 밝게 (모던 오피스 스타일)
- Track B: 에이전트 이동 최소화, 데스크 체류 40-180s
- Track C: 사이드바 파이프라인·완료 섹션 신설
- Track D: 회의실 테이블 통과 금지 강화
- Track E: 대시보드 상태 도트 + 5초 폴링 (29명 에이전트 카드)

### 추가 개선
- 이름태그 위치: 머리 위 → 발 아래 (py+26), 말풍선과 완전 분리
- 디자인팀 통일: PPTX팀 → 디자인팀 (metaverse + index 동시)
- 에이전트 패널 실시간: 패널 열려 있는 동안 3초마다 status/task 갱신
- 미니맵 존 색상: 새 PALETTE 반영 + 하층 4개 구역 분리 표시
- 회의실 테이블: 고급 월넛 + 의자 14개 (fillRoundedRect)
- 서버실: 리뷰룸 대체, 서버랙 + 네트워크 장비

### Kimi Code 업데이트 반영
- race condition 방지 + CORS 보안 + QA 실검증 (scripts/)
- 활성 에이전트 스트립 세로폭 개선 (flex column, scroll)
- 에이전트 반응 채팅 패널 저장 (instructAgent → localStorage)
- memory.md 8개 에이전트 귀촌지 분석 경험 추가

---

## 2026-05-18
### 초기 구현
- Phaser 3 픽셀아트 사무실 렌더링 (40x22 타일, 48px/tile)
- PALETTE 컬러 시스템 구축
- 복도 기반 이동 (computeWaypoints)
- 카메라 줌/드래그 (마우스 휠 0.4~2.5x, 우클릭 드래그)
- 에이전트 상태 폴링 (3초마다 agent_status.json)
- 픽셀아트 에이전트 캐릭터 29명
- SLA 경고, 리더보드, 일일요약, 검색, 일괄지시, 메타버스 연동
- stale working 자동 복귀 (2시간 타임아웃)
- monthly_report.py 신규
- rotate.yml GitHub Actions 추가
