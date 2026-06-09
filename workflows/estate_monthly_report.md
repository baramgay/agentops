# 경남 부동산 동향 월보 파이프라인

> **이 파이프라인은 빅데이터 분석 보고서(7블록 고정 양식, reporter 담당)와 완전히 별개입니다.**
> 부동산 동향 월보 전용 파이프라인이며, reporter 에이전트와 reporter의 7블록 양식을 절대 사용하지 않습니다.

## 양식 구분 (혼용 절대 금지)

| 구분 | 부동산 동향 월보 (이 워크플로우) | 빅데이터 분석 보고서 |
|------|-------------------------------|-------------------|
| 담당 에이전트 | realty-analyst | reporter |
| 양식 | 8섹션 자유 구성 (s0~s8) | 7블록 고정 (표지→요약→Ⅰ~Ⅴ) |
| 빌드 스크립트 | `build_report_p8.py` | 별도 스크립트 |
| 발간 주기 | 매월 정기 | 분석 주제별 1회성 |
| 검토 | lead-data 1차 + orchestrator 2차 | lead-data 1차 |
| 출력 | HTML + PDF (base64 차트 임베드) | docx/HTML/PDF |

> 매월 정기 실행. 다른 빅데이터 분석 파이프라인과 완전히 독립.
> 담당: orchestrator → lead-data → realty-analyst

---

## 에이전트 지휘 체계

```
사용자
  └→ orchestrator   (일정·우선순위·최종 승인)
       └→ lead-data  (데이터·통계 1차 검토)
            └→ realty-analyst  (전체 실행)
                 ├→ gis-specialist  (GIS 시각화 협업)
                 └→ text-analyst    (뉴스·텍스트 협업)
```

---

## 실행 순서

### PHASE 0: 착수 선언 (상태 업데이트)
```bash
python AGENTS_HOME\scripts\update_status.py orchestrator working "2026-MM호 부동산 동향 월보 작업 지시"
python AGENTS_HOME\scripts\update_status.py lead-data     working "2026-MM호 월보 작업 배정"
python AGENTS_HOME\scripts\update_status.py realty-analyst working "2026-MM호 월보 작업 시작"
```

---

### PHASE 1: 데이터 수집

#### 1-1. 폴더 준비
```
C:\업무\estate\data\raw\{YYYY-MM}\molit\         — 실거래가 CSV
C:\업무\estate\data\raw\{YYYY-MM}\rone\          — R-ONE 지표 JSON
C:\업무\estate\data\processed\{YYYY-MM}\         — 정제 데이터
C:\업무\estate\data\processed\{YYYY-MM}\charts\  — 차트 PNG
```

#### 1-2. R-ONE 지표 수집
```bash
cd C:\업무\estate
python scripts\collect\collect_rone.py
```
수집 대상 STATBL_ID:
| 지표 | STATBL_ID |
|------|-----------|
| 아파트 매매가격지수 | A_2024_00045 |
| 아파트 전세가격지수 | A_2024_00050 |
| 전세가율(아파트) | A_2024_00072 |
| 주택종합 매매가격지수 | A_2024_00016 |
| 주택종합 전세가격지수 | A_2024_00019 |
| 연립/다세대 매매 | A_2024_00080 |
| 연립/다세대 전세 | A_2024_00085 |
| 단독주택 매매 | A_2024_00114 |
| 단독주택 전세 | A_2024_00119 |

**⚠️ 금지 코드**: A_2024_00031 (중위전세가격 — 아파트 매매 아님!)

#### 1-3. 국토교통부 실거래가 수집
```bash
python scripts\collect\collect_molit_rtms.py
```
수집 파일:
- `rtms_apt_trade_경남.csv`     — 아파트 매매
- `rtms_row_trade_경남.csv`     — 연립/다세대
- `rtms_detached_trade_경남.csv` — 단독/다가구

#### 1-4. 뉴스 수집 (text-analyst 협업)
```bash
python scripts\collect\collect_news.py
```
필터링: 2,350건 → 886건 목표 (중복 제거 → 광고 제거 → 경남 주제 판별)

---

### PHASE 2: 지오코딩 (신규 단지 발생 시)
```bash
python scripts\collect\geocode_kakao.py
```
- API: Kakao Local API (`KAKAO_REST_API_KEY` in .env)
- 캐시: `data/processed/{YYYY-MM}/geocode_cache.csv`
- 목표 매칭률: 75%+
- 소요 시간: 약 3분 (2,800~3,000건)

---

### PHASE 3: 차트 생성

#### 3-1. 메인 차트 (C01~C25)
```bash
python scripts\report\generate_charts_p6.py
```
**매월 확인 필수**: 스크립트 내 `"2026-05"` → 당월 `"YYYY-MM"` 변경

#### 3-2. GIS 읍면동 단계구분도
```bash
python scripts\report\generate_choropleth_umd.py
```
- 방법: geocode lat/lon → admdongkor 2026 행정동 Spatial Join
- 출력: `choropleth_mom.html` / `choropleth_mom.png`

#### 3-3. (선택) 100m 격자 히트맵
```bash
python scripts\report\generate_heatmap_grid.py
```
- 현재 월보 미포함, 별도 HTML로 확인 후 포함 여부 결정

