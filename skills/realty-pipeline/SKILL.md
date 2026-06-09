---
name: "realty-pipeline"
description: "경남 부동산시장 동향 월보 생성 파이프라인. 데이터 수집 → 지오코딩 → 차트 → 보고서 → PDF → 검토 배포 6단계를 순서대로 안내한다. Use when realty-analyst starts monthly report work or asks to run/resume the estate report pipeline."
user-invocable: true
argument-hint: "[월 지정: YYYY-MM (생략 시 당월 자동)]"
---

# 경남 부동산시장 동향 월보 파이프라인

빅데이터 분석 보고서(reporter 담당 7블록 양식)와 **완전히 별도**인 월보 전용 파이프라인.
담당: `realty-analyst` (lead-data 산하, 2중 검토 필수)

---

## 파이프라인 실행 전 확인사항

```python
# 매월 변경 필요한 경로 상수 (7개 스크립트 일괄 치환)
TARGET_MONTH = "2026-06"   # ← 이번 달로 변경
TARGET_YEAR  = "2026"
TARGET_MM    = "06"
BASE = r"{ESTATE_ROOT}"
RAW  = rf"{BASE}\data\raw\{TARGET_MONTH}"
PROC = rf"{BASE}\data\processed\{TARGET_MONTH}"
OUT  = rf"{BASE}\reports\{TARGET_YEAR}\{TARGET_MM}"
```

치환 대상 스크립트 7개:
- `scripts/report/generate_charts_p6.py`
- `scripts/report/build_report_p8.py`
- `scripts/report/export_pdf.py`
- `scripts/collect/geocode_kakao.py`
- `scripts/report/generate_choropleth_umd.py`
- `scripts/report/generate_heatmap_grid.py`
- `scripts/collect/collect_rone.py`

---

## STEP 1 — 데이터 수집

```bash
cd {ESTATE_ROOT}
python scripts/collect/collect_rone.py          # R-ONE 한국부동산원 9개 지표
python scripts/collect/collect_molit_rtms.py    # 국토교통부 실거래가 (아파트+연립+단독)
python scripts/collect/collect_news.py          # 경남 부동산 뉴스 (Naver API)
```

