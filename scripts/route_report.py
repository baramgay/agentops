# -*- coding: utf-8 -*-
"""
route_report.py — 보고서 요청 키워드 기반 라우팅 결정 도구

사용법:
  python scripts/route_report.py "[보고서 요청 문장]"

예시:
  python scripts/route_report.py "5월 부동산 월보 작성해줘"
  → [라우팅] realty-analyst (부동산 동향 월보, skills/realty-pipeline)

  python scripts/route_report.py "청년 정착 잠재지역 발굴 분석 보고서"
  → [라우팅] reporter (빅데이터 분석 보고서, 7블록 양식)

  python scripts/route_report.py "분석 보고서 만들어줘"
  → [모호] 사용자 명확화 필요 — 빅데이터 분석 보고서 vs 부동산 동향 월보 어느 양식?

옵션:
  --execute   라우팅 결정 후 해당 에이전트 working 상태로 update_status.py 자동 호출
"""
import sys
import subprocess
import re
from pathlib import Path

UPDATE_STATUS = Path(__file__).parent / "update_status.py"

REALTY_KEYWORDS = [
    "부동산", "매매", "전세", "월보", "시장 동향", "미분양", "거래량",
    "R-ONE", "한국부동산원", "공시가격", "경매", "낙찰가율", "분양",
    "인허가", "착공", "준공",
]

REPORTER_KEYWORDS = [
    "빅데이터 분석 보고서", "자체발굴", "수요대응", "정기분석",
    "발굴 분석", "진단 분석", "잠재지역", "취약지", "활력 진단",
]

AMBIGUOUS_KEYWORDS = ["분석 보고서", "보고서"]


def route(query: str) -> dict:
    q = query.lower()
    realty_hits = [kw for kw in REALTY_KEYWORDS if kw.lower() in q]
    reporter_hits = [kw for kw in REPORTER_KEYWORDS if kw.lower() in q]

    if realty_hits and not reporter_hits:
        return {"agent": "realty-analyst", "kind": "부동산 동향 월보",
                "skill": "skills/realty-pipeline", "workflow": "workflows/estate_monthly_report.md",
                "matched": realty_hits, "ambiguous": False}
    if reporter_hits and not realty_hits:
        return {"agent": "reporter", "kind": "빅데이터 분석 보고서 (7블록 양식)",
                "skill": None, "workflow": None,
                "matched": reporter_hits, "ambiguous": False}
    if realty_hits and reporter_hits:
        return {"agent": None, "kind": "충돌", "matched": realty_hits + reporter_hits,
                "ambiguous": True, "reason": f"realty 키워드({realty_hits})와 reporter 키워드({reporter_hits}) 동시 일치"}
    ambig = [kw for kw in AMBIGUOUS_KEYWORDS if kw.lower() in q]
    if ambig:
        return {"agent": None, "kind": "모호", "matched": ambig,
                "ambiguous": True, "reason": "구분 키워드 없이 일반 키워드만 일치"}
    return {"agent": None, "kind": "키워드 없음", "matched": [],
            "ambiguous": True, "reason": "라우팅 키워드 0건 검출"}


def main():
    if len(sys.argv) < 2:
        print("사용법: python scripts/route_report.py \"[보고서 요청 문장]\" [--execute]")
        sys.exit(1)

    query = sys.argv[1]
    execute = "--execute" in sys.argv

    # 한자 검사
    hanja = re.compile(r"[㐀-䶿一-鿿]")
    if any(hanja.match(ch) for ch in query):
        print("[오류] 요청 문장에 한자 포함 — 처리 거부 (한글로 작성하세요)")
        sys.exit(1)

    result = route(query)

    print(f"\n[입력] {query}")
    print(f"[키워드 매칭] {result['matched']}")

    if result["ambiguous"]:
        print(f"[모호] {result['kind']} — {result.get('reason','')}")
        print("[안내] 사용자 명확화 필요:")
        print("  - 빅데이터 분석 보고서 (reporter, 7블록 양식, '발굴 분석'·'진단 분석' 형식)")
        print("  - 부동산 동향 월보 (realty-analyst, 8섹션, 매월 정기 발간)")
        sys.exit(2)

    agent = result["agent"]
    print(f"[라우팅] {agent} — {result['kind']}")
    if result.get("skill"):
        print(f"[참조] 스킬: {result['skill']}")
    if result.get("workflow"):
        print(f"[참조] 워크플로우: {result['workflow']}")

    if execute:
        if not UPDATE_STATUS.exists():
            print(f"[route_report] 오류: update_status.py 없음 ({UPDATE_STATUS})", file=sys.stderr)
            sys.exit(1)
        cmd = [sys.executable, str(UPDATE_STATUS), agent, "working", f"라우팅 결과 — {query[:40]}"]
        print(f"\n[실행] {' '.join(cmd[1:])}")
        try:
            proc = subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[route_report] 상태 업데이트 실패 (종료코드 {e.returncode}): {e}", file=sys.stderr)
            sys.exit(1)
        except (OSError, FileNotFoundError) as e:
            print(f"[route_report] 서브프로세스 실행 실패: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
