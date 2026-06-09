# 라이브 사무실 종합 개편 계획 (2026-05-19)

## 목표
밝고 깔끔한 모던 오피스 룩 + 실제 사무실처럼 정적인 에이전트 + 풍부한 사이드바 + 회의실 동선/시각 개선 + 대시보드 UX 개선.

## 전체 제약
- `D:/업무/agents/scripts/validate.py` 25개 체크 모두 GREEN 유지.
- 작업 종료 시 `python scripts/stamp.py`로 `METAVERSE_UPDATED` 갱신.
- 복도(`corridor*`) 팔레트 값은 절대 변경 금지.
- 모든 변경은 트랙별 단일 커밋.
- DOM 갱신은 가능한 경우 textContent + createElement 우선 사용 (XSS 회피). 다이내믹 문자열은 사용자 입력이 아닐 때만 템플릿 사용.

## 대상 파일
- `D:/업무/agents/metaverse.html` (~3650 라인, Phaser 3)
- `D:/업무/agents/index.html` (~1143 라인, vanilla JS 대시보드)
- `D:/업무/agents/scripts/validate.py`
- `D:/업무/agents/scripts/stamp.py`

---

## TRACK A — 바닥 색상 밝게 (Floor Color Overhaul)

**Files:**
- `D:/업무/agents/metaverse.html` 라인 ~443 (`FLOOR_COLOR` 상수), 라인 ~451 (`PALETTE` 객체)

**Steps:**

- [ ] `metaverse.html` 라인 ~451 `PALETTE` 객체를 다음 값으로 교체 (corridor/orch_floor/lounge_floor/wall_* 등은 그대로 유지):
  ```js
  const PALETTE = {
    orch_floor: 0xF5F0E8, orch_floor2: 0xEDE8DC,
    data_floor: 0x1E4A7A, data_floor2: 0x234F82,
    dev_floor: 0x1E4A28, dev_floor2: 0x235530,
    pptx_floor: 0x2E1A5A, pptx_floor2: 0x341E66,
    lounge_floor: 0x9A6A38, lounge_floor2: 0xAA7A42,
    meeting_floor: 0x2E4878, meeting_floor2: 0x324E82,
    pptx2_floor: 0x2E1A5A,
    review_floor: 0x0E1E2E,
    break_floor: 0x503420, break_floor2: 0x5A3C24,
    corridor: 0xD4C4A0, corridor2: 0xC8BA94, corridor_line: 0xBFB090,
    wall_dark: 0x1E242C, wall_mid: 0x28303A, wall_accent: 0x323C48,
  };
  ```

- [ ] `metaverse.html` 라인 ~443의 `FLOOR_COLOR` 상수를 다음과 같이 동기화:
  ```js
  const FLOOR_COLOR = {
    orch: 0xF5F0E8,
    data: 0x1E4A7A,
    dev: 0x1E4A28,
    pptx: 0x2E1A5A,
    lounge: 0x9A6A38,
    meeting: 0x2E4878,
    break: 0x503420,
    review: 0x0E1E2E,
    corridor: 0xD4C4A0,
  };
  ```

- [ ] Grep으로 옛 헥스(`0x1C3455`, `0x213B5E`, `0x142C1A`, `0x183320`, `0x1E1240`, `0x231548`, `0x243862`, `0x2A406E`, `0x0C1624`, `0x38271A`, `0x42301E`) 잔존 여부 확인 후 위 값으로 치환.

- [ ] 브라우저로 `metaverse.html` 열어 4개 팀 구역 텍스트 가독성·구분 가능 확인, 스크린샷 1장 저장.

- [ ] `python scripts/validate.py` → GREEN. 이어서 `python scripts/stamp.py`.

**Commit:**
```
git add metaverse.html
git commit -m "feat(office): brighten team floor palette for modern office look"
```

---

## TRACK B — 에이전트 이동 최소화 (Agent Movement Reduction)

**Files:**
- `D:/업무/agents/metaverse.html` 라인 ~2244 `pickNextIdleBehavior`, 에이전트 생성 시 `idleTimer` 초기화 위치

**Steps:**

- [ ] 에이전트 생성 루프에서 `idleTimer: Math.random() * 3`를 다음으로 교체 (30~180초 분산):
  ```js
  idleTimer: 30 + Math.random() * 150,
  ```

