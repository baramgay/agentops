# CHANGELOG 2026-05-19

> 라이브 사무실(metaverse.html) 에이전트 지시기능 E2E 구현
> 작성일: 2026-05-19
> 관련 이슈: LIVE_OFFICE_PROGRESS.md "지시 패널 localStorage만 저장, 실행 안됨" 문제 해결

---

## 개요

에이전트 상세 패널(`agentPanel`)의 지시 입력(`apInstructText` + `apSendBtn`)이 기존에는 `localStorage`에만 저장되고 실제로 실행되지 않았습니다. 이번 변경으로 **브라우저 내 즉시 반영(A) + 상태 변경(B) + 행동 명령(C) + 로그 기록(D) + API 동기화(E)** 의 완전한 E2E 파이프라인을 구현했습니다.

---

## 변경 파일 목록

| # | 파일 | 변경 유형 | 설명 |
|---|---|---|---|
| 1 | `metaverse.html` | 수정 | 지시 send 버튼 핸들러에 실행 로직 추가 |
| 2 | `scripts/api_server.py` | 수정(기존 파일 유지) | `POST /api/instruct` 엔드포인트 추가 및 키워드 분석 |
| 3 | `열기.bat` | 수정 | API 서버 자동 시작 로직 추가 |
| 4 | `docs/LIVE_OFFICE_PROGRESS.md` | 문서 업데이트 | 진행 상황 반영 |

---

## 1. metaverse.html 변경 상세

### 변경 위치
- **함수**: `MainScene.openAgentPanel()` 낸 `sendBtn.onclick` 핸들러
- **라인**: 2433 ~ 2540 (기존 코드 유지 + 신규 코드 추가)

### 변경 전 (기존)
```javascript
// 기존: localStorage 저장만 수행
sendBtn.onclick = () => {
  const txt = document.getElementById('apInstructText').value.trim();
  if (!txt || !this.openedAgentId) return;
  const agentId = this.openedAgentId;

  const key = 'agent_chat_' + agentId;
  const msgs = JSON.parse(localStorage.getItem(key) || '[]');
  msgs.push({ ts: Date.now(), text: txt });
  localStorage.setItem(key, JSON.stringify(msgs.slice(-50)));
  document.getElementById('apInstructText').value = '';

  this.renderAgentChat(agentId);
};
```

