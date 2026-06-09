"""
MoC 자동 등록 — Claude Code PostToolUse(Write) 훅용.

wiki/notes/<type>/<슬러그>.md 파일이 저장될 때:
1. frontmatter에서 name, domain, type 읽기
2. wiki/MoC/<domain>.md에 [[슬러그]] 링크가 없으면 자동 추가
3. 이미 있으면 skip (멱등)
"""
import sys
import json
import re
from pathlib import Path

WIKI = Path(__file__).resolve().parent.parent / "wiki"
MOC_DIR = WIKI / "MoC"
NOTES_DIR = WIKI / "notes"

# domain 값 → MoC 파일명 매핑 (frontmatter domain과 MoC 파일명이 다를 때)
DOMAIN_MAP = {
    "agents시스템": "agents시스템",
    "이음지도": "이음지도",
    "경남부동산": "경남부동산",
    "합성데이터스튜디오": "합성데이터스튜디오",
    "누리스탯": "누리스탯",
    "공공데이터소스": "공공데이터소스",
    "작업원칙": "작업원칙",
    "devops": "작업원칙",
    "nuristat": "누리스탯",
}


def parse_frontmatter(text: str) -> dict:
    """--- ... --- 블록에서 key: value 파싱. metadata.domain 중첩 지원."""
    result = {}
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return result
    in_metadata = False
    for line in m.group(1).splitlines():
        stripped = line.strip()
        if stripped == "metadata:":
            in_metadata = True
            continue
        if in_metadata and line.startswith("  "):
            # metadata 하위 필드 (들여쓰기 2칸)
            if ':' in stripped:
                key, _, val = stripped.partition(':')
                result[key.strip()] = val.strip()
            continue
        else:
            in_metadata = False
        if ':' in stripped:
            key, _, val = stripped.partition(':')
            result[key.strip()] = val.strip()
    return result


def is_wiki_note(file_path: str) -> bool:
    """wiki/notes/<type>/<file>.md 패턴인지 확인."""
    fp = file_path.replace("\\", "/")
    # notes/ 뒤에 <type>/<file>.md 형태 (슬래시 2개)
    idx = fp.find("wiki/notes/")
    if idx == -1:
        return False
    remainder = fp[idx + len("wiki/notes/"):]
    return remainder.count("/") == 1 and remainder.endswith(".md")


def extract_description(text: str) -> str:
    """본문에서 설명 추출: '결론:' 줄 또는 첫 비공백 비frontmatter 줄."""
    in_fm = False
    fm_done = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            if not fm_done:
                in_fm = not in_fm
                if not in_fm:
                    fm_done = True
            continue
        if in_fm or not fm_done:
            continue
        if not stripped or stripped.startswith("#"):
            continue
        # '결론:' 패턴
        if stripped.startswith("결론:"):
            desc = stripped[len("결론:"):].strip()
            return desc[:60] + ("…" if len(desc) > 60 else "")
        # 첫 내용 줄 (** 제거)
        clean = stripped.lstrip("*- ").rstrip("*")
        if clean:
            return clean[:60] + ("…" if len(clean) > 60 else "")
    return ""


def build_link_line(slug: str, meta: dict, body_text: str = "") -> str:
    """MoC에 추가할 링크 라인 생성. 본문에서 설명 자동 추출."""
    desc = extract_description(body_text) if body_text else ""
    return f"- [[{slug}]]" + (f" — {desc}" if desc else "")


def register_to_moc(note_path: str) -> str:
    """wiki/notes 노트를 해당 domain MoC에 등록. 결과 메시지 반환."""
    note = Path(note_path)
    if not note.exists():
        return f"skip: 파일 없음 ({note_path})"

    try:
        text = note.read_text(encoding="utf-8")
    except Exception as e:
        return f"skip: 읽기 실패 ({e})"

    meta = parse_frontmatter(text)
    slug = meta.get("name") or note.stem
    domain = meta.get("domain", "")

    if not domain:
        return f"skip: domain 없음 ({slug})"

    moc_name = DOMAIN_MAP.get(domain, domain)
    moc_file = MOC_DIR / f"{moc_name}.md"
    if not moc_file.exists():
        return f"skip: MoC 없음 ({moc_file.name})"

    moc_text = moc_file.read_text(encoding="utf-8")

    # 이미 등록됐으면 skip (링크 형태 유연 검사)
    if f"[[{slug}]]" in moc_text:
        return f"skip: 이미 등록됨 ({slug} → {moc_name})"

    # 마지막 줄에 추가 (빈 줄 후)
    link_line = build_link_line(slug, meta, text)
    if not moc_text.endswith("\n"):
        moc_text += "\n"
    moc_text += link_line + "\n"
    moc_file.write_text(moc_text, encoding="utf-8")
    return f"등록됨: [[{slug}]] → {moc_name}.md"


def main():
    try:
        data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except Exception:
        sys.exit(0)

    # PostToolUse Write 훅 입력 확인
    tool = data.get("tool_name", "")
    if tool != "Write":
        sys.exit(0)

    output = data.get("tool_response", {})
    # tool_input에서 file_path 추출
    file_path = str(data.get("tool_input", {}).get("file_path", ""))
    if not file_path:
        sys.exit(0)

    if not is_wiki_note(file_path):
        sys.exit(0)

    result = register_to_moc(file_path)
    # stdout으로 결과 출력 (Claude Code가 PostToolUse 결과로 확인 가능)
    print(f"[MoC 자동등록] {result}", flush=True)


if __name__ == "__main__":
    # CLI 직접 실행: python moc_auto_register.py <note_path>
    if len(sys.argv) > 1:
        for p in sys.argv[1:]:
            print(register_to_moc(p))
    else:
        main()