출력: `{ESTATE_ROOT}\data\raw\{YYYY-MM}\`

### R-ONE 확정 STATBL_ID (9개)

| indicator_id | STATBL_ID | 통계명 |
|-------------|-----------|--------|
| sales_idx_apt | A_2024_00045 | (월) 매매가격지수_아파트 |
| jeonse_idx_apt | A_2024_00050 | (월) 전세가격지수_아파트 |
| jeonse_ratio_apt | A_2024_00072 | (월) 평균 매매가격 대비 전세가격_아파트 |
| sales_idx_housing | A_2024_00016 | (월) 매매가격지수_주택종합 |
| jeonse_idx_housing | A_2024_00019 | (월) 전세가격지수_주택종합 |
| sales_idx_rowhouse | A_2024_00080 | (월) 매매가격지수_연립/다세대 |
| jeonse_idx_rowhouse | A_2024_00085 | (월) 전세가격지수_연립/다세대 |
| sales_idx_detached | A_2024_00114 | (월) 매매가격지수_단독주택 |
| jeonse_idx_detached | A_2024_00119 | (월) 전세가격지수_단독주택 |

> ⚠️ A_2024_00031 = 중위전세가격 (아파트 매매 아님) — **절대 사용 금지**

### 수집 대기 (14개 — 다음달 추가 목표)
`trade_housing A_2024_00546`, `trade_apt A_2024_00549`, `unsold T237973129847263`,
`sentiment_housing T232543129897499`, `permit T235263129553687` 등

---

## STEP 2 — 지오코딩 (신규 단지 발생 시 또는 최초 실행 시)

```bash
python scripts/collect/geocode_kakao.py
```

- API: Kakao Local — `KakaoAK {KAKAO_REST_API_KEY}`
- 쿼리: `f"경남 {시군구명} {umdNm} {aptNm}"`
- Rate limit: 0.05초 sleep
- 캐시: `data/processed/{YYYY-MM}/geocode_cache.csv`
- 기준 실적(2026-05): 2,844건 → 2,257건 매칭(79.4%)

### sggCd → 시군구명 매핑
```python
SGG_NAME = {
    "48120":"창원시", "48121":"창원시의창구", "48122":"창원시성산구",
    "48123":"창원시마산합포구", "48124":"창원시마산회원구", "48125":"창원시진해구",
    "48170":"진주시", "48220":"통영시", "48240":"사천시", "48250":"김해시",
    "48270":"밀양시", "48310":"거제시", "48330":"양산시", "48720":"의령군",
    "48730":"함안군", "48740":"창녕군", "48820":"고성군", "48840":"남해군",
    "48850":"하동군", "48860":"산청군", "48870":"함양군", "48880":"거창군",
    "48890":"합천군",
}
```

---

## STEP 3 — 차트 생성

```bash
python scripts/report/generate_charts_p6.py         # 메인 차트 C01~C25
python scripts/report/generate_choropleth_umd.py    # 읍면동 단계구분도
# 선택사항
python scripts/report/generate_heatmap_grid.py      # 100m 격자 히트맵
```

출력: `{ESTATE_ROOT}\data\processed\{YYYY-MM}\charts\` (PNG 300dpi)

### 차트 코드표 (C01~C25)

| 코드 | 섹션 | 차트명 | figsize |
|------|------|--------|---------|
| C01 | 1-1 | 매매·전세가격지수 추이 | (6.7, 4.04) |
| C02 | 1-2 | 18시군 매매 히트맵 | auto |
| C03 | 1-2 | 18시군 전세 히트맵 | auto |
| C04 | 1-3 | 미분양 현황 | (6.7, 3.50) |
| C05 | 1-4 | 거래량 현황 | (6.7, 4.04) |
| C06 | 1-5 | 시군비교 매매 | (6.7, 4.04) |
| C07 | 2-1 | 히트맵 전월대비 | auto (x축 rotation=0) |
| C08 | 2-2 | 시군 매매·전세 산점도 | (6.7, 4.04) |
| C09 | 2-3 | 거래량 랭킹 | (6.7, 4.04) |
| C10 | 2-4 | 미분양 랭킹 | (6.7, 4.04) |
| C11 | 2-5 | 전세가율 (Line2D 범례) | (6.7, 4.04) |
| C12 | 3-1 | GIS 시군 매매 단계구분도 | (6.7, auto) |
| C13 | 3-2 | GIS 시군 전월대비 | (6.7, auto) |
| C14 | 4-1 | 창원 매매·전세 추이 | (6.7, 4.04) |
| C15 | 4-2 | 창원 거래량 | (6.7, 4.04) |
| C16 | 5-1 | 이슈시군 1 | (6.7, 4.04) |
| C17 | 5-2 | 이슈시군 2 | (6.7, 4.04) |
| C18 | 5-3 | 3시군 비교 | (6.7, 3.65) |
| C19 | 5-4 | 정규화 지표 | (6.7, 3.03) |
| C20 | 6-1 | 조기경보지수 | (6.7, 4.04) |
| C21 | 6-2 | 활력·공급 지수 | (6.7, 4.04) |
| C22 | 7-1 | 경매 낙찰가율 | (6.7, 4.85) |
| C23 | 7-2 | 감성분석 트렌드 | (6.7, 4.04) |
| C24 | 7-3 | 워드클라우드 | (6.7, 4.04) |
| C25 | 7-3 | 키워드 Top 15 (순수 빈도순) | (6.7, 4.04) |

> ⚠️ C25: 반드시 순수 빈도순 정렬 — TF-IDF 가중치 개입 금지
> ⚠️ C11: Line2D 범례 (80% 주의·85% 위험 기준선) 필수

### 핵심 색상 상수
```python
BG_SOFT   = "#F5F7FA"
NAVY      = "#1A3A6B"
ACCENT    = "#C0392B"
YELLOW_HL = "#F39C12"
FIG_FULL  = (6.7, 4.04)
FIG_HALF  = (3.2, 2.8)
```

### x축 연도 표기 규칙
```python
# 연도 첫 달(1월)에만 연도 표기, 나머지는 숫자만
# 예: '25.1, 2, 3, ..., 12, 1, 2, ..., '26.1
```

---

## STEP 4 — 보고서 빌드

```bash
python scripts/report/build_report_p8.py
```

출력: `{ESTATE_ROOT}\reports\{YYYY}\{MM}\gyeongnam_estate_report_{YYYYMM}.html`

### 보고서 섹션 구조 (8섹션 + Executive Summary)

| 코드 | 섹션명 | 내용 |
|------|--------|------|
| s0 | Executive Summary | 월간 핵심 요약 3~5개 인사이트 |
| s1 | Ⅰ 경남 종합 | 18개 시군 전체 동향 (1-1~1-5) |
| s2 | Ⅱ 시군 비교 | 매매·전세·거래량·미분양 시군 랭킹 |
| s3 | Ⅲ GIS 시각화 | 단계구분도, 변화량 지도 |
| s4 | Ⅳ 창원시 | 창원 5개 구 별 동향 (4-1~4-4) |
| s5 | Ⅴ 이슈 시군 심층 | 트리거 발생 1~3개 시군 |
| s6 | Ⅵ 복합 지수 | 조기경보·활력·공급압력 지수 |
| s7 | Ⅶ 경매·미디어 | 경매 낙찰가율·뉴스·유튜브 텍스트 |
| s8 | Ⅷ 보도자료 | 월보 요약 보도용 |

### chart-insight 블록 패턴
```python
def insight(code: str) -> str:
    items = INSIGHTS.get(code, [])
    if not items: return ""
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<div class="chart-insight"><ul>{lis}</ul></div>'
# CSS: .chart-insight { border-left: 3px solid var(--navy); padding-left: 12px; }
```

### 뉴스 링크 패턴
```python
title_html = (f'<a href="{link}" target="_blank" class="news-title-link">{title_esc}</a>'
              if link and link != "nan" else title_esc)