- [ ] `pickNextIdleBehavior` 함수 내 `status === 'idle'` 분기를 다음 로직으로 교체:
  ```js
  if (a.status === 'idle') {
    const roll = Math.random();
    const isLead = a.role === 'lead';

    if (roll < 0.015) {
      return { kind: 'go_coffee', timer: 20 + Math.random() * 20 };
    }
    if (roll < 0.020) {
      return { kind: 'go_sofa', timer: 30 + Math.random() * 30 };
    }
    if (isLead && roll < 0.023) {
      return { kind: 'go_meeting', timer: 40 + Math.random() * 40 };
    }
    if (isLead && roll < 0.024) {
      return { kind: 'go_whiteboard', timer: 30 + Math.random() * 30 };
    }
    const deskBehaviors = [
      { kind: 'sit_idle', timer: 60 + Math.random() * 60 },
      { kind: 'type_fast', timer: 40 + Math.random() * 40 },
      { kind: 'sit_idle', timer: 90 + Math.random() * 60 },
      { kind: 'lean_back', timer: 30 + Math.random() * 30 },
    ];
    return deskBehaviors[Math.floor(Math.random() * deskBehaviors.length)];
  }
  ```

- [ ] 동일 함수 내 `status === 'done'` 분기를 단순화:
  ```js
  if (a.status === 'done') {
    return { kind: 'sit_idle', timer: 60 + Math.random() * 60 };
  }
  ```

- [ ] `status === 'working'` / `status === 'reviewing'` 분기에서 POI 이동이 있다면 책상 행동(`type_fast`, `sit_idle`)으로 대체, timer 최소 60초.

- [ ] 브라우저로 5분간 관찰, 동시 이동 1~2명 이하 확인. 콘솔에서
  ```js
  console.log(agents.filter(a => a.behavior && a.behavior.kind && a.behavior.kind.startsWith('go_')).length)
  ```
  주기적 출력으로 검증.

- [ ] `python scripts/validate.py` → GREEN. 이어서 `python scripts/stamp.py`.

**Commit:**
```
git add metaverse.html
git commit -m "feat(office): minimize agent movement to realistic office cadence (120s+ desk time)"
```

---

## TRACK C — 사이드바 강화 (Sidebar Enhancement)

**Files:**
- `D:/업무/agents/metaverse.html` 사이드바 HTML 영역 (라인 ~68-419), `window.updateSidebarStats` 함수, `addLog` 함수 (라인 ~3176)

**보안 메모:**
DOM 갱신은 `textContent` + `createElement` 위주로 작성한다. 에이전트 이름/태스크 문자열이 외부 MD에서 유입될 수 있으므로 innerHTML 직삽입 금지.

**Steps:**

- [ ] 사이드바 HTML에서 `<!-- 집합 명령 -->` 주석 바로 앞에 다음 블록 삽입:
  ```html
  <div class="sidebar-section" id="team-progress-section">
    <h3 class="section-title">팀별 완료율</h3>
    <div id="team-progress-bars"></div>
  </div>

  <div class="sidebar-section" id="completed-section">
    <h3 class="section-title">최근 완료</h3>
    <ul id="completed-tasks-list" class="completed-list"></ul>
  </div>

  <div class="sidebar-section" id="pipeline-section">
    <h3 class="section-title">파이프라인 현황</h3>
    <div id="pipeline-flow-text" class="pipeline-flow">대기 중...</div>
  </div>
  ```

- [ ] 사이드바 CSS 영역에 다음 추가:
  ```css
  .sidebar-section { margin: 10px 0; padding: 8px; background: rgba(255,255,255,0.04); border-radius: 6px; }
  .section-title { font-size: 12px; font-weight: 600; margin: 0 0 6px; color: #B8C5D0; letter-spacing: 0.5px; }
  .team-bar-row { display: flex; align-items: center; gap: 6px; margin: 4px 0; font-size: 11px; }
  .team-bar-row .team-label { width: 70px; color: #D4DCE5; }
  .team-bar-row .team-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; }
  .team-bar-row .team-bar-fill { height: 100%; background: linear-gradient(90deg, #4FC3F7, #29B6F6); transition: width 0.4s; }
  .team-bar-row .team-count { width: 38px; text-align: right; color: #9FB0BD; }
  .completed-list { list-style: none; margin: 0; padding: 0; max-height: 110px; overflow-y: auto; }
  .completed-list li { font-size: 11px; padding: 3px 4px; color: #C0D0DC; border-left: 2px solid #66BB6A; margin: 2px 0; background: rgba(102,187,106,0.05); }
  .pipeline-flow { font-size: 11px; color: #E1E8EE; line-height: 1.5; padding: 4px; }
  .pipeline-flow .arrow { color: #4FC3F7; margin: 0 4px; }
  ```

