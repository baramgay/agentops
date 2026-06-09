"""
build_html.py  —  agents/ 폴더 자동 스캔 기반 index.html 재생성

에이전트 추가 시 별도 등록 불필요:
  1. agents/[id]/ 폴더 + role.md 생성
  2. metaverse.html AGENTS 배열에 등록
  3. python scripts/build_html.py 실행
  → MD 에디터 사이드바, AGENT_NAMES, 오피스 뷰 데스크, agent_status.json 자동 반영
"""

import json, re, os
from datetime import datetime
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT   = _SCRIPT_DIR.parent

# ══════════════════════════════════════════════════════════════════
# 0. Claude Code 상태 수집
# ══════════════════════════════════════════════════════════════════

def collect_repo_skills():
    """레포 skills/ 폴더 스캔 — SKILL.md가 있는 하위 폴더를 레포 스킬로 인식."""
    repo_skills_dir = _REPO_ROOT / 'skills'
    if not repo_skills_dir.exists():
        return []
    return sorted([d.name for d in repo_skills_dir.iterdir()
                   if d.is_dir() and (d / 'SKILL.md').exists()])


def _skill_desc(skill_md_path):
    """SKILL.md에서 첫 설명 줄 추출 (프론트매터·제목 제외)."""
    try:
        content = Path(skill_md_path).read_text(encoding='utf-8', errors='ignore')
        in_fm = False; fm_done = False
        for line in content.split('\n'):
            s = line.strip()
            if s == '---':
                if not fm_done:
                    in_fm = not in_fm
                    if not in_fm: fm_done = True
                continue
            if in_fm: continue
            if s.startswith('#') or not s: continue
            return s[:120]
    except Exception:
        pass
    return ''


def collect_mv_skill_data():
    """metaverse.html 사이드바 패널용 스킬 데이터 수집.
    반환: {'skills': [{name,desc,isRepo}], 'repoContent': {name: content}}
    """
    home = Path.home()
    skills_dir = home / '.claude' / 'skills'
    repo_dir   = _REPO_ROOT / 'skills'
    repo_names = set(collect_repo_skills())

    skills = []
    local_names = set()
    if skills_dir.exists():
        for d in sorted(skills_dir.iterdir()):
            if not d.is_dir(): continue
            skill_md = d / 'SKILL.md'
            desc = _skill_desc(skill_md) if skill_md.exists() else ''
            skills.append({'name': d.name, 'desc': desc, 'isRepo': d.name in repo_names})
            local_names.add(d.name)

    # 레포에만 있는 스킬 추가
    for rn in sorted(repo_names - local_names):
        rmd = repo_dir / rn / 'SKILL.md'
        skills.append({'name': rn, 'desc': _skill_desc(rmd) if rmd.exists() else '', 'isRepo': True})
    skills.sort(key=lambda x: x['name'])

    # 레포 스킬 전체 내용 (편집용)
    repo_content = {}
    for rn in repo_names:
        rmd = repo_dir / rn / 'SKILL.md'
        if rmd.exists():
            repo_content[rn] = rmd.read_text(encoding='utf-8', errors='ignore')

    return {'skills': skills, 'repoContent': repo_content}


def collect_cc_status():
    """~/.claude/skills, settings.json 읽어 CC 상태 딕셔너리 반환."""
    home = Path.home()
    cc_dir = home / '.claude'

    # 로컬 스킬 목록
    skills_dir = cc_dir / 'skills'
    local_skills = sorted([d.name for d in skills_dir.iterdir() if d.is_dir()]) if skills_dir.exists() else []

    # 레포 스킬 합산 (중복 제거)
    repo_skills = collect_repo_skills()
    skills = sorted(set(local_skills) | set(repo_skills))

    # 훅 목록 (settings.json)
    hooks_raw = {}
    settings_path = cc_dir / 'settings.json'
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding='utf-8'))
            hooks_raw = data.get('hooks', {})
        except Exception:
            pass

    # 훅 평탄화: {event: [cmd, ...]}
    hooks = {}
    for event, entries in hooks_raw.items():
        for entry in entries:
            items = []
            for h in entry.get('hooks', []):
                cmd = h.get('command', '')
                # 짧은 설명 추출 (python -c "..." 는 첫 줄만)
                if 'memory' in cmd.lower():
                    items.append('메모리 로더')
                elif 'hookify' in cmd.lower() and 'pretooluse' in cmd.lower():
                    items.append('hookify pretooluse 분석기')
                elif 'hookify' in cmd.lower() and 'posttooluse' in cmd.lower():
                    items.append('hookify posttooluse 분석기')
                elif cmd:
                    items.append(cmd[:60].strip())
            matcher = entry.get('matcher', '')
            key = f"{event}:{matcher}" if matcher else event
            hooks[key] = items

    total_hooks = sum(len(v) for v in hooks.values())

    return {
        'skills': skills,
        'skill_count': len(skills),
        'hooks': hooks,
        'hook_count': total_hooks,
        'hook_events': len(hooks),
    }