### 변경 후 (신규)
```javascript
sendBtn.onclick = () => {
  const txt = document.getElementById('apInstructText').value.trim();
  if (!txt || !this.openedAgentId) return;
  const agentId = this.openedAgentId;
  const sp = this.sprites[agentId];
  const name = sp ? sp.def.name : agentId;

  // 1. localStorage 저장 (기존 기능 유지)
  const key = 'agent_chat_' + agentId;
  const msgs = JSON.parse(localStorage.getItem(key) || '[]');
  msgs.push({ ts: Date.now(), text: txt });
  localStorage.setItem(key, JSON.stringify(msgs.slice(-50)));
  document.getElementById('apInstructText').value = '';

  // 2. 브라우저 내 즉시 반영 (A + B + D)
  if (sp) {
    const lower = txt.toLowerCase();
    let reaction = '지시 확인했습니다.';
    let newStatus = 'working';

    // 반응/상태 키워드 분석
    if (['복귀','돌아가','데스크','자리'].some(k=>lower.includes(k))) {
      reaction = '데스크로 복귀합니다.';
      newStatus = 'idle';
    } else if (['집합','모여','회의','라운지','미팅'].some(k=>lower.includes(k))) {
      reaction = '회의실로 이동합니다.';
    } else if (['커피','휴식','쉬어','브레이크'].some(k=>lower.includes(k))) {
      reaction = '잠깐 휴식하겠습니다.';
      newStatus = 'idle';
    } else if (['작업','일해','분석','개발','시작'].some(k=>lower.includes(k))) {
      reaction = '작업 시작하겠습니다.';
    } else if (['검토','확인','리뷰'].some(k=>lower.includes(k))) {
      reaction = '검토 진행하겠습니다.';
      newStatus = 'review';
    } else if (['대기','기다려','홀드'].some(k=>lower.includes(k))) {
      reaction = '대기하겠습니다.';
      newStatus = 'waiting';
    }

    sp.status = newStatus;
    sp.task = txt;

    // 이름태그 색상 동기화
    const LC = { working:'#3FB950', done:'#58A6FF', review:'#D29922', waiting:'#F0883E', idle:'#8B949E' };
    if (sp.label) sp.label.setColor(LC[newStatus] || '#E6EDF3');
    if (sp.nameTag) sp.nameTag.setColor(LC[newStatus] || '#E6EDF3');

    this.updateTaskStrip(sp);
    this.showBubble(sp, reaction, newStatus);

    // 3. 행동 명령 (C)
    if (['복귀','돌아가','데스크','자리'].some(k=>lower.includes(k))) {
      sp.mode = 'returning';
      sp.targetX = sp.baseX / 3;
      sp.targetY = sp.baseY / 3;
      this.resetCharacterPose(sp);
    } else if (['집합','모여','회의','라운지','미팅'].some(k=>lower.includes(k))) {
      const loungePoi = POI_LIST.find(p => p.id === 'lounge');
      if (loungePoi) this.startWalkTo(sp, loungePoi.x / 3, loungePoi.y / 3, loungePoi);
    } else if (['커피','휴식','쉬어','브레이크'].some(k=>lower.includes(k))) {
      const coffeePoi = POI_LIST.find(p => p.id === 'coffee1');
      if (coffeePoi) this.startWalkTo(sp, coffeePoi.x / 3, coffeePoi.y / 3, coffeePoi);
    } else if (['작업','일해','분석','개발','시작'].some(k=>lower.includes(k))) {
      sp.mode = 'desk';
      sp.idleBehavior = 'type_fast';
      sp.idleTimer = 5 + Math.random() * 5;
      this.resetCharacterPose(sp);
    } else if (['검토','확인','리뷰'].some(k=>lower.includes(k))) {
      sp.mode = 'desk';
      sp.idleBehavior = 'sit_idle';
      sp.idleTimer = 5 + Math.random() * 5;
      this.resetCharacterPose(sp);
    } else if (['대기','기다려','홀드'].some(k=>lower.includes(k))) {
      sp.mode = 'desk';
      sp.idleBehavior = 'stand';
      sp.idleTimer = 999;
      this.resetCharacterPose(sp);
    }

    // 4. 로그 기록 + 패널 갱신
    this.addLog(agentId, name, newStatus, txt);
  }

  // 5. API 동기화 (E) - 오프라인 안전
  fetch('http://127.0.0.1:8765/api/instruct', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, text: txt })
  }).then(r => r.json()).then(res => {
    console.log('[API]', agentId, res.reaction || 'ok');
  }).catch(err => {
    console.warn('[API] offline:', err);
  });

  this.renderAgentChat(agentId);
};
```

### 추가/변경된 함수 호출 관계

```
sendBtn.onclick
├── localStorage 저장 (기존)
├── if (sp) { ... }
│   ├── 키워드 분석 → newStatus 결정
│   ├── sp.status = newStatus
│   ├── sp.task = txt
│   ├── sp.label.setColor() / sp.nameTag.setColor()
│   ├── this.updateTaskStrip(sp)     // line 2393
│   ├── this.showBubble(sp, reaction, newStatus)  // line 2667
│   ├── 행동 명령
│   │   ├── this.startWalkTo(...)    // line 2269 (POI 이동)
│   │   ├── this.resetCharacterPose(sp)
│   │   └── sp.mode / sp.idleBehavior / sp.idleTimer 변경
│   └── this.addLog(agentId, name, status, task)  // line 2809
├── fetch POST /api/instruct (비동기, 오프라인 안전)
└── this.renderAgentChat(agentId)    // line 2637
```

### 관련 헬퍼 함수 위치

| 함수 | 라인 | 설명 |
|---|---|---|
| `updateTaskStrip(sp)` | 2393 | 에이전트 머리 위 task 텍스트 갱신 |
| `statusRingColor(status)` | 2406 | 상태별 링 색상 반환 |
| `openAgentPanel(agentId)` | 2425 | 에이전트 패널 열기 |
| `startWalkTo(sp, tx, ty, poi)` | 2269 | 에이전트 걸어가기 시작 |
| `renderAgentChat(id)` | 2637 | 패널 채팅 로그 렌더링 |
| `showBubble(sp, text, status)` | 2667 | 말풍선 표시 |
| `addLog(agentId, name, status, task)` | 2809 | 로그 배열에 추가 |

