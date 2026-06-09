"""
resolve_paths.py — config.local.json 기반 경로 플레이스홀더 해석기

사용법:
    from scripts.resolve_paths import resolve, get_path

    path = resolve("{ESTATE_ROOT}/data/raw/2026-06")
    # → AGENTS_HOME/estate/data/raw/2026-06  (이 PC 기준)

    estate = get_path("ESTATE_ROOT")
    # → AGENTS_HOME/estate
"""

import json
from pathlib import Path

_REPO_ROOT   = Path(__file__).parent.parent
_CONFIG_PATH = _REPO_ROOT / "config.local.json"
_EXAMPLE_PATH = _REPO_ROOT / "config.local.json.example"

def _load_config() -> dict:
    """config.local.json 로드. 없으면 example에서 기본값 읽기."""
    for p in (_CONFIG_PATH, _EXAMPLE_PATH):
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                return {k: v for k, v in data.items() if not k.startswith("_")}
            except Exception:
                pass
    return {}

_CONFIG: dict = _load_config()


def get_path(alias: str) -> str:
    """별칭으로 실제 경로 반환. 없으면 빈 문자열."""
    return _CONFIG.get(alias, "")


def resolve(text: str) -> str:
    """{ALIAS} 플레이스홀더를 실제 경로로 치환."""
    for alias, value in _CONFIG.items():
        if value is None:
            continue
        text = text.replace(f"{{{alias}}}", value)
    return text


def print_paths():
    """현재 PC의 경로 설정 출력 (디버그용)."""
    src = "config.local.json" if _CONFIG_PATH.exists() else "config.local.json.example (기본값)"
    print(f"[resolve_paths] 경로 출처: {src}")
    for k, v in _CONFIG.items():
        print(f"  {{{k}}} → {v}")


if __name__ == "__main__":
    print_paths()
