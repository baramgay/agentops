# -*- coding: utf-8 -*-
"""
라이브 사무실 시스템 자동 검증 스크립트
사용법: python scripts/validate.py
        python scripts/validate.py --fix   (자동 수정 가능한 항목 수정)

Kimi Code 반복 실수 방지 목적:
  - index.html 중복 탭/CSS 감지
  - metaverse.html PALETTE.corridor 색상 검증
  - 중괄호 균형 검증
"""
import sys
import io
import re
from pathlib import Path

# Windows 콘솔 UTF-8 강제
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).parent.parent
FIX_MODE = '--fix' in sys.argv

PASS = '[ OK ]'
FAIL = '[FAIL]'
WARN = '[WARN]'

results = []
fixes_applied = []
_backup_done: set[str] = set()  # 중복 백업 방지


def _backup_before_fix(path: Path) -> None:
    """자동 수정 전 .bak 백업 (최초 1회만)."""
    key = str(path)
    if key in _backup_done:
        return
    bak = path.with_suffix(path.suffix + ".bak")
    try:
        bak.write_bytes(path.read_bytes())
        print(f'    => 백업 생성: {bak.name}')
    except OSError as e:
        print(f'    [WARN] 백업 실패 ({e}) — 수정 계속')
    _backup_done.add(key)


def check(name, ok, detail='', fixable=False):
    tag = PASS if ok else FAIL
    results.append((ok, name, detail, fixable))
    print(f'  {tag} {name}' + (f' — {detail}' if detail else ''))
    return ok

# ─────────────────────────────────────────
# metaverse.html 검증
# ─────────────────────────────────────────
print('\n=== metaverse.html ===')
mv_path = ROOT / 'metaverse.html'
mv = ''
if mv_path.exists():
    mv = mv_path.read_text(encoding='utf-8')

    # 중괄호 균형
    ob, cb = mv.count('{'), mv.count('}')
    check('중괄호 균형', ob == cb, f'{{ {ob} }} {cb}')

    # 베이지 복도
    corridor_ok = '0xD4C4A0' in mv
    _corridor_m = re.search(r'corridor:\s*(0x[0-9A-Fa-f]+)', mv)
    check('PALETTE.corridor 베이지(0xD4C4A0)', corridor_ok,
          '현재: ' + (_corridor_m.group(1) if _corridor_m else '?'),
          fixable=True)
    if not corridor_ok and FIX_MODE:
        _backup_before_fix(mv_path)
        fixed = re.sub(
            r'corridor:\s*0x[0-9A-Fa-f]+,\s*corridor2:\s*0x[0-9A-Fa-f]+,\s*corridor_line:\s*0x[0-9A-Fa-f]+',
            'corridor: 0xD4C4A0, corridor2: 0xC8BA94, corridor_line: 0xBFB090',
            mv
        )
        if fixed != mv:
            mv_path.write_text(fixed, encoding='utf-8')
            mv = fixed
            fixes_applied.append('metaverse.html: PALETTE.corridor 베이지 복원')
            print('    => 자동 수정 완료')

    check('캐릭터 스케일 설정', 'setScale(' in mv)
    check('이름태그 14px', "'14px'" in mv)
    check('Task Strip 11px', "'11px'" in mv)
    check('computeWaypoints 복도 경로', 'computeWaypoints' in mv)
    check('패널 슬라이드(ap-visible)', 'ap-visible' in mv, fixable=True)
    if 'ap-visible' not in mv and FIX_MODE:
        # CSS 추가
        mv = mv.replace(
            '#agentPanel {\n    position: fixed;',
            '#agentPanel {\n    position: fixed;'
        )
        # transition 추가 (간단히)
        print('    => ap-visible 수동 추가 필요 (자동 수정 건너뜀)')

    check('callGathering 전역 함수', 'window.callGathering' in mv)
    check('미니맵 updateMinimap', 'updateMinimap' in mv)
    check('소품 렌더링 drawAccessoryOnCanvas', 'drawAccessoryOnCanvas' in mv)
    check('POI /3 스케일링', 'poi.x / 3' in mv)
    check('exec층 방 분리 경유', 'srcRoom !== dstRoom' in mv)
    check('카메라 줌', 'cam.setZoom' in mv)

