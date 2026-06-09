# -*- coding: utf-8 -*-
"""
rotate_worklog.py — work_log.jsonl 월별 로테이션

사용법:
  python scripts/rotate_worklog.py           # 이전 달 로그를 아카이브
  python scripts/rotate_worklog.py --force   # 현재 달 포함 강제 로테이션
  python scripts/rotate_worklog.py --dry-run # 실제 이동 없이 결과 미리 보기

동작:
  1. work_log.jsonl 에서 이전 달(또는 --force 시 현재 달까지) 로그 분리
  2. work_log_{YYYY-MM}.jsonl 로 아카이브 (logs/ 폴더)
  3. 현재 달 로그만 work_log.jsonl 에 유지
"""
import json
import sys
import argparse
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
WORK_LOG = ROOT / "work_log.jsonl"
LOGS_DIR = ROOT / "logs"


def main():
    parser = argparse.ArgumentParser(description="work_log.jsonl 월별 로테이션")
    parser.add_argument("--force", action="store_true", help="현재 달 포함 강제 로테이션")
    parser.add_argument("--dry-run", action="store_true", help="실제 이동 없이 결과 미리 보기")
    args = parser.parse_args()

    if not WORK_LOG.exists():
        print(f"[rotate] {WORK_LOG} 없음 — 건너뜀")
        return

    today = date.today()
    current_ym = today.strftime("%Y-%m")

    lines = WORK_LOG.read_text(encoding="utf-8").splitlines()
    by_month = defaultdict(list)

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            # ts, timestamp, time, date 순으로 타임스탬프 키 탐색
            ts = (
                entry.get("ts")
                or entry.get("timestamp")
                or entry.get("time")
                or entry.get("date")
                or ""
            )
            ym = ts[:7] if len(ts) >= 7 else "unknown"
        except Exception:
            ym = "unknown"
        by_month[ym].append(line)

    keep_months = {current_ym} if not args.force else set()
    archive_months = {ym for ym in by_month if ym not in keep_months and ym != "unknown"}

    if not archive_months:
        print("[rotate] 아카이브할 이전 달 로그 없음")
        return

    for ym in sorted(archive_months):
        archive_path = LOGS_DIR / f"work_log_{ym}.jsonl"
        new_lines = by_month[ym]
        print(f"[rotate] {ym}: {len(new_lines)}줄 → {archive_path.relative_to(ROOT)}")
        if not args.dry_run:
            LOGS_DIR.mkdir(exist_ok=True)
            # 순서 보존 중복 제거: 기존 줄 리스트 유지, set은 O(1) 조회용으로만 사용
            existing_lines: list[str] = []
            existing_set: set[str] = set()
            if archive_path.exists():
                for ln in archive_path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if ln.strip() and ln not in existing_set:
                        existing_lines.append(ln)
                        existing_set.add(ln)
            to_add = [ln for ln in new_lines if ln not in existing_set]
            if to_add:
                # atomic append: 임시 파일에 쓴 뒤 기존 파일에 병합
                tmp = archive_path.with_suffix(".tmp")
                try:
                    combined = existing_lines + to_add
                    tmp.write_text("\n".join(combined) + "\n", encoding="utf-8")
                    tmp.replace(archive_path)
                except Exception:
                    tmp.unlink(missing_ok=True)
                    raise
            print(f"[rotate]   추가: {len(to_add)}줄 (중복 {len(new_lines)-len(to_add)}줄 건너뜀)")

    keep_lines = []
    for ym in keep_months | {"unknown"}:
        keep_lines.extend(by_month.get(ym, []))

    print(f"[rotate] 유지: {len(keep_lines)}줄 (현재 달 + unknown)")
    if not args.dry_run:
        # atomic write: 임시 파일에 먼저 쓰고 rename
        tmp = WORK_LOG.with_suffix(".tmp")
        try:
            tmp.write_text("\n".join(keep_lines) + ("\n" if keep_lines else ""), encoding="utf-8")
            tmp.replace(WORK_LOG)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
        print("[rotate] work_log.jsonl 갱신 완료")
    else:
        print("[rotate] --dry-run 모드: 파일 변경 없음")


if __name__ == "__main__":
    main()