# union.json 존재 시 우선 사용 (합집합 기준), 없으면 로컬 스킬
_UNION_PATH = _REPO_ROOT / 'cc_status' / 'union.json'
if _UNION_PATH.exists():
    try:
        _union = json.loads(_UNION_PATH.read_text(encoding='utf-8'))
        _local = collect_cc_status()
        _repo_skills = collect_repo_skills()
        _union_skills = sorted(set(_union.get('union_skills', _local['skills'])) | set(_repo_skills))
        CC_STATUS = {
            'skills':        _union_skills,
            'skill_count':   len(_union_skills),
            'repo_skills':   _repo_skills,
            'hooks':         _local['hooks'],
            'hook_count':    _local['hook_count'],
            'hook_events':   _local['hook_events'],
            'source':        'union',
            'machine_count': _union.get('machine_count', 1),
        }
    except Exception:
        CC_STATUS = collect_cc_status()
        CC_STATUS['repo_skills'] = collect_repo_skills()
        CC_STATUS['source'] = 'local'
else:
    CC_STATUS = collect_cc_status()
    CC_STATUS['repo_skills'] = collect_repo_skills()
    CC_STATUS['source'] = 'local'

# ══════════════════════════════════════════════════════════════════
# 1. 에이전트 메타데이터 수집 (metaverse.html AGENTS 배열 파싱)
# ══════════════════════════════════════════════════════════════════

TEAM_LABEL = {'lead': '총괄', 'data': '데이터', 'dev': '개발', 'pptx': 'PPTX'}
TEAM_CLS   = {'lead': 'team-lead', 'data': 'team-data', 'dev': 'team-dev', 'pptx': 'team-pptx'}
TEAM_EMOJI = {'lead': '🏛️', 'data': '📊', 'dev': '💻', 'pptx': '🎨'}

# 팀별 사이드바 표시 이모지 (에이전트 ID -> 이모지)
AGENT_EMOJI = {
    'orchestrator':'🎯','lead-data':'📊','lead-dev':'💻','lead-pptx':'🎨',
    'data-collector':'🕵️','data-cleaner':'🧹','eda-analyst':'🔍',
    'statistician':'📐','ml-engineer':'🤖','deep-learning':'🧠',
    'gis-specialist':'🗺️','text-analyst':'📝','visualizer':'📊',
    'reporter':'📋','realty-analyst':'🏘️',
    'requirements':'📋','ux-designer':'🎨','frontend':'🖼️',
    'backend':'⚙️','dba':'🗄️','security':'🔒','tester-unit':'🧪',
    'tester-qa':'✅','devops':'🚀','tech-writer':'📖','statworkbench':'🔬',
    'pptx-planner':'🗂️','pptx-content':'✍️','pptx-designer':'🖌️',
    'pptx-builder':'🔨','pptx-reviewer':'🔎',
    'architect':'🏗️','tester':'🧪',
}


def parse_metaverse_agents():
    """metaverse.html의 const AGENTS 배열을 파싱해 {id: {name, team}} 반환."""
    try:
        text = (_REPO_ROOT / 'metaverse.html').read_text(encoding='utf-8')
    except FileNotFoundError:
        return {}
    m = re.search(r'const AGENTS\s*=\s*\[([\s\S]*?)\];', text)
    if not m:
        return {}
    agents = {}
    for entry in re.finditer(r'\{([^}]+)\}', m.group(1)):
        fields = dict(re.findall(r"(\w+):'([^']+)'", entry.group(1)))
        if 'id' in fields and 'name' in fields and 'team' in fields:
            agents[fields['id']] = {'name': fields['name'], 'team': fields['team']}
    return agents


def scan_agents_folder():
    """agents/ 폴더 스캔 — role.md가 있는 하위 폴더를 에이전트로 인식."""
    agents_dir = _REPO_ROOT / 'agents'
    found = {}
    for d in sorted(agents_dir.iterdir()):
        if not d.is_dir():
            continue
        role_file = d / 'role.md'
        if not role_file.exists():
            continue
        agent_id = d.name
        # role.md 첫 번째 # 헤딩에서 이름 추출
        lines = role_file.read_text(encoding='utf-8', errors='ignore').splitlines()
        name = next((l.lstrip('# ').strip() for l in lines if l.startswith('# ')), agent_id)
        found[agent_id] = {'name': name}
    return found