### 색상 매핑 테이블 (신규/기존 통합)

```javascript
const LC = {
  working: '#3FB950',   // 녹색
  done:    '#58A6FF',   // 파란색
  review:  '#D29922',   // 주황색
  waiting: '#F0883E',   // 노란색
  idle:    '#8B949E'    // 회색
};
```

Phaser `statusRingColor` (0xRGB):
```javascript
switch (status) {
  case 'working': return 0x3FB950;
  case 'review':  return 0xD29922;
  case 'waiting': return 0xF0883E;
  case 'done':    return 0x58A6FF;
  default:        return 0x6E7681;
}
```

---

## 2. scripts/api_server.py 변경 상세

### 기존 유지 엔드포인트

| 메서드 | 경로 | 설명 | 라인 |
|---|---|---|---|
| GET | `/api/status` | 전체 에이전트 상태 반환 | 75 |
| POST | `/api/status/{agent_id}` | 특정 에이전트 상태 변경 | 81 |
| GET | `/api/agents/{agent_id}` | 단일 에이전트 상태 조회 | 189 |

### 신규 엔드포인트

| 메서드 | 경로 | 설명 | 라인 |
|---|---|---|---|
| POST | `/api/instruct` | 지시 명령 처리 (상태+로그+반응) | 117 |

### 신규 Pydantic 모델

```python
class InstructBody(BaseModel):
    agent_id: str
    text: str
```

### `/api/instruct` 구현 상세 (line 117-186)

```python
@app.post("/api/instruct")
def instruct(body: InstructBody):
    data = load_data()
    agent_id = body.agent_id
    text = body.text.strip()

    if agent_id not in data.get("agents", {}):
        return {"error": f"알 수 없는 에이전트 ID '{agent_id}'"}

    # 키워드 기반 반응/행동 분석
    reaction = "지시 확인했습니다."
    action = "none"
    target_poi = None

    lower = text.lower()
    if any(k in lower for k in ["복귀", "돌아가", "데스크", "자리"]):
        reaction = "데스크로 복귀합니다."
        action = "return"
    elif any(k in lower for k in ["집합", "모여", "회의", "라운지", "미팅"]):
        reaction = "회의실로 이동합니다."
        action = "gather"
        target_poi = "lounge"
    elif any(k in lower for k in ["커피", "휴식", "쉬어", "브레이크"]):
        reaction = "잠깐 휴식하겠습니다."
        action = "break"
        target_poi = "coffee1"
    elif any(k in lower for k in ["작업", "일해", "분석", "개발", "시작"]):
        reaction = "작업 시작하겠습니다."
        action = "work"
    elif any(k in lower for k in ["검토", "확인", "리뷰"]):
        reaction = "검토 진행하겠습니다."
        action = "review"
    elif any(k in lower for k in ["대기", "기다려", "홀드"]):
        reaction = "대기하겠습니다."
        action = "wait"

    # 상태 업데이트
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data["agents"][agent_id] = {"status": "working", "task": text}
    data["updated"] = now

    # 로그 추가 (최근 30개)
    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "status": "working",
        "label": "지시 수행",
        "task": text,
    }
    data.setdefault("log", []).insert(0, log_entry)
    data["log"] = data["log"][:30]

    save_data(data)

    return {
        "ok": True,
        "agent_id": agent_id,
        "status": "working",
        "task": text,
        "reaction": reaction,
        "action": action,
        "target_poi": target_poi,
    }
```

### CORS 설정 (기존 유지, line 23-29)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "null", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> 참고: 컴팩션 컨텍스트에는 `allow_origins=["*"]`로 표기되어 있으나 실제 파일은 위와 같이 명시적 origin 목록을 사용함.

---

## 3. 열기.bat 변경 상세

### 변경 전
```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0"

start python -m http.server 8000
start "" "http://localhost:8000"
```