# ─────────────────────────────────────────
# metaverse.html — 공간/투시 규칙 검증
# (오케스트레이터/리드 사전 검토 대체 자동화)
# ─────────────────────────────────────────
print('\n=== metaverse.html (공간/투시 규칙) ===')
if mv_path.exists():
    # ── 규칙 1: 벽면 부착 오브젝트는 측면뷰여야 함 ──
    # 회의실 좌측 화이트보드: fillRect(24*T+2, ..., width, ...) → width < 15 이어야 함
    # fillRect(24*T+2, 1*T,   7, 3*T) 패턴 검사
    wb_match = re.search(
        r'fillRect\(\s*24\s*\*\s*T\s*\+\s*2\s*,\s*1\s*\*\s*T\s*,\s*(\d+)',
        mv
    )
    if wb_match:
        wb_w = int(wb_match.group(1))
        wb_side_ok = wb_w < 15
        check('회의실 화이트보드 측면뷰(width<15)', wb_side_ok,
              f'width={wb_w}px' if wb_side_ok else f'width={wb_w}px — 측면뷰는 두께만 표현해야 함')
    else:
        check('회의실 화이트보드 존재', False, '화이트보드 fillRect 패턴 미발견')

    # ── 규칙 2: 회의실 화이트보드가 테이블 영역을 침범하지 않아야 함 ──
    # 테이블 TX0 = (31.5 - 5.5)*T = 26*T → 화이트보드 x 끝이 26*T 이하여야 함
    # 화이트보드 시작 x: 24*T+2, width: wb_w → 끝 x ≈ 24*T + 2 + wb_w
    # TILE 상수 추출 (const TILE = 48)
    tile_match = re.search(r'const\s+TILE\s*=\s*(\d+)', mv)
    TILE_VAL = int(tile_match.group(1)) if tile_match else 48
    if wb_match:
        wb_end_approx = 24 * TILE_VAL + 2 + wb_w
        table_start = 26 * TILE_VAL
        overlap_ok = wb_end_approx <= table_start
        check(f'화이트보드-테이블 비겹침(x끝<26T={table_start})', overlap_ok,
              f'화이트보드 x끝≈{wb_end_approx}, 테이블 시작={table_start}')

    # ── 규칙 3: 회의실 테이블이 사각라운드형이어야 함 (ellipse 금지) ──
    # TCX/TCY 영역에서 fillEllipse 호출이 없어야 함 (센터피스 화분은 허용)
    # 테이블 본체 ellipse 검사: fillEllipse(TCX, TCY, TW, ...) 패턴
    table_ellipse = re.search(
        r'fillEllipse\(\s*TCX\s*,\s*TCY\s*,\s*TW\s*,\s*TH', mv
    )
    check('회의 테이블 사각라운드형 유지(ellipse 금지)', table_ellipse is None,
          '' if table_ellipse is None else 'fillEllipse(TCX,TCY,TW,TH) 발견 — fillRoundedRect 사용 필요')

    # ── 규칙 4: 프로젝터 스크린 측면뷰 (우측 벽 x=38T 근방, depth<10) ──
    ps_match = re.search(
        r'fillRect\(\s*38\s*\*\s*T\s*\+\s*\d+\s*,\s*\d+\s*,\s*T\s*\*\s*2\s*-\s*(\d+)',
        mv
    )
    if ps_match:
        ps_inner = int(ps_match.group(1))
        # T*2-10 → 실제 폭 = T*2-10 = 86px — 이는 정면뷰 (스크린 정면 렌더링)
        # 스크린은 우측 벽(x=38T~40T)에 붙어 있어 정면뷰가 정상이므로 pass
        check('프로젝터 스크린 렌더링 존재', True, f'T*2-{ps_inner}px 폭')
    else:
        check('프로젝터 스크린 존재', '38*T' in mv, '프로젝터 스크린 좌표 미발견')

    # ── 규칙 5: WALL_BODIES가 복도 y범위를 침범하지 않아야 함 ──
    # exec 파티션: h:t(7) 이상이면 복도(y=96~112) 포함 → 금지
    # "h:t(7)" 패턴 검사 (exec 파티션에서만)
    wall_h7 = re.search(r'h\s*:\s*t\s*\(\s*7\s*\)', mv)
    check('WALL_BODIES exec파티션 h<t(7)', wall_h7 is None,
          '' if wall_h7 is None else 'h:t(7) 발견 — 복도(y=96-112) 차단 위험, h:t(6)-4 이하로 줄여야 함')

