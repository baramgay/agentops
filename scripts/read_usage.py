#!/usr/bin/env python3
"""Claude Code stats-cache.json을 읽어 data/usage.json으로 저장"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

# Claude Code stats 경로 (Windows/Mac 자동 감지)
_CANDIDATES = [
    Path.home() / '.claude' / 'stats-cache.json',
    Path(os.getenv('APPDATA', '')) / '..' / '.claude' / 'stats-cache.json',
]

def read_claude_stats():
    for p in _CANDIDATES:
        try:
            p = p.resolve()
            if p.exists():
                return json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
    return None

def compute_usage(stats: dict) -> dict:
    if not stats:
        return {"error": "stats-cache.json 없음", "demo": True}

    tokens_by_model = stats.get('dailyModelTokens', [])
    activity = stats.get('dailyActivity', [])

    # 모델별 총 토큰 집계
    totals = {}
    recent_30d = {}  # 최근 30일
    cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    for day in tokens_by_model:
        for model, cnt in day.get('tokensByModel', {}).items():
            totals[model] = totals.get(model, 0) + cnt
            if day.get('date', '') >= cutoff:
                recent_30d[model] = recent_30d.get(model, 0) + cnt

    grand_total = max(sum(totals.values()), 1)
    recent_total = max(sum(recent_30d.values()), 1)

    # 모델명 정규화
    MODEL_LABELS = {
        'claude-sonnet-4-6': 'Sonnet 4.6',
        'claude-opus-4-7': 'Opus 4.7',
        'claude-haiku-4-5-20251001': 'Haiku 4.5',
        'claude-haiku-4-5': 'Haiku 4.5',
    }
    # 비용 추정 (per MTok, 입출력 평균 기준)
    MODEL_COST_PER_MTOK = {
        'claude-sonnet-4-6': 9.0,          # $3 input + $15 output 평균
        'claude-opus-4-7': 45.0,           # $15 + $75 평균
        'claude-haiku-4-5-20251001': 0.75, # $0.25 + $1.25 평균
        'claude-haiku-4-5': 0.75,
    }

    model_stats = []
    total_cost = 0.0
    for model_id, cnt in sorted(totals.items(), key=lambda x: -x[1]):
        label = MODEL_LABELS.get(model_id, model_id)
        pct = round(cnt / grand_total * 100)
        cost = cnt / 1_000_000 * MODEL_COST_PER_MTOK.get(model_id, 5.0)
        total_cost += cost
        model_stats.append({
            "id": model_id,
            "label": label,
            "tokens": cnt,
            "pct": pct,
            "cost_usd": round(cost, 2),
        })

    # 오늘 활동
    today = datetime.now().strftime('%Y-%m-%d')
    today_tokens = sum(
        sum(d.get('tokensByModel', {}).values())
        for d in tokens_by_model if d.get('date') == today
    )
    today_activity = next((a for a in activity if a.get('date') == today), {})

    return {
        "demo": False,
        "total_tokens": grand_total,
        "recent_30d_tokens": recent_total,
        "today_tokens": today_tokens,
        "today_messages": today_activity.get('messageCount', 0),
        "today_tool_calls": today_activity.get('toolCallCount', 0),
        "total_cost_usd": round(total_cost, 2),
        "models": model_stats,
        "updated_at": datetime.now().isoformat(timespec='seconds'),
    }

def main():
    out = Path(__file__).parent.parent / 'data' / 'usage.json'
    out.parent.mkdir(exist_ok=True)
    stats = read_claude_stats()
    result = compute_usage(stats)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[usage] 저장 완료: {out}")
    print(f"  총 토큰: {result.get('total_tokens', 0):,}")
    print(f"  총 비용: ${result.get('total_cost_usd', 0):.2f}")
    for m in result.get('models', []):
        print(f"  {m['label']}: {m['pct']}% ({m['tokens']:,}토큰, ${m['cost_usd']})")

if __name__ == '__main__':
    main()