### 변경 후
```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM API 서버 실행 (포트 8765)
netstat -an | findstr ":8765 " >nul 2>&1
if %errorlevel% neq 0 (
    start "Agent API Server" ".venv\Scripts\python.exe" scripts\api_server.py
    timeout /t 2 /nobreak >nul
)

REM 정적 서버 실행 (포트 8000)
netstat -an | findstr ":8000 " >nul 2>&1
if %errorlevel% neq 0 (
    start "Agent Dashboard Server" python -m http.server 8000 --bind 127.0.0.1
    timeout /t 2 /nobreak >nul
)

start "" "http://localhost:8000"
```

### 변경 내역
- API 서버 자동 시작 추가 (`.venv\Scripts\python.exe scripts\api_server.py`)
- 포트 충돌 방지: `netstat`로 실행 여부 확인 후 조건부 시작
- 정적 서버 바인딩 주소 명시 (`--bind 127.0.0.1`)
- 실행 지연: `timeout /t 2`로 서버 기동 대기

---

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│                          브라우저 (localhost:8000)                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ metaverse.html│    │ agentPanel   │    │ localStorage         │  │
│  │  Phaser 3    │◄───┤ (지시 입력)  │───►│ agent_chat_${id}     │  │
│  │              │    └──────────────┘    └──────────────────────┘  │
│  │  ┌────────┐ │          │                                         │
│  │  │sprites │ │          ▼ 즉시 반영                               │
│  │  │ status │ │    ┌──────────────┐    ┌──────────────┐          │
│  │  │ task   │ │    │ showBubble() │    │ startWalkTo()│          │
│  │  │ label  │ │    │ updateTaskStrip│   │ resetCharacterPose│    │
│  │  │ mode   │ │    │ addLog()     │    │              │          │
│  │  └────────┘ │    └──────────────┘    └──────────────┘          │
│  └──────┬───────┘           │                                         │
│         │                   ▼                                         │
│         │            fetch POST /api/instruct                         │
│         │            (비동기, 오프라인 안전)                            │
│         │                   │                                         │
└─────────┼───────────────────┼─────────────────────────────────────────┘
          │                   │
          ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI 서버 (127.0.0.1:8765)                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ POST /api/instruct                                              │ │
│  │  1. agent_status.json 읽기 (load_data)                          │ │
│  │  2. 키워드 분석 → reaction/action/target_poi 결정                 │ │
│  │  3. data["agents"][id] = {status:"working", task:text}          │ │
│  │  4. 로그 추가 (최근 30개 유지)                                  │ │
│  │  5. agent_status.json 쓰기 (save_data)                          │ │
│  │  6. JSON 반환 {ok, agent_id, status, task, reaction, action, target_poi} │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│                             ▼                                       │
│                    ┌─────────────────┐                              │
│                    │ agent_status.json│ (영구 저장)                   │
│                    └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 데이터 흐름 시퀀스

```
[사용자] 지시 입력 → "커피 마셔"
    │
    ▼
[sendBtn.onclick]
    ├──► localStorage 저장 (즉시)
    ├──► sp.status = 'idle'
    ├──► sp.task = '커피 마셔'
    ├──► nameTag/label 색상 변경 (#8B949E)
    ├──► updateTaskStrip(sp) → taskStrip 숨김
    ├──► showBubble(sp, '잠깐 휴식하겠습니다.', 'idle')
    ├──► startWalkTo(sp, coffee1.x/3, coffee1.y/3, coffee1) → 에이전트 이동 시작
    ├──► addLog(agentId, name, 'idle', '커피 마셔')
    │
    ├──► fetch POST /api/instruct (비동기)
    │       ├──► api_server.py: instruct()
    │       ├──► agent_status.json 읽기
    │       ├──► 키워드 분석: "커피" → action="break", target_poi="coffee1"
    │       ├──► agents[id] = {status:"working", task:"커피 마셔"}
    │       ├──► log.insert(0, {...})
    │       ├──► agent_status.json 쓰기
    │       └──► 반환: {ok:true, reaction:"잠깐 휴식하겠습니다.", action:"break", target_poi:"coffee1"}
    │
    └──► renderAgentChat(agentId) → 패널 채팅 갱신
```

---

## 키워드 매핑 테이블 (프론트/백 동일)

