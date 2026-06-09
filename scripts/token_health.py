"""
토큰 효율 건강 검진 — Claude Code SessionStart 훅용. 토큰 0(LLM 미호출).

매 세션 시작 시 stdout으로 주입 → Claude가 상태를 보고 문제 있으면 즉시 개선.

측정 항목:
  1. Wiki 성장 — 최근 7일 신규·수정 노트 수
  2. distill_nudge 발동 이력 — .distill_marker 기반
  3. PreCompact 효율 — 압축 직후 wiki 노트 생성 여부 (세션 파일 타임스탬프 비교)
  4. 스테일 에이전트 — 2h+ working 상태
  5. MoC 커버리지 — notes/ 노트 중 MoC 미등록 비율
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
WIKI = REPO / "wiki"
NOTES = WIKI / "notes"
MOC_DIR = WIKI / "MoC"
STATUS_FILE = REPO / "agent_status.json"
MARKER = REPO / "logs" / ".distill_marker"
STALE_MINUTES = 120


def _age_days(p: Path) -> float:
    try:
        return (datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)).total_seconds() / 86400
    except Exception:
        return 999


def check_wiki_growth() -> dict:
    """최근 7일 신규·수정 노트 수"""
    try:
        notes = [p for p in NOTES.rglob("*.md") if not p.name.startswith("세션-")]
        recent = [p for p in notes if _age_days(p) <= 7]
        return {"total": len(notes), "recent_7d": len(recent), "ok": len(recent) > 0}
    except Exception:
        return {"total": 0, "recent_7d": 0, "ok": False}


def check_distill_nudge() -> dict:
    """distill_nudge .distill_marker 최근 갱신 여부"""
    try:
        if not MARKER.exists():
            return {"fired_ever": False, "last_days_ago": None, "ok": False}
        age = _age_days(MARKER)
        return {"fired_ever": True, "last_days_ago": round(age, 1), "ok": age <= 7}
    except Exception:
        return {"fired_ever": False, "last_days_ago": None, "ok": False}


def check_precompact_effectiveness() -> dict:
    """
    .compact_pending 플래그 파일로 compact 발생 여부 감지.
    precompact_wiki_guide.py 가 compact 직전 플래그를 생성 → 이 함수가 감지 후 삭제.
    플래그 없으면 정상(compact 미발생 또는 이미 처리됨).
    """
    flag = Path(__file__).resolve().parent.parent / ".compact_pending"
    try:
        if flag.exists():
            import json as _json
            info = _json.loads(flag.read_text(encoding="utf-8"))
            ts = info.get("ts", "?")
            reason = info.get("reason", "?")
            flag.unlink(missing_ok=True)  # 한 번 표시 후 삭제
            return {
                "verdict": f"compact 발생({ts}, reason={reason}) — wiki 저장이 안 됐을 수 있음",
                "ok": False,
            }
        return {"verdict": "이전 compact 후 wiki 저장 확인됨", "ok": True}
    except Exception as e:
        return {"verdict": f"확인 불가: {e}", "ok": None}


def check_stale_agents() -> dict:
    """2h+ working 상태 에이전트"""
    try:
        data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        now = datetime.now()
        stale = []
        for aid, info in data.get("agents", {}).items():
            if info.get("status") != "working":
                continue
            try:
                ts_str = info.get("updated", "").replace("+09:00", "").replace("Z", "").strip()
                ts = datetime.fromisoformat(ts_str)
                if (now - ts).total_seconds() / 60 > STALE_MINUTES:
                    stale.append(aid)
            except Exception:
                pass
        return {"stale_count": len(stale), "stale_ids": stale, "ok": len(stale) == 0}
    except Exception:
        return {"stale_count": 0, "stale_ids": [], "ok": True}


def check_moc_coverage() -> dict:
    """notes/ 노트 중 MoC에 미등록 비율"""
    try:
        # agent role/memory 파일은 MoC 등록 대상이 아님 (에이전트 정의 파일)
        notes = {p.stem for p in NOTES.rglob("*.md")
                 if not p.name.startswith("세션-")
                 and not p.stem.startswith("agent-")}
        if not notes:
            return {"uncovered": 0, "total": 0, "ok": True}

        moc_texts = ""
        for moc in MOC_DIR.glob("*.md"):
            moc_texts += moc.read_text(encoding="utf-8", errors="ignore")

        uncovered = [n for n in notes if f"[[{n}]]" not in moc_texts]
        ratio = len(uncovered) / len(notes)
        return {
            "total": len(notes),
            "uncovered": len(uncovered),
            "ratio_pct": round(ratio * 100),
            "examples": uncovered[:3],
            "ok": ratio <= 0.2,  # 20% 이하면 양호
        }
    except Exception:
        return {"uncovered": 0, "total": 0, "ok": True}


def build_report() -> str:
    wiki = check_wiki_growth()
    nudge = check_distill_nudge()
    compact = check_precompact_effectiveness()
    stale = check_stale_agents()
    moc = check_moc_coverage()

    def icon(ok):
        if ok is True: return "✅"
        if ok is False: return "⚠️"
        return "ℹ️"

    lines = ["## 🔍 토큰 효율 건강 검진"]

    # 1. Wiki 성장
    lines.append(
        f"{icon(wiki['ok'])} **Wiki 성장** — 전체 {wiki['total']}개 노트, "
        f"최근 7일 {wiki['recent_7d']}개 추가/수정"
        + ("" if wiki['ok'] else " → wiki 활용이 저조합니다. 이번 세션 결과를 저장하세요.")
    )

    # 2. distill_nudge
    if nudge["fired_ever"]:
        lines.append(
            f"{icon(nudge['ok'])} **distill_nudge** — 마지막 발동 {nudge['last_days_ago']}일 전"
            + ("" if nudge['ok'] else " → 7일 이상 미발동. 세션이 짧거나 2MB 미도달.")
        )
    else:
        lines.append("ℹ️ **distill_nudge** — 아직 한 번도 발동 안 됨 (세션 길이 미도달)")

    # 3. PreCompact 효율
    lines.append(
        f"{icon(compact['ok'])} **PreCompact 효율** — {compact['verdict']}"
        + ("" if compact.get('ok') else " → 압축 후 wiki 저장이 안 됐을 수 있습니다.")
    )

    # 4. 스테일 에이전트
    if stale["ok"]:
        lines.append("✅ **스테일 에이전트** — 없음")
    else:
        ids = ", ".join(stale["stale_ids"])
        lines.append(f"⚠️ **스테일 에이전트** — {stale['stale_count']}개 방치 중: {ids} → done 선언 필요")

    # 5. MoC 커버리지
    if moc["ok"]:
        lines.append(f"✅ **MoC 커버리지** — {moc['total']}개 중 미등록 {moc['uncovered']}개 ({moc['ratio_pct']}%)")
    else:
        ex = ", ".join(moc.get("examples", []))
        lines.append(
            f"⚠️ **MoC 커버리지** — 미등록 {moc['uncovered']}/{moc['total']}개 ({moc['ratio_pct']}%)"
            f" 예: {ex} → 해당 MoC에 [[링크]] 등록 필요"
        )

    # 종합 판정
    all_ok = all([wiki["ok"], stale["ok"], moc["ok"]])
    if all_ok:
        lines.append("\n> 전반적으로 양호합니다.")
    else:
        lines.append("\n> 위 ⚠️ 항목을 이번 세션에서 개선하세요.")

    return "\n".join(lines)


def main():
    try:
        print(build_report())
    except Exception as e:
        # 훅 실패가 세션 흐름을 막아선 안 됨
        pass


if __name__ == "__main__":
    main()
