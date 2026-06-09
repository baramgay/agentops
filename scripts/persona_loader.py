"""
Persona loader — agents/{agent_id}/role.md 파서

각 에이전트의 role.md에서 페르소나 정보(정체성, 역량, 원칙)를 추출한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PersonaContext:
    """에이전트 페르소나 컨텍스트"""

    agent_id: str
    name: str  # e.g. "오케스트레이터 (Orchestrator) — 총괄 에이전트"
    identity: str  # "## 정체성" 내용
    expertise: list[str]  # "## 정체성/## 원칙" 외 모든 ## 섹션
    principles: list[str]  # "## 원칙" 불릿 목록


def _split_sections(text: str) -> dict[str, str]:
    """## 헤딩을 기준으로 섹션 분리"""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def load_persona(
    agent_id: str,
    agents_dir: Path | str | None = None,
) -> PersonaContext | None:
    """agents/{agent_id}/role.md 를 파싱하여 PersonaContext 반환.

    role.md 가 없으면 None 을 반환한다.
    """
    if agents_dir is None:
        agents_dir = Path(__file__).parent.parent / "agents"
    else:
        agents_dir = Path(agents_dir)

    role_path = agents_dir / agent_id / "role.md"
    if not role_path.exists():
        return None

    text = role_path.read_text(encoding="utf-8-sig")

    # 첫 번째 H1 → name
    name = agent_id
    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            name = line[2:].strip()
            break

    sections = _split_sections(text)

    identity = sections.get("정체성", "")

    # "## 원칙" → 불릿 목록
    principles_text = sections.get("원칙", "")
    principles = [
        line.strip("- *• ").strip()
        for line in principles_text.splitlines()
        if line.strip() and line.strip()[0] in ("-", "*", "•")
    ]

    # 나머지 ## 섹션 → expertise
    expertise: list[str] = []
    for heading, content in sections.items():
        if heading in ("정체성", "원칙"):
            continue
        body = content.strip()
        if body:
            expertise.append(f"## {heading}\n{body}")

    return PersonaContext(
        agent_id=agent_id,
        name=name,
        identity=identity,
        expertise=expertise,
        principles=principles,
    )


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    for aid in ("orchestrator", "data-collector", "frontend", "security"):
        p = load_persona(aid)
        if p:
            print(f"\n--- {aid} ---")
            print(f"name: {p.name}")
            print(f"identity: {p.identity[:60]}...")
            print(f"expertise sections: {len(p.expertise)}")
            print(f"principles: {p.principles[:3]}")
        else:
            print(f"\n--- {aid} --- NOT FOUND")