- [ ] `window.updateSidebarStats` 함수를 다음 로직으로 확장(textContent 기반):
  ```js
  // 팀별 완료율
  const teamStats = {};
  agents.forEach(a => {
    const t = a.team || 'etc';
    if (!teamStats[t]) teamStats[t] = { total: 0, done: 0 };
    teamStats[t].total += 1;
    if (a.status === 'done') teamStats[t].done += 1;
  });
  const tpBars = document.getElementById('team-progress-bars');
  if (tpBars) {
    while (tpBars.firstChild) tpBars.removeChild(tpBars.firstChild);
    Object.entries(teamStats).forEach(([t, s]) => {
      const pct = s.total ? Math.round(s.done / s.total * 100) : 0;
      const row = document.createElement('div');
      row.className = 'team-bar-row';
      const lab = document.createElement('span'); lab.className = 'team-label'; lab.textContent = t;
      const bar = document.createElement('span'); bar.className = 'team-bar';
      const fill = document.createElement('span'); fill.className = 'team-bar-fill';
      fill.style.width = pct + '%';
      bar.appendChild(fill);
      const cnt = document.createElement('span'); cnt.className = 'team-count'; cnt.textContent = s.done + '/' + s.total;
      row.appendChild(lab); row.appendChild(bar); row.appendChild(cnt);
      tpBars.appendChild(row);
    });
  }

  // 최근 완료
  const compList = document.getElementById('completed-tasks-list');
  const recent = (window.__completedRecently || []).slice(-3).reverse();
  if (compList) {
    while (compList.firstChild) compList.removeChild(compList.firstChild);
    if (recent.length === 0) {
      const li = document.createElement('li');
      li.style.border = 'none'; li.style.color = '#7A8A95';
      li.textContent = '(없음)';
      compList.appendChild(li);
    } else {
      recent.forEach(c => {
        const li = document.createElement('li');
        const b = document.createElement('b'); b.textContent = c.name;
        li.appendChild(b);
        li.appendChild(document.createTextNode(' — ' + (c.task || '작업 완료')));
        compList.appendChild(li);
      });
    }
  }

  // 파이프라인 흐름
  const pipe = document.getElementById('pipeline-flow-text');
  if (pipe) {
    while (pipe.firstChild) pipe.removeChild(pipe.firstChild);
    const working = agents.filter(a => a.status === 'working').map(a => a.team).filter(Boolean);
    const uniq = [...new Set(working)];
    if (uniq.length === 0) {
      pipe.textContent = '대기 중...';
    } else {
      uniq.forEach((t, i) => {
        if (i > 0) {
          const arr = document.createElement('span'); arr.className = 'arrow'; arr.textContent = '▶';
          pipe.appendChild(arr);
        }
        const sp = document.createElement('span'); sp.textContent = t;
        pipe.appendChild(sp);
      });
    }
  }
  ```

- [ ] 스크립트 초기화부에 다음 1줄 추가:
  ```js
  window.__completedRecently = window.__completedRecently || [];
  ```

- [ ] `addLog` 함수 (라인 ~3176) 내부, status 전환 처리부에 다음 push 로직 추가:
  ```js
  if (status === 'done' && agent) {
    window.__completedRecently = window.__completedRecently || [];
    window.__completedRecently.push({
      name: agent.name,
      task: agent.currentTask || agent.lastTask || '작업 완료',
      ts: Date.now()
    });
    if (window.__completedRecently.length > 20) window.__completedRecently.shift();
  }
  ```

- [ ] 브라우저에서 fetchStatus 1회 이상 호출 후 3개 섹션 모두 채워짐 확인.

- [ ] `python scripts/validate.py` → GREEN. 이어서 `python scripts/stamp.py`.

