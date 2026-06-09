"""
스프라이트 시트를 개별 에이전트 아바타로 슬라이싱합니다.
사용법: python assets/slice_sprite.py
"""
from PIL import Image
from pathlib import Path

SPRITE_PATH = Path(r"C:\Users\username\Downloads\ChatGPT Image 2026년 5월 20일 오전 08_47_47.png")
OUTPUT_DIR  = Path(__file__).parent / "avatars"
CELL_SIZE   = 229   # 실측 셀 크기 (1374/6 = 229, 1145/5 = 229)
COLS        = 6
OUTPUT_SIZE = 64    # 최종 출력 크기 (px) — 32px 표시 기준 2x 레티나

# 에이전트 ID 목록 (스프라이트 시트 순서와 정확히 일치)
AGENTS = [
    # Row 1
    "orchestrator", "lead-data", "lead-dev", "lead-pptx",
    "data-collector", "data-cleaner",
    # Row 2
    "eda-analyst", "statistician", "ml-engineer", "deep-learning",
    "gis-specialist", "text-analyst",
    # Row 3
    "visualizer", "reporter", "requirements", "ux-designer",
    "frontend", "backend",
    # Row 4
    "dba", "security", "tester-unit", "tester-qa",
    "devops", "tech-writer",
    # Row 5
    "statworkbench", "pptx-planner", "pptx-content", "pptx-designer",
    "pptx-builder", "pptx-reviewer",
]

def slice_sprite():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.open(SPRITE_PATH).convert("RGBA")

    print(f"스프라이트 시트 크기: {img.size}")
    print(f"셀 크기: {CELL_SIZE}px, 총 {len(AGENTS)}개 슬라이싱 시작\n")

    for idx, agent_id in enumerate(AGENTS):
        col = idx % COLS
        row = idx // COLS
        x = col * CELL_SIZE
        y = row * CELL_SIZE
        cell = img.crop((x, y, x + CELL_SIZE, y + CELL_SIZE))
        cell = cell.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
        out_path = OUTPUT_DIR / f"{agent_id}.png"
        cell.save(out_path, "PNG", optimize=True)
        print(f"  [{idx+1:02d}] {agent_id}.png → {out_path}")

    print(f"\n슬라이싱 완료: {len(AGENTS)}개 아이콘 → {OUTPUT_DIR}")

if __name__ == "__main__":
    slice_sprite()
