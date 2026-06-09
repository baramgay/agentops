"""
LLM 위키 부트스트랩 — Claude 메모리(.claude/projects/.../memory) → 옵시디언 Vault 씨앗.

동작:
  1. memory/*.md(인덱스 MEMORY.md 제외)를 notes/<slug>.md 로 복사.
     - slug = 각 노트 frontmatter의 name: (없으면 파일명 하이픈화).
     - 이렇게 하면 노트 본문의 [[slug]] 위키링크가 옵시디언에서 그대로 resolve.
  2. MEMORY.md에서 노트별 설명을 파싱.
  3. 파일명 키워드로 도메인 분류 → MoC/<도메인>.md (지도 노트) 자동 생성.

멱등 갱신(2026-06-07): 더 이상 notes/·MoC/를 통째로 지우지 않는다.
      메모리에서 생성한 파일만 매니페스트(.bootstrap_manifest.json)로 추적해
      덮어쓰고, 사라진 메모리의 노트만 정리한다. → 에이전트 노트(agent-*-role/memory.md),
      사람이 만든 MoC(에이전트 등)는 보존되어 안전하게 재실행 가능.
"""
import json
import re
from pathlib import Path

MEM = Path(r"C:\Users\username\.claude\projects\C--Users-username\memory")
VAULT = Path(__file__).resolve().parent.parent
NOTES = VAULT / "notes"
MOC = VAULT / "MoC"
MANIFEST = VAULT / "_tools" / ".bootstrap_manifest.json"
NOTES.mkdir(parents=True, exist_ok=True)
MOC.mkdir(parents=True, exist_ok=True)

# 직전 실행이 생성한 파일 목록(이것만 정리 대상 — 외부 노트는 절대 건드리지 않음)
_prev = (json.loads(MANIFEST.read_text(encoding="utf-8"))
         if MANIFEST.exists() else {"notes": [], "moc": []})


def _sanitize(s: str) -> str:
    s = s.strip().strip('"').strip("'").strip()
    s = re.sub(r'[<>:"/\\|?*]', '', s)   # Windows 파일명 금지문자 제거
    return s.strip()


def get_slug(filename_stem: str) -> str:
    # 슬러그 = 파일명 기준 하이픈화 (프론트매터 name이 한글이어도 링크 일관성 유지)
    return _sanitize(filename_stem.replace('_', '-'))


def normalize_links(body: str) -> str:
    # 본문 위키링크 타깃의 밑줄 → 하이픈 (파일명 슬러그와 일치시켜 resolve)
    def repl(m):
        return '[[' + m.group(1).replace('_', '-')
    return re.sub(r'\[\[([^\]|#`]+)', repl, body)


# 파일명 키워드 → 도메인 (위에서부터 매칭)
RULES = [
    ('estate', '경남부동산'),
    ('eum_jido', '이음지도'), ('eumjido', '이음지도'),
    ('synthetic', '합성데이터스튜디오'), ('nuristat', '합성데이터스튜디오'),
    ('gis_resources', '공공데이터소스'), ('opendataloader', '공공데이터소스'),
    ('agents_always', 'agents시스템'), ('agents_improvements', 'agents시스템'),
    ('cc_changes', 'agents시스템'), ('html_build', 'agents시스템'),
    ('cp949', 'agents시스템'), ('sync_after', 'agents시스템'),
    ('ci_dependency', 'agents시스템'),
    ('no_hanja', '작업원칙'), ('no_competition', '작업원칙'),
    ('no_security', '작업원칙'), ('optimization', '작업원칙'),
    ('absolute_numbers', '작업원칙'),
    ('user_profile', '사용자'),
]


def domain_of(fname: str) -> str:
    for key, dom in RULES:
        if key in fname:
            return dom
    return '기타'


# MEMORY.md: "- [제목](파일.md) — 설명" 파싱
descs = {}
idx = (MEM / 'MEMORY.md').read_text(encoding='utf-8')
for m in re.finditer(r'-\s*\[(.+?)\]\((.+?\.md)\)\s*[—-]+\s*(.+)', idx):
    descs[m.group(2)] = (m.group(1).strip(), m.group(3).strip())

buckets = {}
for f in sorted(MEM.glob('*.md')):
    if f.name == 'MEMORY.md':
        continue
    text = normalize_links(f.read_text(encoding='utf-8'))
    slug = get_slug(f.stem)
    (NOTES / f'{slug}.md').write_text(text, encoding='utf-8')
    title, desc = descs.get(f.name, (slug, ''))
    buckets.setdefault(domain_of(f.name), []).append((slug, desc))

cur_notes = sorted({get_slug(f.stem) for f in MEM.glob('*.md') if f.name != 'MEMORY.md'})
cur_moc = sorted(buckets.keys())

for dom, items in sorted(buckets.items()):
    lines = ['---', 'type: moc', f'domain: {dom}', 'tags: [moc]', '---', '',
             f'# {dom} — 지도(MoC)', '',
             '> 이 도메인 지식 노트의 허브. 새 노트는 아래에 `[[링크]]`로 등록한다.', '']
    for slug, desc in sorted(items):
        lines.append(f'- [[{slug}]]' + (f' — {desc}' if desc else ''))
    (MOC / f'{dom}.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

# 사라진 메모리의 자기 생성물만 정리 (외부 노트는 매니페스트에 없으므로 안전)
removed = 0
for slug in set(_prev.get('notes', [])) - set(cur_notes):
    p = NOTES / f'{slug}.md'
    if p.exists():
        p.unlink(); removed += 1
for dom in set(_prev.get('moc', [])) - set(cur_moc):
    p = MOC / f'{dom}.md'
    if p.exists():
        p.unlink(); removed += 1

MANIFEST.write_text(json.dumps({'notes': cur_notes, 'moc': cur_moc},
                               ensure_ascii=False, indent=2), encoding='utf-8')

print('도메인별 노트 수:', {k: len(v) for k, v in sorted(buckets.items())})
print(f'동기화 노트: {len(cur_notes)} | MoC: {len(cur_moc)} | 정리된 stale: {removed}')