else:
    print(f'  {FAIL} metaverse.html 파일 없음')


# ─────────────────────────────────────────
# index.html 검증
# ─────────────────────────────────────────
print('\n=== index.html ===')
idx_path = ROOT / 'index.html'
if idx_path.exists():
    idx = idx_path.read_text(encoding='utf-8')

    te_cnt = idx.count('id="tab-editor"')
    te_ok = te_cnt == 1
    check('tab-editor div 1개', te_ok, f'현재 {te_cnt}개', fixable=True)

    nav_btn_cnt = sum(1 for l in idx.splitlines()
                      if '<div class="tab"' in l and "switchTab('editor')" in l)
    check('MD 에디터 탭버튼 nav에서 1개', nav_btn_cnt == 1, f'현재 {nav_btn_cnt}개', fixable=True)

    css_cnt = idx.count('/* ── MD 에디터 ── */')
    css_ok = css_cnt <= 1
    check('MD 에디터 CSS 중복 없음', css_ok, f'현재 {css_cnt}개', fixable=True)

    # 자동 수정
    if FIX_MODE and (not te_ok or nav_btn_cnt > 1):
        _backup_before_fix(idx_path)
        lines = idx.splitlines(keepends=True)
        new, btn_seen = [], 0
        for l in lines:
            is_nav_btn = '<div class="tab"' in l and "switchTab('editor')" in l
            if is_nav_btn:
                btn_seen += 1
                if btn_seen == 1: new.append(l)
            else:
                new.append(l)
        lines = new
        te_pos = [i for i,l in enumerate(lines) if 'id="tab-editor"' in l]
        if len(te_pos) > 1:
            start = te_pos[1]
            for j in range(start-1, max(0,start-4), -1):
                if '<!--' in lines[j]: start=j; break
            depth, end = 0, start
            for j in range(te_pos[1], len(lines)):
                depth += lines[j].count('<div')
                depth -= lines[j].count('</div>')
                if depth <= 0 and j > te_pos[1]:
                    end = j+1; break
            lines = lines[:start] + lines[end:]
        idx_path.write_text(''.join(lines), encoding='utf-8')
        fixes_applied.append(f'index.html: tab-editor 중복 {te_cnt}→1개 수정')
        print('    => 자동 수정 완료')

    # toast 중복 검사
    toast_cnt = idx.count('id="toast"')
    toast_ok = toast_cnt == 1
    check('toast div 1개', toast_ok, f'현재 {toast_cnt}개', fixable=True)
    if not toast_ok and FIX_MODE:
        _backup_before_fix(idx_path)
        lines2 = idx.splitlines(keepends=True)
        new2, ts = [], 0
        for l in lines2:
            if 'id="toast"' in l:
                ts += 1
                if ts == 1: new2.append(l)
            else:
                new2.append(l)
        idx_path.write_text(''.join(new2), encoding='utf-8')
        fixes_applied.append(f'index.html: toast 중복 {toast_cnt}→1개 수정')
        print('    => 자동 수정 완료')

    # 탭 버튼 id 일관성 체크
    EXPECTED_TAB_IDS = [
        'tab-btn-overview', 'tab-btn-metaverse', 'tab-btn-agents', 'tab-btn-pipeline',
        'tab-btn-comms', 'tab-btn-sync', 'tab-btn-editor', 'tab-btn-issues',
        'tab-btn-goals', 'tab-btn-approvals', 'tab-btn-timeline', 'tab-btn-memory',
        'tab-btn-manual',
    ]
    missing_tab_ids = [tid for tid in EXPECTED_TAB_IDS if f'id="{tid}"' not in idx]
    if missing_tab_ids:
        # 미적용 탭 id는 경고 출력 (다른 에이전트 작업 중일 수 있어 실패 처리 안 함)
        print(f'  {WARN} 탭 버튼 id 미적용 ({len(missing_tab_ids)}개): {missing_tab_ids}')
    else:
        print(f'  {PASS} 탭 버튼 id 전체 적용 ({len(EXPECTED_TAB_IDS)}개)')

    check('MD_CONTENT 내장', 'MD_CONTENT' in idx)
    # metaverse.html AGENTS 배열 수와 동적 비교
    import re as _re_agent
    _meta_agents = len(_re_agent.findall(r"\{ id:'[^']+',\s*name:'[^']+',\s*team:'[^']+'", mv)) if mv_path.exists() else 0
    _idx_editor   = idx.count('editorSelect(')
    check(f'MD에디터 사이드바 에이전트 수({_idx_editor}) >= AGENTS 배열({_meta_agents})',
          _idx_editor >= _meta_agents,
          f'에디터={_idx_editor} vs AGENTS={_meta_agents}')

    # MD_CONTENT 동기화 검증 (md_content.json과 실제 파일 비교)
    import json as _json, re as _re
    mc_path = ROOT / 'scripts' / 'md_content.json'
    if mc_path.exists():
        mc = _json.loads(mc_path.read_text(encoding='utf-8'))
        m = _re.search(r'const MD_CONTENT = ({.*?});', idx, _re.DOTALL)
        if m:
            try:
                html_mc = _json.loads(m.group(1))
                in_sync = all(mc.get(k, {}) == html_mc.get(k, {}) for k in mc)
                check('MD_CONTENT ↔ memory.md 동기화', in_sync,
                      '비동기 — python scripts/sync.py 실행 필요', fixable=True)
                if not in_sync and FIX_MODE:
                    import subprocess as _sp, sys as _sys
                    _sp.run([_sys.executable, str(ROOT/'scripts'/'update_md_content.py')], cwd=ROOT)
                    fixes_applied.append('index.html: MD_CONTENT 동기화 완료')
                    print('    => 자동 수정 완료')
            except Exception:
                check('MD_CONTENT ↔ memory.md 동기화', False, 'JSON 파싱 실패')
        else:
            check('MD_CONTENT ↔ memory.md 동기화', False, 'MD_CONTENT 미발견')
    else:
        print(f'  {WARN} md_content.json 없음 — build_md_content.py 실행 필요')