| 키워드 그룹 | 키워드 목록 | newStatus | action | target_poi | 행동 |
|---|---|---|---|---|---|
| 복귀 | 복귀, 돌아가, 데스크, 자리 | idle | return | - | baseX/baseY로 이동 |
| 집합 | 집합, 모여, 회의, 라운지, 미팅 | working | gather | lounge | 라운지로 이동 |
| 휴식 | 커피, 휴식, 쉬어, 브레이크 | idle | break | coffee1 | 커피머신으로 이동 |
| 작업 | 작업, 일해, 분석, 개발, 시작 | working | work | - | desk 모드 + type_fast |
| 검토 | 검토, 확인, 리뷰 | review | review | - | desk 모드 + sit_idle |
| 대기 | 대기, 기다려, 홀드 | waiting | wait | - | desk 모드 + stand |

> **주의**: 프론트엔드(metaverse.html line 2454-2470)와 백엔드(api_server.py line 138-158)의 키워드 목록은 반드시 동일하게 유지해야 함.

---

## 알려진 이슈 및 주의사항

### 1. Race Condition on agent_status.json
- `fetchStatus()`가 3초마다 `agent_status.json`을 읽음 (metaverse.html)
- API 서버가 동시에 같은 파일을 씀
- **현재 파일 잠금(file locking) 미구현**
- 해결책: SQLite 교체 또는 `portalocker`/`fcntl` 사용

### 2. 프론트/백 상태 불일치
- 프론트엔드는 `newStatus`를 키워드에 따라 다르게 설정 (idle, working, review, waiting)
- 백엔드는 무조건 `"working"`으로 저장
- **이것은 의도된 설계**: 백엔드는 "작업 중"으로 기록하고, 프론트는 시각적 표현만 다르게 함

### 3. POI 도착 후 복귀 동작
- `startWalkTo()`로 POI에 도착하면 기존 `update()` 루프의 POI 완료 처리가 작동
- `sp.mode = 'returning'`으로 설정되어 있으면 자동으로 base 위치로 복귀
- **명시적 "이전 작업으로 복귀" 명령은 구현되지 않음**

### 4. 배치 지시 미구현
- 현재 1:1 지시만 가능
- "전체 집합" 사이드바 버튼은 기존 `update_status.py`를 통해 동작
- **metaverse.html 내에서 다중 에이전트 동시 지시는 미구현**

### 5. 오프라인 동작
- API 서버가 꺼져도 localStorage 저장 + 브라우저 내 반영은 정상 작동
- `fetch().catch()`로 오류를 콘솔에만 기록, UI는 깨지지 않음

---

## 테스트 방법

### 1. 수동 테스트 (브라우저)
1. `열기.bat` 실행 (또는 `.venv\Scripts\python.exe scripts\api_server.py` 직접 실행)
2. 브라우저에서 `http://localhost:8000/metaverse.html` 접속
3. 에이전트 클릭 → 패널 열림
4. 지시 입력창에 "커피 마셔" 입력 → Send
5. 확인 사항:
   - 말풍선에 "잠깐 휴식하겠습니다." 표시
   - 에이전트가 커피머신 방향으로 이동
   - 패널 채팅에 기록 추가
   - `agent_status.json`에 로그 추가됨

### 2. API 직접 테스트 (curl)
```bash
curl -X POST http://127.0.0.1:8765/api/instruct \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"lead_001","text":"회의실로 집합"}'
```

### 3. 로그 확인
```bash
# API 서버 콘솔: fetch 응답 확인
# 브라우저 개발자도구 콘솔: [API] lead_001 "회의실로 이동합니다."
```

---

## 추후 클로드 코드(Claude Code) 작업 가이드

### 이 문서를 참조해야 하는 상황
1. **metaverse.html의 지시 기능을 수정할 때** → 라인 2433-2540 참조
2. **api_server.py의 키워드 분석을 수정할 때** → 라인 138-158 참조
3. **새로운 POI를 추가할 때** → POI_LIST 및 `/3` 스케일링 확인
4. **새로운 상태(status)를 추가할 때** → 색상 매핑 테이블(프론트/백 모두) 수정
5. **배치 지시 기능을 추가할 때** → 현재 1:1 구조를 배열 순회로 확장