---

### PHASE 4: HTML 보고서 빌드
```bash
python scripts\report\build_report_p8.py
```
출력: `C:\업무\estate\reports\{YYYY}\{MM}\gyeongnam_estate_report_{YYYYMM}.html`

**매월 업데이트 필수 항목** (build_report_p8.py 내):
- INSIGHTS 딕셔너리 (C01~C25 해석 문구)
- Executive Summary 핵심 판단 3개
- 이슈 시군 선정 (5-1, 5-2)
- KPI 4개 수치

---

### PHASE 5: PDF 내보내기
```bash
python scripts\report\export_pdf.py
```
**⚠️ 필수 설정**: `display_header_footer=False` (True 시 표지 border 충돌)

---

### PHASE 6: 검토 및 배포

#### 6-1. 자체 점검
- [ ] 모든 차트 PNG 생성 확인 (charts/ 폴더)
- [ ] INSIGHTS 수치가 원자료와 일치하는지 대조
- [ ] 시군명 표기 오류 없는지 확인 (한글 전체 표기)
- [ ] 인사이트 단정 표현 없는지 검토 ("상승/하락" 단독 사용 금지)

#### 6-2. lead-data 1차 검토 요청
```bash
python AGENTS_HOME\scripts\update_status.py realty-analyst review "월보 초안 완성, lead-data 1차 검토 요청"
python AGENTS_HOME\scripts\update_status.py lead-data working "월보 1차 검토 중"
```

#### 6-3. orchestrator 2차 최종 승인
```bash
python AGENTS_HOME\scripts\update_status.py lead-data done "1차 검토 완료, orchestrator 상신"
python AGENTS_HOME\scripts\update_status.py orchestrator working "월보 최종 검토 중"
python AGENTS_HOME\scripts\update_status.py orchestrator done "승인 완료, 배포 가능"
python AGENTS_HOME\scripts\update_status.py realty-analyst done "2026-MM호 월보 발간 완료"
```

#### 6-4. 단일 명령 완료 처리 (권장)

PHASE 6 종료 시 아래 한 줄로 여러 에이전트 상태 + 학습 패턴 자동 축적:

```bash
python {AGENTS_ROOT}\scripts\finish_phase.py estate_monthly_report PHASE6 \
    --learn "{YYYY-MM}호 발간 시 발견한 핵심 패턴 (예: 새 차트 색상 충돌, PDF margin 조정 등)" \
    --agents realty-analyst,lead-data,orchestrator
```

- 첫 번째 에이전트(realty-analyst) 메모리에 학습 패턴 자동 append
- 모든 에이전트 status=done 일괄 처리
- --learn 본문에 한자 포함 시 자동 차단 (memory.md 미수정)

---

## 산출물 위치

```
C:\업무\estate\reports\{YYYY}\{MM}\
  ├── gyeongnam_estate_report_{YYYYMM}.html   — 메인 보고서
  ├── gyeongnam_estate_report_{YYYYMM}.pdf    — PDF 버전
  └── charts\                                  — 차트 PNG (C01~C25)

C:\업무\estate\data\processed\{YYYY-MM}\
  ├── geocode_cache.csv                        — 지오코딩 캐시
  ├── choropleth_mom.html                      — 읍면동 단계구분도
  ├── choropleth_mom.png                       — 읍면동 단계구분도 PNG
  └── heatmap_mom.html                         — 100m 격자 히트맵 (참고용)
```

---

## 환경 점검 (처음 실행 또는 새 PC)

```bash
# 패키지 설치
pip install pandas numpy geopandas pyproj shapely
pip install matplotlib folium admdongkor
pip install requests python-dotenv openpyxl
pip install playwright && playwright install chromium

# .env 확인
cat C:\업무\estate\.env
# → KAKAO_REST_API_KEY, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 필수

# GIS 경계 파일 확인
ls "C:\업무\gis_resources\boundaries\"
# → gyeongnam_emd_2026.geojson 없으면:
python -c "
import admdongkor as adk
import geopandas as gpd
gdf = adk.get('20260401')
gdf[gdf['sidocd']=='48'].to_crs('EPSG:4326').to_file(
    r'C:\업무\gis_resources\boundaries\gyeongnam_emd_2026.geojson',
    driver='GeoJSON', encoding='utf-8')
print('GeoJSON 생성 완료')
"
```

---

## 주요 주의사항

### 창원시 코드 불일치
MOLIT(48122~48125) ↔ admdongkor(48123/48125/48127/48129) — 상세 매핑 → gis-specialist/memory.md

### 법정동 vs 행정동
MOLIT 실거래가 = 법정동 기준 / admdongkor = 행정동 기준 — 이름 직접 매칭 불가
→ **좌표 기반 Spatial Join 필수** (geocode_cache.csv lat/lon 활용)

### YoY 히트맵 생성 조건
전년동월 데이터가 수집 범위에 포함되어야 함
- 예: 2026-06호 → 2025.06 데이터 필요 → 수집 범위: 2025.06~2026.06

### memory.md 수정 후 필수
```bash
cd AGENTS_HOME && python scripts/sync.py && python scripts/build_html.py
```