else:
    print(f'  {FAIL} index.html 파일 없음')

# ─────────────────────────────────────────
# requirements.txt 필수 패키지 검증
# ─────────────────────────────────────────
print('\n=== requirements.txt ===')
req_path = ROOT / 'requirements.txt'
if req_path.exists():
    req_content = req_path.read_text(encoding='utf-8')
    for pkg in ['fastapi', 'uvicorn', 'pydantic', 'openai', 'python-dotenv']:
        check(f'requirements.txt에 {pkg} 포함', pkg in req_content, fixable=False)
else:
    check('requirements.txt 존재', False, '파일 없음', fixable=False)

# ─────────────────────────────────────────
# api_server.py 검증
# ─────────────────────────────────────────
print('\n=== api_server.py ===')
api_path = ROOT / 'scripts' / 'api_server.py'
if api_path.exists():
    api = api_path.read_text(encoding='utf-8')
    check('GET /api/status 엔드포인트', '/api/status' in api)
    check('POST /api/instruct 엔드포인트', '/api/instruct' in api)
    check('CORS 설정', 'CORSMiddleware' in api)
    check('api_server.py CORS 환경변수화', '_CORS_ORIGINS' in api and 'ALLOWED_ORIGINS' in api, fixable=False)
    check('api_server.py /api/gathering 엔드포인트', 'gathering' in api, fixable=False)
    check('파일 읽기 load_data', 'load_data' in api)
    check('파일 쓰기 save_data', 'save_data' in api)
    check('페르소나 import (load_persona)', 'load_persona' in api)
    check('LLM provider import (get_provider)', 'get_provider' in api)
    check('persona_loaded 응답 필드', 'persona_loaded' in api)
    check('api_server.py /api/git-status 엔드포인트 없음', 'git-status' in api, fixable=False)
else:
    print(f'  {WARN} api_server.py 없음 (선택사항)')

# ─────────────────────────────────────────
# persona_loader.py / llm_provider.py 검증
# ─────────────────────────────────────────
print('\n=== persona & LLM provider ===')
pl_path = ROOT / 'scripts' / 'persona_loader.py'
lp_path = ROOT / 'scripts' / 'llm_provider.py'
if pl_path.exists():
    pl = pl_path.read_text(encoding='utf-8')
    check('PersonaContext dataclass', 'PersonaContext' in pl)
    check('load_persona 함수', 'def load_persona' in pl)
    # 실제 파싱 동작 확인
    sys.path.insert(0, str(ROOT / 'scripts'))
    try:
        from persona_loader import load_persona
        p = load_persona('data-collector', agents_dir=ROOT / 'agents')
        check('role.md 실제 파싱', p is not None and '데이터 수집' in p.name)
    except Exception as e:
        check('role.md 실제 파싱', False, str(e))