# 최신순 + 광고·중복 제거 후 30건 표시
```

### 페이지 나누기 CSS
```css
@media print {
  @page { margin:18mm 15mm 22mm 15mm; size:A4 }
  .page-break-wrap { page-break-before:always; break-before:page }
  .page-break-wrap .report-section { margin-top:5mm }
}
```

---

## STEP 5 — PDF 내보내기

```bash
python scripts/report/export_pdf.py
```

출력: `{ESTATE_ROOT}\reports\{YYYY}\{MM}\gyeongnam_estate_report_{YYYYMM}.pdf`

```python
# ⚠️ display_header_footer=False 필수
# True 설정 시 Playwright 내장 헤더가 표지 border-radius와 충돌
await page.pdf(
    path=str(PDF_FILE), format="A4", print_background=True,
    margin={"top":"18mm","bottom":"22mm","left":"15mm","right":"15mm"},
    display_header_footer=False,
)
```

---

## STEP 6 — 검토 및 배포

```bash
# 에이전트 상태 체인 (검토 → 배포 순서)
python {AGENTS_ROOT}\scripts\update_status.py realty-analyst done "월보 초안 완료 — lead-data 검토 요청"
python {AGENTS_ROOT}\scripts\update_status.py lead-data review "{YYYY-MM}호 검토 중"
python {AGENTS_ROOT}\scripts\update_status.py lead-data done "1차 검토 완료 — orchestrator 상신"
python {AGENTS_ROOT}\scripts\update_status.py orchestrator review "최종 배포 승인 검토"
python {AGENTS_ROOT}\scripts\update_status.py orchestrator done "{YYYY-MM}호 배포 승인"
```

### 2중 검토 체크리스트
- [ ] 이상치·오기재·논리 비약 없음 (lead-data)
- [ ] 수치 표·차트 라벨·시군명 표기 정확
- [ ] 단정 표현 없음 ("상승/하락/급등/급락" 금지)
- [ ] 한자·일본어 0건
- [ ] 전망 서술에 불확실성 표현 병기
- [ ] HTML 렌더링 확인, PDF 표지 border-radius 정상
- [ ] 정책 일관성·배포 적합성 (orchestrator)

---

## 코드 체계 및 오류 방지

### MOLIT ↔ southkorea-maps 코드 변환
```python
MOLIT_TO_SK = {
    "48121":"38111","48122":"38112","48123":"38113","48124":"38114","48125":"38115",
    "48170":"38030","48220":"38050","48240":"38060","48250":"38070","48270":"38080",
    "48310":"38090","48330":"38100","48720":"38310","48730":"38320","48740":"38330",
    "48820":"38340","48840":"38350","48850":"38360","48860":"38370","48870":"38380",
    "48880":"38390","48890":"38400",
}
# MOLIT 48xxx vs southkorea-maps 38xxx — 혼용 절대 금지
```

### 데이터 처리 표준
```python
df["sggCd"] = df["sggCd"].str[:5]                          # 앞 5자리만
df["dealAmount"] = df["dealAmount"].str.replace(",","").str.strip().astype(float)
df["umdNm"] = df["umdNm"].str.split().str[0]               # choropleth 전처리
```

### 표기 규칙
- CSV 인코딩: `UTF-8-sig`
- 시군명: 한글 전체 표기 (약칭 금지)
- 단위: 지수 / % / 호 / 건 / 만원 반드시 명시
- 변동 표기: `전월 대비 N% 변동` 또는 `+N.N%`

---

## 필수 환경 변수 ({ESTATE_ROOT}\.env)

```
KAKAO_REST_API_KEY=<.env 파일 또는 사용자 PC 로컬 메모리 참조>
CODEF_CLIENT_ID=(미확보)
CODEF_CLIENT_SECRET=(미확보)
NAVER_CLIENT_ID=(뉴스 수집용)
NAVER_CLIENT_SECRET=(뉴스 수집용)
```

## 필수 Python 패키지

```bash
pip install pandas numpy geopandas pyproj shapely
pip install matplotlib folium
pip install requests python-dotenv openpyxl
pip install playwright
playwright install chromium
```

## 폰트
- KoPubDotum Medium: `{FONTS_ROOT}\`
- 폴백: `plt.rcParams["font.family"] = "Malgun Gothic"`

---

## 보고서 버전 관리

| 호수 | 발간일 | 특이사항 |
|------|--------|---------|
| 2026-04호 | 2026-04 | 경로: C:\업무\분석_부동산동향최종\4월자료\작업스크립트\generate_april_v5.py |
| 2026-05호 | 2026-05-23 | 차트 C01~C25 전면 재설계, GIS choropleth, 실거래가 지오코딩, PDF Playwright |