def build_agent_list():
    """metaverse + agents/ 폴더 통합 목록. 팀 순서: lead → data → dev → pptx → 기타."""
    meta = parse_metaverse_agents()
    folder = scan_agents_folder()

    # metaverse 기준 우선, 폴더에만 있는 에이전트는 팀 'data'로 기본 배정
    merged = {}
    for ag_id, info in meta.items():
        merged[ag_id] = info
    for ag_id, info in folder.items():
        if ag_id not in merged:
            merged[ag_id] = {'name': info['name'], 'team': 'data'}

    # 팀 순서로 정렬
    order = {'lead': 0, 'data': 1, 'dev': 2, 'pptx': 3}
    return sorted(merged.items(), key=lambda x: (order.get(x[1]['team'], 9), x[0]))


AGENTS = build_agent_list()   # [(id, {name, team}), ...]

# ══════════════════════════════════════════════════════════════════
# 2. agent_status.json — 누락 에이전트 자동 등록
# ══════════════════════════════════════════════════════════════════

status_path = _REPO_ROOT / 'agent_status.json'
try:
    status_data = json.loads(status_path.read_text(encoding='utf-8'))
except Exception:
    status_data = {'agents': {}}

added_agents = []
for ag_id, _ in AGENTS:
    if ag_id not in status_data.get('agents', {}):
        status_data.setdefault('agents', {})[ag_id] = {
            'status': 'idle', 'task': '',
            'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'history': []
        }
        added_agents.append(ag_id)