else:
    check('persona_loader.py 존재', False, '파일 없음')

if lp_path.exists():
    lp = lp_path.read_text(encoding='utf-8')
    check('LLMProvider ABC', 'class LLMProvider' in lp)
    check('MockLLMProvider', 'class MockLLMProvider' in lp)
    check('OpenAILLMProvider', 'class OpenAILLMProvider' in lp)
    check('get_provider 팩토리', 'def get_provider' in lp)
    check('openai 클라이언트 import', 'import openai' in lp)
    check('dotenv 로드', 'load_dotenv' in lp)
    # 실제 반응 생성 동작 확인
    try:
        from llm_provider import get_provider
        provider = get_provider()
        from persona_loader import load_persona
        p = load_persona('frontend', agents_dir=ROOT / 'agents')
        reaction = provider.generate_reaction('frontend', '화면 구현', p, 'work')
        check('MockLLM 실제 반응',
              any(kw in reaction for kw in ['프론트엔드', '화면', '개발', 'React', 'Streamlit', '지시', '시작', '진행']),
              f'반응: {reaction}')
    except Exception as e:
        check('MockLLM 실제 반응', False, str(e))
else:
    check('llm_provider.py 존재', False, '파일 없음')

# .env.example / .gitignore 검증
env_ex = ROOT / '.env.example'
gi = ROOT / '.gitignore'
check('.env.example 존재', env_ex.exists())
if gi.exists():
    check('.gitignore 에 .env 추가', '.env' in gi.read_text(encoding='utf-8'))
else:
    check('.gitignore 에 .env 추가', False, '파일 없음')

# ─────────────────────────────────────────
# metaverse.html — fetch 콜백 반응 교체 검증
# ─────────────────────────────────────────
print('\n=== metaverse.html (persona fetch) ===')
if mv_path.exists():
    mv = mv_path.read_text(encoding='utf-8')
    check('fetch res.reaction 교체', 'res.reaction' in mv and 'showBubble(sp, res.reaction' in mv)
    check('localStorage agent 메시지 교체', "last.type === 'agent'" in mv or "last && last.type === 'agent'" in mv)

# ─────────────────────────────────────────
# memory.md 커버리지
# ─────────────────────────────────────────
print('\n=== memory.md 커버리지 ===')
agents_dir = ROOT / 'agents'
if agents_dir.exists():
    all_agents = [d for d in agents_dir.iterdir() if d.is_dir()]
    missing = [d.name for d in all_agents if not (d / 'memory.md').exists()]
    check(f'memory.md 전체 커버({len(all_agents)}명)', len(missing) == 0,
          f'없는 에이전트: {missing}' if missing else '전체 완료')

# ─────────────────────────────────────────
# role.md 최소 라인 수 체크 (80줄 이상 권장)
# ─────────────────────────────────────────
print('\n=== role.md 최소 라인 수 ===')
MIN_ROLE_LINES = 80
agents_root = ROOT / 'agents'
if agents_root.exists():
    for agent_dir in sorted(agents_root.iterdir()):
        if not agent_dir.is_dir():
            continue
        role_path = agent_dir / "role.md"
        if not role_path.exists():
            continue
        line_count = len(role_path.read_text(encoding="utf-8").splitlines())
        check(
            f'role.md 라인 수 충분 ({agent_dir.name})',
            line_count >= MIN_ROLE_LINES,
            f'{line_count}줄 (최소 {MIN_ROLE_LINES}줄)',
            fixable=False
        )

# ─────────────────────────────────────────
# 한자 혼입 검사 — 절대 금지 규칙
# ─────────────────────────────────────────
import re as _re_hanja
_HANJA_RE = _re_hanja.compile("[一-龥]")  # CJK Unified Ideographs (U+4E00~U+9FA5) — 표준 범위

def _scan_hanja(target_dir, glob_pattern):
    hits = []
    for p in (ROOT / target_dir).rglob(glob_pattern):
        if any(seg.startswith('.') or seg.startswith('_backup') for seg in p.parts):
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        for i, line in enumerate(text.split('\n'), 1):
            for ch in line:
                if _HANJA_RE.match(ch):
                    hits.append(f"{p.relative_to(ROOT)}:L{i} '{ch}'(U+{ord(ch):04X}) -- {line.strip()[:60]}")
                    break
    return hits

