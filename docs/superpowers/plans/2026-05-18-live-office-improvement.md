# Live Office Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development for executing this plan. Each task is independently shippable and verifiable in the browser. After each task, run a manual browser check before committing.

**Goal:** `D:/업무/agents/metaverse.html`의 Phaser 3 픽셀아트 사무실 시뮬레이션에 5가지 라이브 시각화 기능을 추가하여 에이전트의 작업 상태를 한눈에 파악할 수 있게 개선한다.

**Architecture:**
- 단일 HTML 파일(`metaverse.html`, 2299줄), Phaser 3 기반 캔버스 + HTML 오버레이 패널
- `MainScene.sprites[id]`에 에이전트 인스턴스 저장 (container/parts/bubble/label/status/task/mode)
- 3초마다 `agent_status.json` 폴링 → 상태 변경시 말풍선 + 로그
- Container는 scale 3x → 월드 공간 효과(링/아크)는 container 밖 별도 graphics 레이어에 그린다

**Tech Stack:** Phaser 3, Vanilla JS, HTML/CSS overlay, fetch polling

---

## 작업 원칙 (모든 태스크 공통)

- 단일 파일 프로젝트이므로 자동화 테스트는 없음 → **각 Step마다 브라우저에서 확인할 것**을 명시한다.
- 코드는 placeholder 없이 완전하게 붙여넣을 수 있는 형태로 작성한다.
- 한 태스크가 끝나면 `git add metaverse.html && git commit` 으로 격리한다.
- 검증 시 `agent_status.json`의 일부 에이전트 status를 수동으로 `working`/`review`/`done` 등으로 바꿔 새로고침하여 확인한다.
- DOM 조작 시 XSS 방지를 위해 `innerHTML` 대신 `textContent` 및 `createElement`/`appendChild`만 사용한다.

---

## Task 1: 상시 작업 표시 (Task Strip)

에이전트 이름 라벨 바로 아래에 항상 보이는 작은 텍스트로 현재 task를 표시한다. 18자 truncate, 상태에 따라 색상 변경, 이동 시 따라다님.

**Files:**
- Modify: `metaverse.html:1201-1280` (`createAgent` 내부)
- Modify: `metaverse.html:1845-1900` (`animateWalk` 라벨 추적 부분)
- Modify: `metaverse.html:2018-2060` (`fetchStatus` task 갱신 부분)

- [ ] **Step 1: createAgent 안에 taskStrip Text 객체 추가**

`createAgent(def)` 안에서 `label`을 생성한 직후, 아래 코드를 추가한다:

```js
// Task Strip: 라벨 아래 항상-보이는 현재 task 텍스트
const taskStrip = this.add.text(px, py + 46, '', {
  fontFamily: 'monospace',
  fontSize: '10px',
  color: '#6E7681',
  backgroundColor: 'rgba(13,17,23,0.6)',
  padding: { left: 4, right: 4, top: 1, bottom: 1 }
}).setOrigin(0.5, 0).setDepth(50);
```

그리고 `this.sprites[def.id] = { ... }` 객체에 `taskStrip` 키를 추가한다:

```js
this.sprites[def.id] = {
  def, container, parts, bubble, label, taskStrip, teamColor, skin, hair,
  status: 'idle', task: '', bubbleTimer: 0, mode: 'desk',
  baseX: px, baseY: py,
  /* 기존 필드 유지 */
};
```

- [ ] **Step 2: taskStrip 갱신 헬퍼 추가**

`MainScene` 클래스 안 (예: `showBubble` 메서드 직전)에 다음 메서드를 추가한다:

```js
updateTaskStrip(sp) {
  if (!sp.taskStrip) return;
  const raw = (sp.task || '').toString();
  const txt = raw.length > 18 ? raw.slice(0, 17) + '…' : raw;
  sp.taskStrip.setText(txt || (sp.status === 'idle' ? '대기 중' : sp.status));
  const color =
    sp.status === 'working' ? '#58A6FF' :
    sp.status === 'review'  ? '#D29922' :
    sp.status === 'waiting' ? '#F0883E' :
    sp.status === 'done'    ? '#3FB950' :
                              '#6E7681';
  sp.taskStrip.setColor(color);
}
```

- [ ] **Step 3: animateWalk에서 taskStrip 위치 추적**

`animateWalk(sp, dts)` 안 라벨 위치 갱신 코드 바로 아래에 추가:

