---
name: reference-gis-resources
domain: 공공데이터소스
description: 경남 GIS 공용 자원 저장소 위치 및 경계 데이터 사용법 — 단계구분도 제작 시 참조
metadata: 
  node_type: memory
  type: reference
  originSessionId: d946fcc3-f37c-4314-9118-4d03260c267e
---

## 공용 GIS 자원 저장소

**위치**: `C:\업무\estate\data\external\gis_resources\`  
**README**: `C:\업무\estate\data\external\gis_resources\README.md`

> 2026-05-31 이동: 기존 `C:\업무\gis_resources\` → estate 프로젝트 내부로 통합

## 핵심 파일
- `boundaries/korea_municipalities_2018.geojson` — 전국 250개 시군구 경계 (17MB, EPSG:4326)
- `boundaries/gyeongnam_emd_2026.geojson` — 경남 읍면동 경계 (generate_choropleth_umd.py 사용)
- `boundaries/skorea_submunicipalities_2018.geojson` — 전국 읍면동 경계 (3,504개)
- 출처: southkorea-maps (통계청 2018년 행정구역 기준)

## 경남 필터링 — 반드시 코드 38xxx 기준
```python
GIS_ROOT = Path(r"C:\업무\estate\data\external\gis_resources")
gdf = gpd.read_file(GIS_ROOT / "boundaries" / "korea_municipalities_2018.geojson")
gyeongnam = gdf[gdf["code"].str.startswith("38")].to_crs(epsg=5186)
```

**Why:** 이름 기반 필터 사용 시 강원도 고성군(32400)이 경남 고성군(38340)과 동명 중복 포함 → bbox가 한반도 북동쪽까지 확장되는 버그 발생 (2026-05-21 부동산월보 P7에서 발견)

## 창원시 구 단위: 코드 3811x
```python
changwon_gu = gdf[gdf["code"].str.startswith("381")].copy()
```

## 관련 에이전트
- [[gis-specialist]] memory.md에 상세 코드 스니펫 포함
- 부동산 월보 스크립트: `C:\업무\estate\scripts\report\generate_maps_p7.py`