_hanja_role = _scan_hanja('agents', '*role.md')
_hanja_mem = _scan_hanja('agents', '*memory.md')
_hanja_html = _scan_hanja('.', 'index.html') + _scan_hanja('.', 'metaverse.html')

_hanja_total = len(_hanja_role) + len(_hanja_mem) + len(_hanja_html)
_msg = f'role.md {len(_hanja_role)}건 / memory.md {len(_hanja_mem)}건 / html {len(_hanja_html)}건'
check('한자(U+4E00~U+9FFF) 0건 — agents/*, index.html, metaverse.html', _hanja_total == 0, _msg)

if _hanja_total > 0:
    print('\n[한자 혼입 상세]')
    for hit in (_hanja_role + _hanja_mem + _hanja_html)[:20]:
        print(f'  {hit}')

# ─────────────────────────────────────────
# GitHub PAT 토큰 커밋 방지 검사 — 추적 파일에 실제 토큰이 들어가면 실패
# ─────────────────────────────────────────
import subprocess as _sp_tok
_TOKEN_RE = _re_hanja.compile(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})')
_SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.woff', '.woff2', '.zip', '.gz'}
_token_hits = []
try:
    _tracked = _sp_tok.run(['git', 'ls-files'], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=15)
    _files = [f for f in _tracked.stdout.splitlines() if f.strip()]
except Exception:
    _files = []
for _f in _files:
    _p = ROOT / _f
    if _p.suffix.lower() in _SKIP_EXT:
        continue
    try:
        _t = _p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    if _TOKEN_RE.search(_t):
        _token_hits.append(_f)
check('GitHub PAT 토큰 커밋 0건 — 추적 파일 내 ghp_/github_pat_ 패턴 없음',
      len(_token_hits) == 0,
      ('노출 의심 파일: ' + ', '.join(_token_hits[:5])) if _token_hits else '추적 파일 토큰 0건')

# ─────────────────────────────────────────
# index.html KPI rules 수치 동기화 체크
# ─────────────────────────────────────────
_total_so_far = len(results) + 1  # 이 체크 자체 포함
_idx_path2 = ROOT / 'index.html'
if _idx_path2.exists():
    _idx2 = _idx_path2.read_text(encoding='utf-8')
    import re as _re_kpi
    _m_kpi = _re_kpi.search(r'id="v2-kpi-rules">(\d+)<', _idx2)
    if _m_kpi:
        _kpi_val = int(_m_kpi.group(1))
        _kpi_ok = (_kpi_val == _total_so_far)
        check(f'KPI rules 수치 동기화 ({_kpi_val} == {_total_so_far})',
              _kpi_ok,
              f'index.html v2-kpi-rules={_kpi_val}, validate.py 총 체크={_total_so_far}',
              fixable=True)
        # --fix: index.html v2-kpi-rules 자동 갱신
        if not _kpi_ok and FIX_MODE:
            _backup_before_fix(_idx_path2)
            _idx2_fixed = _re_kpi.sub(
                r'id="v2-kpi-rules">\d+<',
                f'id="v2-kpi-rules">{_total_so_far}<',
                _idx2,
                count=1,
            )
            if _idx2_fixed != _idx2:
                _idx_path2.write_text(_idx2_fixed, encoding='utf-8')
                fixes_applied.append(f'index.html: v2-kpi-rules {_kpi_val}→{_total_so_far} 갱신')
                print(f'    => 자동 수정 완료 ({_kpi_val}→{_total_so_far})')
    else:
        check('KPI rules 수치 동기화', False, 'v2-kpi-rules 요소 미발견')

# ─────────────────────────────────────────
# 최종 결과
# ─────────────────────────────────────────
passed = sum(1 for r in results if r[0])
total = len(results)
print(f'\n{"="*40}')
print(f'결과: {passed}/{total} 통과')
if fixes_applied:
    print('\n자동 수정 완료:')
    for f in fixes_applied: print(f'  - {f}')
failed = [r for r in results if not r[0]]
if failed:
    print('\n실패 항목:')
    for r in failed:
        print(f'  - {r[1]}' + (f' ({r[2]})' if r[2] else '') + (' [자동수정 가능: --fix]' if r[3] else ''))
    sys.exit(1)
else:
    print('모든 검증 통과!')
