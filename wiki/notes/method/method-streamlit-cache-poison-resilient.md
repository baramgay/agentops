---
type: method
domain: 이음지도
tags: [streamlit, cache, resilient, pattern]
updated: 2026-06-08
---

# Streamlit 캐시 독(Cache Poison) 방지 — `_resilient` 패턴

## 문제

`@st.cache_data` 래퍼가 API 장애 시 `None` 또는 빈 DataFrame을 캐시에 저장하면,
TTL(최대 1시간)이 만료될 때까지 그 API 데이터가 서비스 불가 상태가 된다.

## 해결 — `_resilient` 헬퍼

```python
def _resilient(getter, *args):
    val = getter(*args)
    target = val[0] if isinstance(val, tuple) else val
    if target is None or (hasattr(target, "empty") and target.empty):
        try:
            getter.clear()        # 독이 든 캐시 무효화
            val = getter(*args)   # 재조회
        except Exception:
            _log.debug("캐시 독 재조회 실패: %s", getattr(getter, "__name__", getter), exc_info=True)
    return val
```

## 핵심 설계 결정

- **튜플 반환 투명 처리**: `(df, badge)` 형태로 반환하는 함수는 `val[0]`으로 DataFrame 추출 후 검사. 반환값은 원본 튜플 그대로 전달.
- **예외 격리**: 재조회 실패 시에도 최초 실패값 반환 — 앱 crash 금지.
- **일반화**: 기존 `get_weather_resilient`(날씨 전용)을 대체하는 범용 헬퍼.

## 적용 대상 (app.py)

| 호출 지점 | 교체 전 | 교체 후 |
|---|---|---|
| 복지시설 API | `get_welfare_api()` | `_resilient(get_welfare_api)` |
| 충전기 | `get_chargers()` | `_resilient(get_chargers)` |
| 이동지원센터 | `get_mobility_centers()` | `_resilient(get_mobility_centers)` |
| 병원 | `get_hospitals()` | `_resilient(get_hospitals)` |
| 주차 | `get_parking()` | `_resilient(get_parking)` |
| 부산 시설/관광 | 직접 반환 | `_resilient(get_busan_*)`로 경유 |

## 관련

- [[project-eumjido-improvements-2026-06]] — 이 패턴이 적용된 이음지도 개선 작업
- [[project-eumjido-streamlit-ops]] — Streamlit 운영 일반 노트