if added_agents:
    status_path.write_text(json.dumps(status_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[build] agent_status.json 자동 등록: {added_agents}')

# ══════════════════════════════════════════════════════════════════
# 3. MD 콘텐츠 로드
# ══════════════════════════════════════════════════════════════════

try:
    with open(_SCRIPT_DIR / 'md_content.json', encoding='utf-8') as f:
        md_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    sys.exit(f'[build] md_content.json 오류: {e}')

md_json_str = json.dumps(md_data, ensure_ascii=False)
# HTML 파서가 </script>를 조기 종료로 해석하지 않도록 </를 <\/로 이스케이프
md_json_str = md_json_str.replace('</', '<\\/')

# ══════════════════════════════════════════════════════════════════
# 4. AGENT_NAMES JS 딕셔너리 자동 생성
# ══════════════════════════════════════════════════════════════════

agent_names_js = 'const AGENT_NAMES = {\n'
for ag_id, info in AGENTS:
    agent_names_js += f"  '{ag_id}':'{info['name']}',\n"
agent_names_js += '};'

# ══════════════════════════════════════════════════════════════════
# 5. MD 에디터 사이드바 HTML 자동 생성
# ══════════════════════════════════════════════════════════════════

def make_sidebar_html():
    lines = []
    for ag_id, info in AGENTS:
        team = info['team']
        emoji = AGENT_EMOJI.get(ag_id, '🤖')
        cls   = TEAM_CLS.get(team, 'team-data')
        label = TEAM_LABEL.get(team, team)
        icon  = f'<img src="assets/avatars/{ag_id}.png" alt="{ag_id}" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;border-radius:3px;flex-shrink:0;">'
        lines.append(
            f'          <div class="editor-agent-item" id="sidebar-{ag_id}" '
            f'onclick="editorSelect(\'{ag_id}\')">'
            f'{icon} {ag_id}'
            f'<span class="editor-agent-team {cls}">{label}</span></div>'
        )
    return '\n'.join(lines) + '\n'

sidebar_html = make_sidebar_html()

# ══════════════════════════════════════════════════════════════════
# 6. index.html 읽기
# ══════════════════════════════════════════════════════════════════

html = (_REPO_ROOT / 'index.html').read_text(encoding='utf-8')

# ── 6-1. MD 에디터 탭 버튼 추가 (최초 1회) ─────────────────────
if 'onclick="switchTab(\'editor\')"' not in html:
    old_tabs = "    <div class=\"tab\" onclick=\"switchTab('sync')\">☁️ GitHub 동기화</div>"
    new_tabs  = old_tabs + '\n    <div class="tab" onclick="switchTab(\'editor\')">✏️ MD 에디터</div>'
    html = html.replace(old_tabs, new_tabs, 1)

# ── 6-2. MD 에디터 CSS 추가 (최초 1회) ─────────────────────────
if '.editor-layout' not in html:
    editor_css = """
  /* ── MD 에디터 ── */
  .editor-layout { display:grid; grid-template-columns:220px 1fr; gap:16px; }
  .editor-sidebar { background:var(--surface); border:1px solid var(--border); border-radius:12px; overflow:hidden; max-height:700px; overflow-y:auto; }
  .editor-sidebar-title { padding:12px 16px; font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; border-bottom:1px solid var(--border); position:sticky; top:0; background:var(--surface); z-index:1; }
  .editor-agent-item { padding:9px 14px; cursor:pointer; font-size:11px; display:flex; align-items:center; gap:6px; border-bottom:1px solid rgba(48,54,61,.4); transition:.15s; }
  .editor-agent-item:hover { background:var(--surface2); }
  .editor-agent-item.active { background:rgba(56,139,253,.15); color:var(--blue); border-left:3px solid var(--blue); padding-left:11px; }
  .editor-agent-team { font-size:9px; padding:1px 5px; border-radius:8px; margin-left:auto; flex-shrink:0; }
  .editor-main { display:flex; flex-direction:column; gap:12px; min-width:0; }
  .editor-topbar { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:14px 18px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
  .editor-agent-name { font-size:15px; font-weight:700; flex:1; min-width:0; }
  .file-tab { padding:5px 12px; border-radius:6px; cursor:pointer; font-size:11px; border:1px solid var(--border); color:var(--muted); transition:.15s; }
  .file-tab.active { background:var(--blue); color:#fff; border-color:var(--blue); }
  .editor-actions { display:flex; gap:6px; flex-wrap:wrap; }
  .btn { padding:6px 12px; border-radius:6px; cursor:pointer; font-size:11px; font-weight:500; border:1px solid var(--border); transition:.15s; background:transparent; }
  .btn-copy { color:var(--text); } .btn-copy:hover { border-color:var(--blue); color:var(--blue); }
  .btn-prompt { color:var(--purple); border-color:rgba(188,140,255,.3); background:rgba(188,140,255,.1); } .btn-prompt:hover { background:rgba(188,140,255,.2); }
  .btn-link { color:var(--green); border-color:rgba(63,185,80,.3); background:rgba(63,185,80,.1); } .btn-link:hover { background:rgba(63,185,80,.2); }
  .btn-save { color:var(--blue); border-color:rgba(56,139,253,.3); background:rgba(56,139,253,.1); } .btn-save:hover { background:rgba(56,139,253,.2); }
  .editor-box { background:var(--surface); border:1px solid var(--border); border-radius:10px; overflow:hidden; }
  .editor-box-header { padding:10px 16px; background:var(--surface2); border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; font-size:11px; color:var(--muted); }
  .editor-textarea { width:100%; min-height:540px; background:var(--bg); color:var(--text); border:none; padding:16px 18px; font-family:'Malgun Gothic',monospace; font-size:13px; line-height:1.8; resize:vertical; outline:none; }
  .editor-path { font-family:monospace; font-size:11px; color:var(--orange); }
  .toast { position:fixed; bottom:28px; right:28px; background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:12px 20px; font-size:13px; color:var(--text); z-index:300; transform:translateY(80px); opacity:0; transition:.3s ease; pointer-events:none; max-width:420px; }
  .toast.show { transform:translateY(0); opacity:1; } .toast.success { border-color:var(--green); color:var(--green); } .toast.warn { border-color:var(--yellow); color:var(--yellow); }
  .editor-info { background:rgba(56,139,253,.07); border:1px solid rgba(56,139,253,.2); border-radius:8px; padding:12px 16px; font-size:12px; color:var(--muted); line-height:1.9; margin-bottom:8px; }
  @media (max-width:900px) { .editor-layout { grid-template-columns:1fr; } .editor-sidebar { max-height:180px; } }
"""
    html = html.replace('</style>', editor_css + '</style>', 1)

# ── 6-3. GitHub 동기화 탭 통계 항상 최신화 ─────────────────────
count = len(AGENTS)
# role.md + memory.md 파일 수
file_count = sum(
    1 for ag_id, _ in AGENTS
    for fname in ('role.md', 'memory.md')
    if (_REPO_ROOT / 'agents' / ag_id / fname).exists()
)
html = re.sub(
    r'(<div class="sync-card-title">총 에이전트 파일</div>\s*<div class="sync-card-value">)\d+(</div>)',
    rf'\g<1>{file_count}\2', html
)
html = re.sub(
    r'(<div class="sync-card-title">등록 에이전트</div>\s*<div class="sync-card-value">)\d+(</div>)',
    rf'\g<1>{count}\2', html
)

# ── 6-3c. 상단 subtitle 총 에이전트 수 항상 최신화 ─────────────
html = re.sub(
    r'총 \d+개 에이전트',
    f'총 {count}개 에이전트', html
)

# ── 6-3d. 에이전트 목록 탭 팀 인원수 항상 최신화 ───────────────
team_counts = {}
for ag_id, info in AGENTS:
    t = info['team']
    team_counts[t] = team_counts.get(t, 0) + 1

team_name_map = {
    'data': '빅데이터 분석팀',
    'dev': '웹앱 개발팀',
    'pptx': '디자인팀',
    'lead': '총괄 · 리드 에이전트',
}
for team_key, team_label in team_name_map.items():
    cnt = team_counts.get(team_key, 0)
    if cnt:
        html = re.sub(
            r'(<div class="team-name">' + re.escape(team_label) + r'</div><div class="team-count">)\d+명(</div>)',
            rf'\g<1>{cnt}명\2', html
        )

# ── 6-3d. MD 에디터 사이드바 항상 최신화 ───────────────────────
if 'id="tab-editor"' in html:
    new_sb = (
        f'<div class="editor-sidebar-title">에이전트 선택 ({count}개)</div>\n'
        f'{sidebar_html}      '
    )
    html = re.sub(
        r'<div class="editor-sidebar-title">에이전트 선택[^<]*</div>\n[\s\S]*?(?=      </div>\n      <div class="editor-main">)',
        new_sb, html, count=1
    )

# ── 6-4. MD 에디터 탭 HTML (최초 1회) ──────────────────────────
if 'id="tab-editor"' not in html:
    editor_tab = f"""
  <!-- ══════════════════════════════════════
       탭 6: MD 에디터
  ══════════════════════════════════════ -->
  <div id="tab-editor" class="tab-content">
    <div class="editor-info">
      ✏️ 에이전트의 <strong>role.md</strong> · <strong>memory.md</strong> 열림 및 편집 &nbsp;|&nbsp;
      <strong>Copy as Markdown</strong>: 원본 복사 &nbsp;|&nbsp;
      <strong>Copy as Prompt</strong>: Claude에 바로 붙여넣기 가능한 형태로 복사 &nbsp;|&nbsp;
      <strong>공유 링크</strong>: 현재 에이전트 URL 복사 &nbsp;|&nbsp;
      <strong>수정 후 복사</strong>: 편집 후 실제 .md 파일에 붙여넣기
    </div>
    <div class="editor-layout">
      <div class="editor-sidebar">
        <div class="editor-sidebar-title">에이전트 선택 ({count}개)</div>
{sidebar_html}      </div>
      <div class="editor-main">
        <div class="editor-topbar">
          <div class="editor-agent-name" id="editor-agent-name">← 에이전트를 선택하세요</div>
          <div style="display:flex;gap:6px;flex-shrink:0;">
            <div class="file-tab active" id="file-tab-role" onclick="editorSwitchFile('role')">role.md</div>
            <div class="file-tab" id="file-tab-memory" onclick="editorSwitchFile('memory')">memory.md</div>
          </div>
          <div class="editor-actions">
            <button class="btn btn-copy" onclick="copyAsMarkdown()">📋 Copy as Markdown</button>
            <button class="btn btn-prompt" onclick="copyAsPrompt()">🤖 Copy as Prompt</button>
            <button class="btn btn-link" onclick="copyShareLink()">🔗 공유 링크</button>
            <button class="btn btn-save" onclick="copyEdited()">💾 수정 후 복사</button>
          </div>
        </div>
        <div class="editor-box">
          <div class="editor-box-header">
            <span id="editor-file-path" class="editor-path">에이전트를 선택하면 내용이 표시됩니다</span>
            <span id="editor-char-count" style="color:var(--muted);font-size:11px;"></span>
          </div>
          <textarea class="editor-textarea" id="editor-textarea"
            placeholder="← 왼쪽에서 에이전트를 선택하세요&#10;&#10;선택하면 role.md 또는 memory.md 내용이 여기 표시됩니다.&#10;직접 편집 후 [수정 후 복사]로 클립보드에 복사하여 실제 파일에 붙여넣기 하세요."
            oninput="updateCharCount()"></textarea>
        </div>
      </div>
    </div>
  </div>
"""
    marker = '</div>\n\n<!-- ══════════════════════════════════════\n     모달'
    html = html.replace(marker, editor_tab + '</div>\n\n<!-- ══════════════════════════════════════\n     모달', 1)

# ── 6-5. 모달 MD 편집 버튼 (최초 1회) ──────────────────────────
if 'openEditorFromModal' not in html:
    old_btn = '      <button class="modal-close" onclick="closeModal()">닫기</button>'
    new_btn = (old_btn + '\n      <button class="modal-close" '
               'style="background:rgba(56,139,253,.15);color:var(--blue);border-color:rgba(56,139,253,.3);margin-left:4px;" '
               'onclick="openEditorFromModal()">✏️ MD 편집</button>')
    html = html.replace(old_btn, new_btn, 1)

# ── 6-6. 탭 스위칭 업데이트 (최초 1회) ─────────────────────────
if "TABS=['metaverse'" not in html:
    old_sw = ("function switchTab(name) {\n"
              "  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('active', ['metaverse','agents','pipeline','comms','sync'][i]===name));\n"
              "  document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));\n"
              "  document.getElementById('tab-'+name).classList.add('active');\n"
              "}")
    new_sw = ("function switchTab(name) {\n"
              "  const TABS=['metaverse','agents','pipeline','comms','sync','editor'];\n"
              "  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('active', TABS[i]===name));\n"
              "  document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));\n"
              "  document.getElementById('tab-'+name).classList.add('active');\n"
              "  if(name==='editor') updateURL();\n"
              "}")
    html = html.replace(old_sw, new_sw, 1)

# ── 6-7. JS: AGENT_NAMES + MD_CONTENT + 에디터 함수 ────────────
old_end = ("// 동기화 상태\n"
           "document.getElementById('syncStatus').textContent = 'github.com/your-github-username/agent';\n"
           "document.getElementById('lastSync').textContent = new Date().toLocaleDateString('ko-KR', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});\n"
           "</script>")

editor_js = r"""
// ── MD 에디터 데이터 ──
const MD_CONTENT = """ + md_json_str + ";\n\n" + agent_names_js + r"""

let currentAgent = null;
let currentFile = 'role';

function editorSelect(id) {
  currentAgent = id;
  document.querySelectorAll('.editor-agent-item').forEach(el=>el.classList.remove('active'));
  const si = document.getElementById('sidebar-'+id);
  if(si) { si.classList.add('active'); si.scrollIntoView({block:'nearest'}); }
  document.getElementById('editor-agent-name').textContent = (AGENT_NAMES[id]||id)+' ('+id+')';
  loadEditorContent();
  updateURL();
}

function editorSwitchFile(file) {
  currentFile = file;
  document.getElementById('file-tab-role').classList.toggle('active', file==='role');
  document.getElementById('file-tab-memory').classList.toggle('active', file==='memory');
  loadEditorContent();
  updateURL();
}

function loadEditorContent() {
  if(!currentAgent) return;
  const data = MD_CONTENT[currentAgent];
  const content = data ? (data[currentFile]||'(내용 없음)') : '(데이터 없음)';
  const ta = document.getElementById('editor-textarea');
  ta.value = content;
  document.getElementById('editor-file-path').textContent = 'agents/'+currentAgent+'/'+currentFile+'.md';
  updateCharCount();
}

function updateCharCount() {
  const ta = document.getElementById('editor-textarea');
  const lines = (ta.value.match(/\n/g)||[]).length + 1;
  document.getElementById('editor-char-count').textContent = lines+'행 · '+ta.value.length+'자';
}

function copyAsMarkdown() {
  const content = document.getElementById('editor-textarea').value;
  if(!content.trim()) return showToast('먼저 에이전트를 선택하세요', 'warn');
  navigator.clipboard.writeText(content).then(()=>showToast('📋 Markdown 복사 완료!','success'));
}

function copyAsPrompt() {
  if(!currentAgent) return showToast('먼저 에이전트를 선택하세요','warn');
  const roleMd = MD_CONTENT[currentAgent]?.role || '';
  const memMd  = MD_CONTENT[currentAgent]?.memory || '';
  const name   = AGENT_NAMES[currentAgent] || currentAgent;
  const prompt = '# 역할 지시\n당신은 Your Organization 멀티 에이전트 시스템의 **'+name+'** 에이전트입니다.\n아래 역할 정의와 기억을 숙지한 후, 주어진 작업을 수행해 주세요.\n\n---\n\n## role.md\n'+roleMd+'\n---\n\n## memory.md\n'+(memMd||'(축적된 경험 없음)')+'\n\n---\n\n# 현재 작업\n[여기에 작업 지시를 입력하세요]';
  navigator.clipboard.writeText(prompt).then(()=>showToast('🤖 Claude 프롬프트 복사 완료! Claude에 붙여넣기 하세요.','success'));
}

function copyEdited() {
  const content = document.getElementById('editor-textarea').value;
  if(!content.trim()) return showToast('내용이 없습니다','warn');
  const fname = (currentAgent||'?')+'/'+currentFile+'.md';
  navigator.clipboard.writeText(content).then(()=>showToast('💾 복사 완료! agents/'+fname+' 에 붙여넣기 하세요','success'));
}

function copyShareLink() {
  if(!currentAgent) return showToast('먼저 에이전트를 선택하세요','warn');
  const url = location.origin+location.pathname+'?tab=editor&agent='+currentAgent+'&file='+currentFile;
  navigator.clipboard.writeText(url).then(()=>showToast('🔗 공유 링크 복사 완료!','success'));
}

function updateURL() {
  if(!currentAgent) return;
  const url = new URL(location.href);
  url.searchParams.set('tab','editor');
  url.searchParams.set('agent',currentAgent);
  url.searchParams.set('file',currentFile);
  history.replaceState(null,'',url.toString());
}

let _modalCurrentAgent = null;
const _origOpenModal = openModal;
openModal = function(id) { _modalCurrentAgent=id; _origOpenModal(id); };

function openEditorFromModal() {
  closeModal();
  switchTab('editor');
  if(_modalCurrentAgent) setTimeout(()=>editorSelect(_modalCurrentAgent),50);
}

function showToast(msg, type) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast '+(type||'success');
  void t.offsetWidth;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(()=>t.classList.remove('show'), 3200);
}

// URL 파라미터 처리 (페이지 로드 시 자동 라우팅)
(function() {
  const p = new URLSearchParams(location.search);
  const tab=p.get('tab'), agent=p.get('agent'), file=p.get('file');
  if(tab) {
    switchTab(tab);
    if(tab==='editor' && agent) {
      if(file==='memory') { currentFile='memory'; editorSwitchFile('memory'); }
      setTimeout(()=>editorSelect(agent),80);
    } else if((tab==='metaverse'||tab==='agents') && agent) {
      setTimeout(()=>openModal(agent),120);
    }
  }
})();
</script>"""

new_end = ("// 동기화 상태\n"
           "document.getElementById('syncStatus').textContent = 'github.com/your-github-username/agent';\n"
           "document.getElementById('lastSync').textContent = new Date().toLocaleDateString('ko-KR', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});\n"
           + editor_js)

html = html.replace(old_end, new_end, 1)

# ── 6-8. 토스트 div (최초 1회) ──────────────────────────────────
if 'id="toast"' not in html:
    html = html.replace('</body>', '<div class="toast" id="toast"></div>\n</body>', 1)

# ══════════════════════════════════════════════════════════════════
# 7. 저장
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# 8. Claude Code 상태 주입 (스킬·훅 KPI + 드릴다운 데이터)
# ══════════════════════════════════════════════════════════════════

# 8-1. KPI 카드: 스킬 숫자
html = re.sub(
    r'(<div class="v2-kpi-num" id="v2-kpi-skills-num">)[^<]*(</div>)',
    rf'\g<1>{CC_STATUS["skill_count"]}\g<2>',
    html, count=1
)

# 8-2. KPI 카드: 훅 숫자 + delta
html = re.sub(
    r'(<div class="v2-kpi" onclick="v2ShowKpiDetail\(\'hooks\'\)">)'
    r'(<div class="v2-kpi-num">)[^<]*(</div>)'
    r'(<div class="v2-kpi-lbl">훅</div>)'
    r'(<div class="v2-kpi-delta neu">)[^<]*(</div>)',
    rf'\g<1>\g<2>{CC_STATUS["hook_count"]}\g<3>\g<4>'
    rf'\g<5>{CC_STATUS["hook_events"]} 이벤트\g<6>',
    html, count=1
)

# 8-3. JS 상수 V2_HOOKS_DATA, V2_CC_SKILLS 교체 (드릴다운 세부 데이터)
skills_js = json.dumps(CC_STATUS['skills'], ensure_ascii=False)
hooks_js_list = []
for event, items in CC_STATUS['hooks'].items():
    items_js = json.dumps(items, ensure_ascii=False)
    hooks_js_list.append(f'  {{ event:{json.dumps(event, ensure_ascii=False)}, items:{items_js} }}')
hooks_js = '[\n' + ',\n'.join(hooks_js_list) + '\n]'

html = re.sub(
    r'const V2_HOOKS_DATA = \[[\s\S]*?\];',
    f'const V2_HOOKS_DATA = {hooks_js};',
    html, count=1
)

# CC 스킬 목록 + 레포 스킬 상수 주입
repo_skills_js = json.dumps(CC_STATUS.get('repo_skills', []), ensure_ascii=False)
cc_skills_const = f'const V2_CC_SKILLS = {skills_js};\nconst V2_REPO_SKILLS = {repo_skills_js};'
if 'const V2_CC_SKILLS' in html:
    html = re.sub(
        r'const V2_CC_SKILLS = \[[\s\S]*?\];(\s*const V2_REPO_SKILLS = \[[\s\S]*?\];)?',
        cc_skills_const, html, count=1
    )
else:
    html = html.replace('const V2_HOOKS_DATA', cc_skills_const + '\nconst V2_HOOKS_DATA', 1)

# 8-4. 스킬 드릴다운: 레포 스킬(🔗)과 로컬 스킬 구분 표시
old_skill_detail = "const skillMap = {};\n    Object.entries(AGENTS).forEach(([id, a]) => {\n      (a.skills||[]).forEach(s => {\n        if (!skillMap[s]) skillMap[s] = [];\n        skillMap[s].push(a.name);\n      });\n    });\n    const skills = Object.entries(skillMap).sort((a,b) => b[1].length - a[1].length);\n    countText = skills.length + '개 고유 스킬';\n    html += '<div style=\"display:flex;flex-direction:column;gap:5px;\">';\n    skills.forEach(([skill, names]) => {\n      html += `<div class=\"v2-skill-row\">\n        <span>${skill}</span>\n        <span class=\"v2-skill-agents\">${names.slice(0,3).join(', ')}${names.length>3?' 외 '+(names.length-3)+'명':''}</span>\n      </div>`;\n    });\n    html += '</div>';"
new_skill_detail = f"""const ccSkills = typeof V2_CC_SKILLS !== 'undefined' ? V2_CC_SKILLS : [];
    const repoSkills = typeof V2_REPO_SKILLS !== 'undefined' ? new Set(V2_REPO_SKILLS) : new Set();
    countText = ccSkills.length + '개 설치됨 (레포 ' + repoSkills.size + '개 포함)';
    html += '<div style="display:flex;flex-direction:column;gap:5px;">';
    ccSkills.forEach(skill => {{
      const isRepo = repoSkills.has(skill);
      const badge = isRepo ? '<span style="font-size:9px;background:#1A3A6B;color:#fff;border-radius:3px;padding:1px 4px;margin-left:4px;">레포</span>' : '';
      html += `<div class="v2-skill-row"><span>${{skill}}${{badge}}</span><span class="v2-skill-agents">${{isRepo ? '에이전트 공유' : '로컬'}}</span></div>`;
    }});
    html += '</div>';"""

if old_skill_detail in html:
    html = html.replace(old_skill_detail, new_skill_detail, 1)

(_REPO_ROOT / 'index.html').write_text(html, encoding='utf-8')

# ══════════════════════════════════════════════════════════════════
# 9. metaverse.html — CC 스킬·훅·레포스킬 카운트 자동 갱신
# ══════════════════════════════════════════════════════════════════
mv_path = _REPO_ROOT / 'metaverse.html'
if mv_path.exists():
    mv = mv_path.read_text(encoding='utf-8')
    repo_skill_cnt = len(CC_STATUS.get('repo_skills', []))
    mv = re.sub(r'(<div[^>]*id="mv-skill-count"[^>]*>)[^<]*(</div>)',
                rf'\g<1>{CC_STATUS["skill_count"]}\g<2>', mv, count=1)
    mv = re.sub(r'(<div[^>]*id="mv-hook-count"[^>]*>)[^<]*(</div>)',
                rf'\g<1>{CC_STATUS["hook_count"]}\g<2>', mv, count=1)
    mv = re.sub(r'(<div[^>]*id="mv-repo-skill-count"[^>]*>)[^<]*(</div>)',
                rf'\g<1>{repo_skill_cnt}\g<2>', mv, count=1)
    # MV 스킬·훅 상세 데이터 주입
    mv_data = collect_mv_skill_data()
    mv_skill_js  = json.dumps(mv_data['skills'],      ensure_ascii=False)
    mv_repo_js   = json.dumps(mv_data['repoContent'], ensure_ascii=False)
    mv_hooks_list = [{'event': k, 'items': v} for k, v in CC_STATUS['hooks'].items()]
    mv_hooks_js  = json.dumps(mv_hooks_list,           ensure_ascii=False)
    # lambda 사용 — re.sub가 \n 등을 이스케이프 해석하지 않도록 방지
    _s = f'const MV_SKILL_DATA = {mv_skill_js};\n'
    _r = f'const MV_REPO_CONTENT = {mv_repo_js};\n'
    _h = f'const MV_HOOKS_DATA = {mv_hooks_js};\n'
    mv = re.sub(r'const MV_SKILL_DATA\s*=\s*\[[\s\S]*?(?=\nconst MV_REPO_CONTENT)',
                lambda _: _s, mv, count=1)
    mv = re.sub(r'const MV_REPO_CONTENT\s*=\s*[\s\S]*?(?=\nconst MV_HOOKS_DATA)',
                lambda _: _r, mv, count=1)
    mv = re.sub(r'const MV_HOOKS_DATA\s*=\s*\[[\s\S]*?(?=\n\nfunction mvShowDp)',
                lambda _: _h, mv, count=1)
    mv_path.write_text(mv, encoding='utf-8')

print(f'Done. 에이전트 {count}명 반영 | CC 스킬 {CC_STATUS["skill_count"]}개 · 훅 {CC_STATUS["hook_count"]}개 | 레포스킬 {len(CC_STATUS.get("repo_skills",[]))}개 | 파일 크기: {len(html):,} bytes / {len(html.encode())//1024} KB')