```js
if (sp.taskStrip) {
  sp.taskStrip.x = sp.container.x;
  sp.taskStrip.y = sp.container.y + 46;
}
```

또한 데스크에 있을 때(animateWorking / animateIdle 내부 등)에도 label과 같은 방식으로 위치가 동기화되어야 하므로, label.x/y를 갱신하는 모든 위치에 같은 패턴으로 taskStrip.x/y도 갱신한다. (label 갱신 라인을 Grep해 모두 같이 갱신할 것)

- [ ] **Step 4: fetchStatus와 초기 생성 시 갱신 호출**

`fetchStatus()` 내부 `sp.status = status; sp.task = task;` 다음 줄에 추가:

```js
this.updateTaskStrip(sp);
```

또한 `createAgent` 끝부분 (return 직전)에서 초기 호출:

```js
this.updateTaskStrip(this.sprites[def.id]);
```

- [ ] **Step 5: 브라우저에서 확인**

1. `metaverse.html`을 브라우저로 연다.
2. 모든 에이전트 라벨 아래에 작은 회색 바가 보이는지 확인 (idle이면 "대기 중").
3. `agent_status.json`을 편집해 임의 에이전트의 `status`를 `working`, `task`를 `"긴 작업 텍스트 테스트 문자열입니다"`로 변경 후 새로고침 → 파란색(#58A6FF)으로 18자 truncate되어 `…` 표시 확인.
4. POI 이동 트리거 후 캐릭터 따라 taskStrip이 함께 이동하는지 확인.

- [ ] **Step 6: Commit**

```
git add metaverse.html
git commit -m "feat: 에이전트별 상시 작업 표시 task strip 추가"
```

---

## Task 2: 상태 링 광효과 (Status Ring)

캐릭터 머리 위에 월드 공간 글로우 링을 그린다. container 밖 별도 graphics로 그려 scale 영향을 받지 않게 한다.

**Files:**
- Modify: `metaverse.html:296-330` (`MainScene.create`)
- Modify: `metaverse.html:1201-1280` (`createAgent`)
- Modify: `metaverse.html:1845-1900` (`animateWalk`)
- Modify: `metaverse.html:2075-2160` (`update`)

- [ ] **Step 1: ringGfx 전역 레이어 생성**

`MainScene.create()` 안 `this.flowGfx = this.add.graphics();` 라인 근처에 추가:

```js
// 월드 공간 상태 링 (container 밖, scale 독립)
this.ringGfx = this.add.graphics();
this.ringGfx.setDepth(40); // 캐릭터 아래, 라벨 위
```

- [ ] **Step 2: 색상 매핑 헬퍼 추가**

`MainScene` 클래스 안에 다음 메서드 추가:

```js
statusRingColor(status) {
  switch (status) {
    case 'working': return 0x3FB950;
    case 'review':  return 0xD29922;
    case 'waiting': return 0xF0883E;
    case 'done':    return 0x58A6FF;
    default:        return 0x6E7681;
  }
}
```

- [ ] **Step 3: update()에서 매 프레임 모든 에이전트 링 redraw**

`update(time, dt)` 시작 부분에 추가 (per-agent 루프 전에):

```js
this.ringGfx.clear();
const t = time / 1000;
Object.keys(this.sprites).forEach(id => {
  const sp = this.sprites[id];
  if (!sp || !sp.container) return;
  const cx = sp.container.x;
  const cy = sp.container.y - 18; // 머리 위
  const color = this.statusRingColor(sp.status);
  let alpha = 0.55;
  let radius = 14;
  if (sp.status === 'working') {
    // pulsing
    const pulse = 0.5 + 0.5 * Math.sin(t * 3 + (sp.def ? sp.def.x : 0));
    alpha = 0.35 + pulse * 0.45;
    radius = 13 + pulse * 4;
  } else if (sp.status === 'idle') {
    alpha = 0.25;
  }
  // outer glow
  this.ringGfx.lineStyle(3, color, alpha * 0.5);
  this.ringGfx.strokeCircle(cx, cy, radius + 3);
  // inner ring
  this.ringGfx.lineStyle(2, color, alpha);
  this.ringGfx.strokeCircle(cx, cy, radius);
});
```

- [ ] **Step 4: 브라우저에서 확인**

1. 새로고침 후 모든 에이전트 머리 위에 회색 dim 링 표시 확인.
2. `agent_status.json`에서 일부 에이전트를 `working`으로 변경 → 초록색이 sin파로 펄싱하는지 확인.
3. `review`(주황 어두움), `waiting`(주황 밝음), `done`(파랑) 각각 색상 확인.
4. 에이전트가 POI로 이동할 때 링이 함께 따라다니는지 확인.

- [ ] **Step 5: Commit**

```
git add metaverse.html
git commit -m "feat: 상태별 머리 위 글로우 링 (working pulsing)"
```

---

## Task 3: 파이프라인 아크 연결선 (Pipeline Arcs)

PIPELINE 연결 관계인 두 에이전트가 모두 활성 상태(working/review/waiting)일 때 베지에 아크를 그리고 팀 컬러 점이 그 위를 흐른다.

**Files:**
- Modify: `metaverse.html:296-330` (`MainScene.create`)
- Modify: `metaverse.html:2075-2160` (`update`)

- [ ] **Step 1: pipelineGfx 레이어 생성**

`create()` 안 `this.ringGfx` 생성 다음 줄에 추가:

```js
this.pipelineGfx = this.add.graphics();
this.pipelineGfx.setDepth(20); // 캐릭터/링보다 아래
this.pipelineFlowT = 0;       // 아크 위 점 진행률
```

- [ ] **Step 2: PIPELINE 활성 판정 헬퍼**

`MainScene` 클래스 안에 추가:

```js
isPipelineActive(status) {
  return status === 'working' || status === 'review' || status === 'waiting';
}

quadPoint(p0, p1, p2, t) {
  const u = 1 - t;
  return {
    x: u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x,
    y: u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y
  };
}
```

- [ ] **Step 3: update()에서 매 프레임 아크 redraw**

`update(time, dt)` 안, 링 그리기 다음에 추가:

```js
this.pipelineGfx.clear();
this.pipelineFlowT = (this.pipelineFlowT + dt / 1000 * 0.4) % 1;

Object.keys(PIPELINE).forEach(srcId => {
  const src = this.sprites[srcId];
  if (!src || !this.isPipelineActive(src.status)) return;
  const targets = PIPELINE[srcId] || [];
  targets.forEach(dstId => {
    const dst = this.sprites[dstId];
    if (!dst || !this.isPipelineActive(dst.status)) return;

    const p0 = { x: src.container.x, y: src.container.y - 10 };
    const p2 = { x: dst.container.x, y: dst.container.y - 10 };
    const midX = (p0.x + p2.x) / 2;
    const midY = Math.min(p0.y, p2.y) - 40 - Math.abs(p2.x - p0.x) * 0.08;
    const p1 = { x: midX, y: midY };

    const color = src.teamColor || 0x58A6FF;

    // arc line
    this.pipelineGfx.lineStyle(1.5, color, 0.45);
    this.pipelineGfx.beginPath();
    this.pipelineGfx.moveTo(p0.x, p0.y);
    const steps = 24;
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const pt = this.quadPoint(p0, p1, p2, t);
      this.pipelineGfx.lineTo(pt.x, pt.y);
    }
    this.pipelineGfx.strokePath();

    // animated dot
    const dotT = this.pipelineFlowT;
    const dot = this.quadPoint(p0, p1, p2, dotT);
    this.pipelineGfx.fillStyle(color, 0.9);
    this.pipelineGfx.fillCircle(dot.x, dot.y, 3);
    // trailing fainter dot
    const trailT = (dotT + 0.85) % 1;
    const trail = this.quadPoint(p0, p1, p2, trailT);
    this.pipelineGfx.fillStyle(color, 0.4);
    this.pipelineGfx.fillCircle(trail.x, trail.y, 2);
  });
});
```

- [ ] **Step 4: 브라우저에서 확인**

1. `agent_status.json`에서 `data-collector`, `data-cleaner`, `eda-analyst`를 모두 `working`으로 설정 → 새로고침.
2. 세 에이전트 사이에 곡선 아크가 그려지고 점이 src→dst 방향으로 흐르는지 확인.
3. 그 중 하나를 `idle`로 바꾸면 해당 아크가 사라지는지 확인.
4. 팀 컬러(`teamColor`)가 아크 색에 반영되는지 확인.

- [ ] **Step 5: Commit**

```
git add metaverse.html
git commit -m "feat: 활성 에이전트 간 파이프라인 베지에 아크 + 흐름 점"
```

---

## Task 4: 클릭 → 에이전트 상세 패널 (Detail Panel)

캔버스 클릭으로 가장 가까운 에이전트(30px 이내) 감지 → HTML 오버레이 패널로 상세 표시. 구조화된 로그 5개. **XSS 방지를 위해 innerHTML 사용 금지, 모든 DOM은 createElement/appendChild/textContent로만 구성한다.**

**Files:**
- Modify: `metaverse.html:1-50` (CSS 영역)
- Modify: `metaverse.html:50-200` (HTML body, logs div 인근)
- Modify: `metaverse.html:296-330` (`MainScene.create`)
- Modify: `metaverse.html:2063-2074` (`addLog`)

- [ ] **Step 1: HTML 패널 마크업 + CSS 추가**

`<style>` 안에 추가:

```css
#agentPanel {
  position: fixed;
  right: 16px;
  top: 16px;
  width: 280px;
  background: rgba(13,17,23,0.92);
  border: 1px solid #30363d;
  border-radius: 8px;
  color: #c9d1d9;
  font-family: monospace;
  font-size: 12px;
  padding: 12px;
  z-index: 9999;
  display: none;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}
#agentPanel .ap-head {
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid #30363d; padding-bottom: 6px; margin-bottom: 8px;
}
#agentPanel .ap-name { font-size: 14px; font-weight: bold; }
#agentPanel .ap-close {
  cursor: pointer; color: #8b949e; padding: 2px 6px; border-radius: 4px;
}
#agentPanel .ap-close:hover { background: #21262d; color: #fff; }
#agentPanel .ap-badge {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 10px; font-weight: bold; margin-bottom: 6px;
}
#agentPanel .ap-task {
  background: #161b22; padding: 6px 8px; border-radius: 4px;
  margin: 6px 0; word-break: break-word;
}
#agentPanel .ap-logs { margin-top: 8px; max-height: 180px; overflow-y: auto; }
#agentPanel .ap-log {
  padding: 4px 6px; border-left: 2px solid #30363d;
  margin-bottom: 4px; font-size: 11px;
}
#agentPanel .ap-empty {
  color: #8b949e; font-style: italic;
}
#agentPanel .ap-logs-title {
  font-size: 10px; color: #8b949e; margin-top: 6px;
}
```

`<body>` 안 logs div 근처에 추가 (정적 마크업이므로 안전):

```html
<div id="agentPanel">
  <div class="ap-head">
    <span class="ap-name" id="apName">—</span>
    <span class="ap-close" id="apClose">✕</span>
  </div>
  <div id="apBadge" class="ap-badge">idle</div>
  <div class="ap-task" id="apTask">—</div>
  <div class="ap-logs-title">최근 로그</div>
  <div class="ap-logs" id="apLogs"></div>
</div>
```

- [ ] **Step 2: this.logs 배열 추가 + addLog 구조화 (textContent만 사용)**

`MainScene.create()` 시작부에 추가:

```js
this.logs = []; // [{ts, agentId, name, status, task}]
```

`addLog`를 다음과 같이 교체 (id 인자 추가, innerHTML 미사용):

```js
addLog(agentId, name, status, task) {
  const entry = { ts: Date.now(), agentId, name, status, task };
  this.logs.unshift(entry);
  if (this.logs.length > 200) this.logs.length = 200;

  const div = document.getElementById('logs');
  if (div) {
    const line = document.createElement('div');
    const time = new Date(entry.ts).toLocaleTimeString();
    line.textContent = `[${time}] ${name} → ${status}${task ? ': ' + task : ''}`;
    line.style.borderLeft = '2px solid ' +
      (status === 'working' ? '#3FB950' :
       status === 'review'  ? '#D29922' :
       status === 'waiting' ? '#F0883E' :
       status === 'done'    ? '#58A6FF' : '#6E7681');
    line.style.padding = '2px 6px';
    div.insertBefore(line, div.firstChild);
    while (div.childNodes.length > 50) div.removeChild(div.lastChild);
  }

  // 현재 패널이 열린 에이전트면 갱신
  if (this.openedAgentId === agentId) this.refreshAgentPanel();
}
```

그리고 `fetchStatus`에서 호출부를 다음과 같이 수정:

```js
this.addLog(id, sp.def.name, status, task);
```

- [ ] **Step 3: 클릭 핸들러 + 패널 갱신 (innerHTML 미사용)**

`MainScene.create()` 끝부분에 추가:

```js
this.input.on('pointerdown', (pointer) => {
  const wx = pointer.worldX;
  const wy = pointer.worldY;
  let best = null;
  let bestDist = 30; // 30px 이내
  Object.keys(this.sprites).forEach(id => {
    const sp = this.sprites[id];
    if (!sp || !sp.container) return;
    const dx = sp.container.x - wx;
    const dy = sp.container.y - wy;
    const d = Math.sqrt(dx * dx + dy * dy);
    if (d < bestDist) { bestDist = d; best = id; }
  });
  if (best) this.openAgentPanel(best);
});

const apClose = document.getElementById('apClose');
if (apClose) apClose.onclick = () => {
  document.getElementById('agentPanel').style.display = 'none';
  this.openedAgentId = null;
};
```

`MainScene` 클래스 안에 메서드 두 개 추가 (DOM 조작은 textContent + createElement만 사용):

```js
openAgentPanel(agentId) {
  this.openedAgentId = agentId;
  document.getElementById('agentPanel').style.display = 'block';
  this.refreshAgentPanel();
}

refreshAgentPanel() {
  const id = this.openedAgentId;
  if (!id) return;
  const sp = this.sprites[id];
  if (!sp) return;

  document.getElementById('apName').textContent = sp.def.name;
  document.getElementById('apTask').textContent = sp.task || '(작업 없음)';

  const badge = document.getElementById('apBadge');
  badge.textContent = sp.status;
  const colors = {
    working: ['#0d2818', '#3FB950'],
    review:  ['#2a210a', '#D29922'],
    waiting: ['#2a1a0a', '#F0883E'],
    done:    ['#0a1f2a', '#58A6FF'],
    idle:    ['#161b22', '#8b949e']
  };
  const c = colors[sp.status] || colors.idle;
  badge.style.background = c[0];
  badge.style.color = c[1];
  badge.style.border = '1px solid ' + c[1];

  // 로그 영역 안전하게 비우기 (innerHTML='' 대신)
  const logsDiv = document.getElementById('apLogs');
  while (logsDiv.firstChild) logsDiv.removeChild(logsDiv.firstChild);

  const recent = (this.logs || []).filter(e => e.agentId === id).slice(0, 5);
  if (recent.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'ap-empty';
    empty.textContent = '로그 없음';
    logsDiv.appendChild(empty);
  } else {
    recent.forEach(e => {
      const t = new Date(e.ts).toLocaleTimeString();
      const div = document.createElement('div');
      div.className = 'ap-log';
      div.style.borderLeftColor =
        e.status === 'working' ? '#3FB950' :
        e.status === 'review'  ? '#D29922' :
        e.status === 'waiting' ? '#F0883E' :
        e.status === 'done'    ? '#58A6FF' : '#6E7681';
      div.textContent = `[${t}] ${e.status}${e.task ? ': ' + e.task : ''}`;
      logsDiv.appendChild(div);
    });
  }
}
```

> **보안 메모:** task/name 문자열은 외부(`agent_status.json`)에서 오는 데이터이므로 절대 `innerHTML`로 삽입하지 않는다. 위 코드는 모두 `textContent`만 사용하여 XSS를 방지한다.

- [ ] **Step 4: 브라우저에서 확인**

1. 새로고침 → 캔버스에서 임의 에이전트 클릭.
2. 우측 상단에 패널이 뜨고 이름/배지/task가 정확히 표시되는지 확인.
3. ✕ 클릭으로 닫히는지 확인.
4. 패널을 열어둔 상태에서 해당 에이전트의 status를 `agent_status.json`에서 바꿔 폴링 후 패널이 자동 갱신되고 로그 라인이 쌓이는지 확인.
5. 빈 공간 클릭 시 패널이 열리지 않는지 확인 (30px 임계).
6. `task` 필드에 `<script>alert(1)</script>` 같은 문자열을 넣어 새로고침 → 텍스트로만 표시되고 스크립트 실행 안 되는지 확인 (XSS 검증).

- [ ] **Step 5: Commit**

```
git add metaverse.html
git commit -m "feat: 에이전트 클릭 상세 패널 + 구조화 로그 (XSS-safe DOM)"
```

---

## Task 5: 상태 반응형 행동 (Status-Reactive Behavior)

`pickNextIdleBehavior`를 상태별로 분기시켜 working 에이전트가 커피 마시러 가는 버그를 고친다.

**Files:**
- Modify: `metaverse.html:1671-1750` (`pickNextIdleBehavior`)

- [ ] **Step 1: pickNextIdleBehavior 재구성**

기존 `pickNextIdleBehavior(sp)` 함수 전체를 아래로 교체한다 (POI_LIST/데스크액션 명칭은 기존 코드와 동일 가정):

```js
pickNextIdleBehavior(sp) {
  if (!sp || !sp.def) return;
  const status = sp.status || 'idle';
  const r = Math.random();

  // done: 즉시 축하 표시 + 짧게 coffee1로 이동
  if (status === 'done') {
    this.showBubble(sp, '✅ 완료!', 'done');
    const coffee = (typeof POI_LIST !== 'undefined') ? POI_LIST.find(p => p.id === 'coffee1') : null;
    if (coffee) {
      this.startMoveTo(sp, coffee.x, coffee.y, { duration: 8, mode: 'poi', poi: 'coffee1' });
    } else {
      this.doDeskAction(sp, 'look_around');
    }
    return;
  }

  // working: 95% 데스크 미세 액션, 5% lounge 잠깐
  if (status === 'working') {
    if (r < 0.95) {
      const acts = ['type_fast', 'sit_idle', 'look_around'];
      const pick = acts[Math.floor(Math.random() * acts.length)];
      this.doDeskAction(sp, pick);
    } else {
      this.visitPOI(sp, 'lounge');
    }
    return;
  }

  // review / waiting: 70% 데스크, 30% lounge 또는 board 방문
  if (status === 'review' || status === 'waiting') {
    if (r < 0.7) {
      const acts = ['sit_idle', 'look_around', 'type_fast'];
      const pick = acts[Math.floor(Math.random() * acts.length)];
      this.doDeskAction(sp, pick);
    } else {
      const poi = Math.random() < 0.5 ? 'lounge' : 'board';
      this.visitPOI(sp, poi);
    }
    return;
  }

  // idle: 기존 확률 유지 (데스크/POI 혼합)
  if (r < 0.55) {
    const acts = ['sit_idle', 'look_around', 'type_fast', 'stretch'];
    const pick = acts[Math.floor(Math.random() * acts.length)];
    this.doDeskAction(sp, pick);
  } else {
    const pois = ['coffee1', 'coffee2', 'lounge', 'board', 'sofa', 'server'];
    const poi = pois[Math.floor(Math.random() * pois.length)];
    this.visitPOI(sp, poi);
  }
}
```

> 주의: 기존 코드의 `doDeskAction` / `visitPOI` / `startMoveTo` 시그니처와 정확히 맞춰야 한다. 함수명이 다르면 Grep으로 실제 명칭을 찾아 대체할 것 (`grep -n "deskAction\|visitPOI\|startMoveTo" metaverse.html`). 액션 키(`type_fast`, `sit_idle`, `look_around`, `stretch`)도 기존 정의와 일치하는지 확인.

- [ ] **Step 2: 브라우저에서 확인**

1. `agent_status.json`에서 한 에이전트를 `working`으로 설정 → 새로고침.
2. 최소 1분 관찰: 자리에서 데스크 액션만 반복하고 거의 커피/POI로 안 가는지 확인 (5% 확률 lounge만 허용).
3. 다른 에이전트를 `review`로 설정 → 가끔 board/lounge로 가는지 확인.
4. 또 다른 에이전트를 `done`으로 설정 → 즉시 "✅ 완료!" 말풍선 후 coffee1로 짧게 이동 확인.
5. idle 에이전트들은 기존처럼 다양한 POI 방문을 계속하는지 확인.

- [ ] **Step 3: Commit**

```
git add metaverse.html
git commit -m "fix: pickNextIdleBehavior를 status별 분기로 재구성 (working 커피 버그 fix)"
```

---

## 최종 검증 체크리스트

모든 태스크 완료 후 브라우저에서 다음을 한번에 확인한다:

- [ ] 모든 에이전트 아래에 task strip이 보이고 색이 상태에 맞다.
- [ ] 모든 에이전트 머리 위에 상태 링이 있고 working은 펄싱.
- [ ] 활성 에이전트끼리 PIPELINE 아크가 보이고 점이 흐른다.
- [ ] 에이전트 클릭 시 우측 패널이 뜨고 ✕로 닫힌다. 패널 안의 로그가 폴링마다 갱신된다.
- [ ] XSS 페이로드를 task로 넣어도 텍스트로만 표시된다.
- [ ] working 에이전트는 자리를 거의 안 비우고, done은 완료 표시 후 coffee1로 간다.
- [ ] 콘솔에 에러 없음 (F12 → Console).

검증이 모두 통과하면 superpowers:verification-before-completion 스킬로 최종 완료 선언.