**Commit:**
```
git add metaverse.html
git commit -m "feat(sidebar): add team progress bars, recent completions, pipeline flow"
```

---

## TRACK D — 회의실 개선 (Meeting Room Fixes)

**Files:**
- `D:/업무/agents/metaverse.html` `computeWaypoints` 함수, 회의실 테이블 그리기(`drawMeetingRoom` 또는 `createRoomDecor` 내 `meeting` 분기)

**Steps:**

- [ ] `computeWaypoints` 함수 진입부에 다음 분기 추가 (좌표는 실제 입구에 맞게 조정):
  ```js
  const meetingZone = dstTX >= 24 && dstTY <= 6;
  if (meetingZone) {
    const corridorWP = { tx: 23, ty: 7 };
    const fromCorridor = (srcTX === 23 && srcTY === 7);
    if (!fromCorridor) {
      return [corridorWP, { tx: 24, ty: 6 }, { tx: dstTX, ty: dstTY }];
    }
  }
  ```

- [ ] 회의실 테이블 시각: 기존 `fillRect` 호출을 다음으로 교체:
  ```js
  const tx = roomX + 2 * TILE, ty = roomY + 2 * TILE;
  const tw = 4 * TILE, th = 2 * TILE;
  graphics.fillStyle(0x6B4226, 1);
  graphics.fillRoundedRect(tx, ty, tw, th, 8);
  graphics.lineStyle(2, 0x4A2D18, 1);
  graphics.strokeRoundedRect(tx, ty, tw, th, 8);
  graphics.lineStyle(1, 0x5A3820, 0.5);
  for (let i = 1; i < 4; i++) {
    graphics.lineBetween(tx + 4, ty + (th * i / 4), tx + tw - 4, ty + (th * i / 4));
  }
  ```

- [ ] 좌석 도트 6개 추가:
  ```js
  const seats = [
    { x: tx + tw*0.25, y: ty - 4, color: 0x4FC3F7 },
    { x: tx + tw*0.50, y: ty - 4, color: 0xE57373 },
    { x: tx + tw*0.75, y: ty - 4, color: 0x81C784 },
    { x: tx + tw*0.25, y: ty + th + 4, color: 0xBA68C8 },
    { x: tx + tw*0.50, y: ty + th + 4, color: 0xFFB74D },
    { x: tx + tw*0.75, y: ty + th + 4, color: 0xA1887F },
  ];
  seats.forEach(s => {
    graphics.fillStyle(s.color, 1);
    graphics.fillCircle(s.x, s.y, 3);
  });
  ```

- [ ] 브라우저: 에이전트 회의실 진입 5회 관찰, 테이블 가로지름 없음 확인.

- [ ] `python scripts/validate.py` → GREEN. 이어서 `python scripts/stamp.py`.

**Commit:**
```
git add metaverse.html
git commit -m "feat(meeting): force corridor approach, add wood-grain table and seat dots"
```

---

## TRACK E — index.html 대시보드 개선

**Files:**
- `D:/업무/agents/index.html` (에이전트 카드 렌더링부, MD 에디터부, 폴링 init)

**보안 메모:**
에이전트 이름/태스크는 textContent로 렌더. innerHTML 사용 시 사용자가 편집한 MD 콘텐츠가 흘러들 위험이 있으므로 카드 내부는 createElement 기반으로 유지.

**Steps:**

- [ ] 에이전트 카드 렌더 함수(`renderAgentCard` 또는 카드 생성 루프)를 다음 구조로 교체:
  ```js
  function renderAgentCard(a) {
    const card = document.createElement('div');
    card.className = 'agent-card';
    card.setAttribute('data-name', a.name);

    const header = document.createElement('div'); header.className = 'card-header';
    const dot = document.createElement('span'); dot.className = 'status-dot';
    dot.setAttribute('data-status', a.status || 'idle');
    const name = document.createElement('span'); name.className = 'agent-name'; name.textContent = a.name;
    const team = document.createElement('span'); team.className = 'agent-team'; team.textContent = a.team || '';
    header.appendChild(dot); header.appendChild(name); header.appendChild(team);

    const task = document.createElement('div'); task.className = 'agent-task';
    task.textContent = a.currentTask || '대기 중';

    const btn = document.createElement('button'); btn.className = 'edit-md'; btn.textContent = 'MD 편집';
    btn.addEventListener('click', () => openMdEditor(a.name));

    card.appendChild(header); card.appendChild(task); card.appendChild(btn);
    return card;
  }
  ```