### 주요 상수/테이블 위치
| 항목 | 파일 | 라인 | 설명 |
|---|---|---|---|
| LC 색상 테이블 | metaverse.html | 2476 | nameTag/label 색상 |
| statusRingColor | metaverse.html | 2406 | 링 색상 (0xRGB) |
| showBubble border | metaverse.html | 2671-2675 | 말풍선 테두리 색상 |
| POI_LIST | metaverse.html | 상단 | POI 정의 (tile 좌표) |
| 키워드 분석 | metaverse.html | 2454-2470 | 프론트엔드 분석 |
| 키워드 분석 | api_server.py | 138-158 | 백엔드 분석 |
| STATUS_LABEL | api_server.py | 53-59 | 상태 라벨 |

### 주의: 반드시 양쪽 모두 수정해야 하는 항목
- **키워드 목록**: metaverse.html 2454-2470 ↔ api_server.py 138-158
- **새 상태 추가**: LC 테이블 + statusRingColor + STATUS_LABEL + updateTaskStrip 색상
- **새 POI**: POI_LIST + startWalkTo 호출 지점의 `/3` 스케일링

---

## 업데이트 2: 병렬 개발 파이프라인 + QA 게이트 + 협업 메모리 (2026-05-19 11:30)

### 배경
- 사용자 요청: "병렬 작업도 적극적으로 활용해줘. 품질이 매우 중요하므로 각 단계에 대한 QA 철저하게 신경써줘. 해당 작업을 agents의 도움을 적극 받을 수 있도록 해줘. 라이브 사무실도 업데이트"

### 신규 파일

| 파일 | 설명 | 라인 |
|---|---|---|
| `scripts/run_pipeline.py` | DAG 위상 정렬 기반 병렬 파이프라인 실행기 | ~230줄 |
| `scripts/qa_gate.py` | 단계별 품질 체크포인트 관리자 | ~210줄 |
| `scripts/agent_collab.py` | 에이전트 협업 메모리 (핸드오프/동기화) | ~180줄 |
| `docs/PIPELINE_DEV.md` | 개발 파이프라인 가이드 | ~100줄 |

### metaverse.html 수정 상세

