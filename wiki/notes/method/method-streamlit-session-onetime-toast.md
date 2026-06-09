---
name: method-streamlit-session-onetime-toast
type: method
domain: 이음지도
updated: 2026-06-08
---

# Streamlit session_state 1회 side-effect 제어 패턴

session_state 플래그로 비용 있는 알림/사이드이펙트를 첫 1회에만 발동시키는 패턴.

**Why:** Streamlit은 rerun마다 코드 전체가 재실행된다. 토스트·안내·초기화 같은 1회성 동작을 조건 없이 쓰면 매 rerun마다 반복 발동된다.

**How to apply:**
`python
# 조건: 첫 로딩 시에만 toast 표시
if show_osm and not st.session_state.get('_osm_cache_loaded'):
    st.toast('처음 1회는 30초 소요될 수 있습니다', icon='⏳')
# ... 실제 데이터 로드 ...
if show_osm and df_osm is not None:
    st.session_state['_osm_cache_loaded'] = True
`

- **플래그 명명**: _ 접두사 + 기능명 + _loaded/_shown/_done 형태 권장 (예: _osm_cache_loaded, _intro_shown)
- **초기화 필요 시**: 사용자가 레이어 끄고 다시 켤 때 재toast 원하면 플래그를 False로 리셋하는 시점 결정 필요
- **주의**: st.session_state.get(key, False) 로 None/미존재 모두 안전하게 처리
- **이음지도 적용**: app.py OSM 레이어 첫 Overpass API 호출(~30초) 안내 (2026-06-08)
