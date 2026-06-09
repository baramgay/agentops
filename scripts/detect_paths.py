"""
경로 자동 감지 유틸리티
다중 PC 환경에서 config.local.json이 없어도 작동하도록 설계됨
"""

import json
import os
from pathlib import Path


def get_workspace_root() -> Path:
    """이 스크립트 위치 기준으로 에이전트 루트 자동 감지"""
    return Path(__file__).parent.parent.resolve()


def load_config() -> dict:
    """
    설정 로드 우선순위:
    1. config.local.json (머신별 설정, gitignore)
    2. 환경변수 AGENT_WORKSPACE_ROOT
    3. 스크립트 위치 기반 자동 감지 (기본값)
    """
    workspace_root = get_workspace_root()
    local_config_path = workspace_root / "config.local.json"

    if local_config_path.exists():
        try:
            with open(local_config_path, encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[detect_paths] config.local.json 파싱 오류 — 기본값 사용: {e}", file=sys.stderr)
            config = {}
        config["workspace_root"] = str(workspace_root)
        return _resolve_placeholders(config)

    env_root = os.environ.get("AGENT_WORKSPACE_ROOT")
    if env_root:
        workspace_root = Path(env_root).resolve()

    return _build_default_config(workspace_root)


def _build_default_config(workspace_root: Path) -> dict:
    data_root = workspace_root / "data"
    output_root = workspace_root / "output"
    return {
        "machine_id": "auto-detected",
        "workspace_root": str(workspace_root),
        "data_root": str(data_root),
        "output_root": str(output_root),
        "python_path": "python",
        "r_path": "Rscript",
        "paths": {
            "raw_data": str(data_root / "raw"),
            "processed_data": str(data_root / "processed"),
            "analysis_output": str(output_root / "analysis"),
            "webapp_output": str(output_root / "webapp"),
            "pptx_output": str(output_root / "pptx"),
            "reports": str(output_root / "reports"),
        },
    }


def _resolve_placeholders(config: dict) -> dict:
    """{data_root}, {output_root} 같은 플레이스홀더를 실제 경로로 치환"""
    replacements = {
        "{workspace_root}": config.get("workspace_root", ""),
        "{data_root}": config.get("data_root", ""),
        "{output_root}": config.get("output_root", ""),
    }
    if "paths" in config:
        for key, val in config["paths"].items():
            for placeholder, actual in replacements.items():
                val = val.replace(placeholder, actual)
            config["paths"][key] = val
    return config


def ensure_directories(config: dict) -> None:
    """필요한 디렉토리가 없으면 자동 생성"""
    for path_str in config.get("paths", {}).values():
        Path(path_str).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    config = load_config()
    print(f"머신 ID: {config['machine_id']}")
    print(f"워크스페이스: {config['workspace_root']}")
    print("\n경로 설정:")
    for key, val in config["paths"].items():
        print(f"  {key}: {val}")