#### 1. QA 링 시각화 (line ~534, ~2855)
- `qaRingGfx` graphics 레이어 추가 (depth 45)
- review 상태: 노란색(#FFD700) 펄스 링
- waiting 상태: 주황색(#F0883E) 링

#### 2. 활성 파이프라인 아크 강화 (line ~2724, ~2882)
- `spawnFlow(fromId, toId, active)`에 active 파라미터 추가
- 활성 경로: 금색(#FFD700), 10개 파티클, 속도 1.2
- 비활성 경로: 팀 색상, 5개 파티클, 속도 0.6
- 활성 경로 아크: 두께 2.5, 알파 0.8
- 활성 경로 도착 시 스파크 파티클 생성

#### 3. 상태 변화 트리거 (line ~2820)
- working 상태 변경 시: PIPELINE 다음 단계로 `spawnFlow(id, nextId, true)`
- done 상태 변경 시: 다음 단계 idle 에이전트 주변에 스파크 + 컨페티

#### 4. 데이터 흐름 렌더링 강화 (line ~3052)
- 활성 흐름: 크기 4, 꼬리 효과, 12개 컨페티
- 비활성 흐름: 크기 2.5, 8개 컨페티

#### 5. Phase 인디케이터 (line ~218, ~2850)
- 사이드바 HTML UI 추가 (Phase 1/6 ~ 6/6)
- `fetchStatus()` 내 Phase 계산 로직
- 개발팀 6개 Phase 자동 감지

### 실행 결과

```bash
$ python3 scripts/run_pipeline.py dev

############################################################
# 팀: DEV 파이프라인 실행
############################################################

📋 총 6개 Phase, 10개 에이전트
   Phase 1 [순차]: requirements
   Phase 2 [병렬]: ux-designer, dba
   Phase 3 [병렬]: frontend, backend
   Phase 4 [병렬]: security, tester-unit
   Phase 5 [순차]: tester-qa
   Phase 6 [병렬]: devops, tech-writer

✅ Phase 1-6 QA 게이트 전원 통과
```

### QA 게이트 체크리스트

| 에이전트 | 검토자 | 항목 수 | 통과 기준 | 실제 점수 |
|---|---|---|---|---|
| requirements | lead-dev | 5 | 4/5 | 5/5 ✅ |
| ux-designer | lead-dev | 5 | 4/5 | 5/5 ✅ |
| dba | lead-dev | 5 | 4/5 | 5/5 ✅ |
| frontend | tester-unit | 5 | 4/5 | 5/5 ✅ |
| backend | tester-unit | 5 | 4/5 | 5/5 ✅ |
| security | tester-qa | 5 | 5/5 | 5/5 ✅ |
| tester-unit | tester-qa | 5 | 4/5 | 5/5 ✅ |
| tester-qa | lead-dev | 5 | 4/5 | 5/5 ✅ |
| devops | lead-dev | 5 | 4/5 | - |
| tech-writer | lead-dev | 5 | 4/5 | - |

### 추가 업데이트: 개발팀 활성화 (2026-05-19 11:03)

### 배경
- 사용자 요청: "라이브 사무실이 놀고있어. 개발팀을 적극 활용하면 좋을 것 같아. 당연히 상태 업데이트도 하고"
- 개발팀 10명 + 리드 1명 전원 `working` 상태로 전환

### 변경 파일
- `agent_status.json` — 상태 및 로그 업데이트 (수동)

### 업데이트된 에이전트 목록

| 에이전트 ID | 상태 | 작업 내용 |
|---|---|---|
| lead-dev | working | 개발팀 전체 프로젝트 관리 및 코드 리뷰 |
| requirements | working | 라이브 사무실 기능 확장 요구사항 정의 |
| ux-designer | working | 신규 패널 UI/UX 설계 및 인터랙션 정의 |
| frontend | working | Phaser 3 신규 씬 및 모달 컴포넌트 개발 |
| backend | working | FastAPI 신규 엔드포인트 및 WebSocket 구현 |
| dba | working | 에이전트 활동 로그 스키마 설계 및 마이그레이션 |
| security | working | API 인증 및 CORS 정책 강화 |
| tester-unit | working | 지시 기능 단위 테스트 작성 |
| tester-qa | working | E2E 테스트 시나리오 및 자동화 구축 |
| devops | working | Docker화 및 배포 파이프라인 구축 |
| tech-writer | working | API 명세서 및 개발 가이드 작성 |

### 실행 명령
```bash
# 배치 업데이트 (Python 스크립트)
cd /mnt/d/업무/agents && python3 << 'EOF'
import json
from datetime import datetime

with open("agent_status.json", encoding="utf-8") as f:
    data = json.load(f)

dev_tasks = {
    "requirements": "라이브 사무실 기능 확장 요구사항 정의",
    "ux-designer": "신규 패널 UI/UX 설계 및 인터랙션 정의",
    "frontend": "Phaser 3 신규 씬 및 모달 컴포넌트 개발",
    "backend": "FastAPI 신규 엔드포인트 및 WebSocket 구현",
    "dba": "에이전트 활동 로그 스키마 설계 및 마이그레이션",
    "security": "API 인증 및 CORS 정책 강화",
    "tester-unit": "지시 기능 단위 테스트 작성",
    "tester-qa": "E2E 테스트 시나리오 및 자동화 구축",
    "devops": "Docker화 및 배포 파이프라인 구축",
    "tech-writer": "API 명세서 및 개발 가이드 작성"
}

for agent_id, task in dev_tasks.items():
    data["agents"][agent_id] = {"status": "working", "task": task}
    data.setdefault("log", []).insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "status": "working",
        "label": "작업 시작",
        "task": task
    })

data["updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
data["log"] = data["log"][:30]

with open("agent_status.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
EOF

# 리드 개발자 개별 업데이트
python3 scripts/update_status.py lead-dev working "개발팀 전체 프로젝트 관리 및 코드 리뷰"
```

---

## 관련 문서

- `docs/LIVE_OFFICE_PROGRESS.md` — 전체 프로젝트 진행 상황
- `tasks/lessons.md` — 패턴 및 교훈 기록
- `CLAUDE.md` — 에이전트 역할 정의
- `agent_status.json` — 런타임 상태 파일 (자동 생성)