- [ ] CSS 추가:
  ```css
  .agent-card { background:#fff; border-radius:10px; padding:12px; margin:8px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06); transition:transform 0.15s, box-shadow 0.15s; }
  .agent-card:hover { transform:translateY(-2px); box-shadow:0 4px 14px rgba(0,0,0,0.10); }
  .card-header { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
  .status-dot { width:10px; height:10px; border-radius:50%; background:#BDBDBD; }
  .status-dot[data-status="working"] { background:#42A5F5; box-shadow:0 0 6px #42A5F5; }
  .status-dot[data-status="reviewing"]{ background:#FFB300; box-shadow:0 0 6px #FFB300; }
  .status-dot[data-status="done"]     { background:#66BB6A; box-shadow:0 0 6px #66BB6A; }
  .status-dot[data-status="idle"]     { background:#BDBDBD; }
  .agent-name { font-weight:600; font-size:14px; color:#212B36; }
  .agent-team { font-size:11px; color:#6B7785; margin-left:auto; }
  .agent-task { font-size:12px; color:#445566; min-height:16px; }
  textarea.md-editor { width:100%; min-height:320px; padding:12px; font:13px/1.6 'D2Coding','Consolas',monospace;
    border:1px solid #DDE3EA; border-radius:8px; background:#FAFBFC; resize:vertical; }
  textarea.md-editor:focus { outline:none; border-color:#42A5F5; box-shadow:0 0 0 3px rgba(66,165,245,0.15); }
  .toast { position:fixed; bottom:24px; right:24px; background:#212B36; color:#fff; padding:10px 16px;
    border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,0.18); opacity:0; transform:translateY(10px);
    transition:opacity 0.2s, transform 0.2s; z-index:9999; }
  .toast.show { opacity:1; transform:translateY(0); }
  .toast.success { background:#2E7D32; }
  .toast.error { background:#C62828; }
  ```

- [ ] MD 저장 + 토스트 함수(textContent 기반):
  ```js
  function showToast(msg, type) {
    type = type || 'success';
    let t = document.getElementById('toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'toast';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.className = 'toast ' + type + ' show';
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
  }

  async function saveMd(name, content) {
    try {
      const res = await fetch('/api/md/' + encodeURIComponent(name), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });
      if (!res.ok) throw new Error(res.statusText);
      showToast('저장되었습니다', 'success');
    } catch (e) {
      showToast('저장 실패: ' + e.message, 'error');
    }
  }
  ```

- [ ] 실시간 폴링: 페이지 init에 추가:
  ```js
  async function pollAgentStatus() {
    try {
      const res = await fetch('/agent_status.json?_=' + Date.now());
      const data = await res.json();
      (data.agents || []).forEach(a => {
        const card = document.querySelector('.agent-card[data-name="' + a.name + '"]');
        if (!card) return;
        const dot = card.querySelector('.status-dot');
        if (dot) dot.setAttribute('data-status', a.status || 'idle');
        const task = card.querySelector('.agent-task');
        if (task) task.textContent = a.currentTask || '대기 중';
      });
    } catch (e) { /* silent */ }
  }
  setInterval(pollAgentStatus, 5000);
  pollAgentStatus();
  ```

- [ ] 브라우저: index.html 열어 카드 hover, 상태 dot 색 변화, MD 저장 시 토스트, 5초 폴링(네트워크 탭) 모두 확인.

- [ ] `python scripts/validate.py` → GREEN. 이어서 `python scripts/stamp.py`.

**Commit:**
```
git add index.html
git commit -m "feat(dashboard): refresh agent cards, MD toast, 5s status polling"
```

---

## 종료 체크리스트
- [ ] 5개 커밋 모두 생성됨
- [ ] `validate.py` 25/25 GREEN
- [ ] `METAVERSE_UPDATED` 갱신 확인
- [ ] 브라우저 스크린샷 5장 (트랙별) 저장
- [ ] 메모리에 결과 요약 기록 (이동 빈도, 색상, 사이드바 변화)
