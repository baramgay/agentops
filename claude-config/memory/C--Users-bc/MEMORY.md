# 경남 민간데이터 분석 프로젝트 메모리

## 프로젝트 개요
- **목적**: 경남 청년 유출입 실태 분석 및 청년 정착 잠재 지역 발굴
- **데이터 기간**: 2018.01 ~ 2025.12 ✅ 완전 확보 (2026-03-19 기준)
- **산출물**: `D:\민간데이터\민간데이터 명세서\경남_청년정착잠재지역발굴_분석계획서.docx`
- **보고서 최종본**: `D:\업무\분석_청년생활인구\경남_청년정착잠재지역_분석보고서_최종.docx` (7826KB, 2026-03-23 기준)

## 2026-03-23 폴더 통합
- 두 폴더 통합 완료: 한자석 폴더 삭제, 순한글 분석_청년생활인구 단일 폴더로 정리
- 구버전 파일(output/구, data39, 로그, 보고서 백업) → _백업/ 폴더 이동
- 파일명 내 석(한자)→석(한글) 전면 교체 완료

## 데이터 위치
- KT: `D:\민간데이터\KT 데이터\`
- KB: `D:\민간데이터\KB 데이터\`
- KCB: `D:\민간데이터\KCB 데이터\`
- 명세서: `D:\민간데이터\민간데이터 명세서\`
- KT 참조파일: `D:\민간데이터\KT 데이터\00 참고 자료\00. 경남행정동코드_현황.csv`

## 핵심 검증 완료 사항

### KT 통신 데이터
- **구버전(2018~2022)**: 헤더 있음, 인코딩 **utf-8(-sig)** — cp949 아님. preprocess_all.py는 utf-8 → cp949 순서로 시도.
- **신버전(2023~2025)**: **헤더 없음** — `header=None` 필수
  - 파일명 앞 6자리 숫자 여부로 구분 (`fname[:6].isdigit()`)
- **유입 컬럼 순서**: `base_date | sgg_cd(목적지) | rsdn_sgg_cd(출발지) | m10~f75`
- **유출 컬럼 순서**: `base_date | rsdn_sgg_cd(경남출발) | sgg_cd(목적지) | m10~f75` ← 2·3번째 반대
- 청년 컬럼: `m20, m25, m30, m35, f20, f25, f30, f35` (5세 단위, 20~39세)
- 경남 시군구 코드: 앞 2자리 "48"
- 생활인구: `gn_living_pop_hjd_YYYYMM.csv`(~2022) + `native_admdong_sum_YYYYMM.csv`(2023~)

### KB국민카드 데이터
- **전 파일 헤더 없음** (`header=None`) — 2018~2022 통합본만 예외(헤더 있음)
- **age_cd 실제값**: `'2.2024'`(20~24), `'3.2529'`(25~29), `'4.3034'`(30~34), **`'5.3539'`(35~39)** — 마침표 포함, 20~39세
- SEXAGE 컬럼(10개): `hj_cd | cln_gb | ta_d | sex_cd | age_cd | buz_a | buz_b | buz_c | cnt | amt`
- RESIDENCE 컬럼(9개): `hj_cd | ta_d | buz_a | buz_b | buz_c | c_do_nm | c_ct_nm | cnt | amt`
- TIME 컬럼(8개): `hj_cd | cln_gb | ta_d | time | buz_a | buz_b | cnt | amt`
- **ms 보정계수 파일**: `D:\민간데이터\KB 데이터\ms파일(2025년버전이며-적용필요)\250000020137_1_GN_MODIFICATION_FACTOR_2512.csv`
  - 구조: `date(YYYYMMDD) | YYMM | factor(~0.145)` — 1일 1행, 월 단위 constant
  - **2018~2022 통합본**: preprocess_all.py에서 `cnt/=factor`, `amt/=factor` 보정 후 저장
  - **2023~2025**: `_ms` 파일 우선 사용 (이미 보정된 값)
  - 보정 결과: 2018~2025 연속 추이 확보 (2018: 153백만건, 2022: 171백만건, 2023: 178백만건, 2025: 153백만건)
  - 연도별 보정계수 평균: 0.141~0.153 범위로 안정적

### KCB 신용융합 데이터 (명세서 xlsx 검증 완료)
- **누적 데이터** → 최신 폴더만 사용: `(KCB)Your Region청_데이터_20251121`
- **인코딩**: cp949 (utf-8-sig 아님)
- **구분자**: pipe(`|`)
- **AP00002** (연령구간 5세): 21=20~24세, 22=25~29세, 31=30~34세, **32=35~39세** → 청년: `IN (21,22,31,32)` (20~39세)
- **MA00001**: **이미 1인당 값** (추산소득합계/가입자수, 千원/인) — 추가 나눗셈 불필요. preprocess_all.py에서 `income_per_cap = MA00001` (그대로 사용)
- **⚠️ 수정 이력**: 이전에 `/MP00001` 중복 나눗셈 버그 있었음 → 2026-03-18 수정 완료
- **MA00002**: 중위소득 (千원/인, MA00001과 동일 방식)
- **ML00009**: 대출잔액 합계 (千원) — 총합, /MP00001로 1인당 환산 필요
- **MC00006**: 3개월간 카드 이용금액 합계 (千원) — 총합, /MP00001로 1인당 환산 필요
- **MS00002**: **이미 1인당 값** (신용점수합계/가입자수, 0~1000점) — 추가 나눗셈 불필요. `credit_avg = MS00002` (그대로 사용)
- **RT_ICM_1~7**: 소득분위별 비율 (%, 1=2천만원미만, 7=7천만원초과)
- **MA00001_1~10**: 소득 구간별 총소득 합계 (천원)
- **MA00001_11~20**: 소득 구간별 인원 수 (명)
- STAT 파일: STAT_00(100m격자), STAT_02(행정동), STAT_07(전국시군구)

## 피드백
- [agents 활용 의미](feedback_agents_meaning.md): "agents 활용" = D:\업무\agents 멀티에이전트 시스템. 개발팀/빅데이터팀 등 팀명 → 해당 role.md 참조하여 작업 위임
- [한자 사용 금지](feedback_korean_hanja.md): '분석' 표기 시 한자(석) 혼용 금지, 순한글 '분석' 사용
- [차트 스타일 규칙](feedback_chart_style.md): ax.set_title() 금지, 폰트 크기 크게 (xlabel/ylabel 22+, tick 18+, legend 17+)
- [보고서 검증 규칙](feedback_report_verification.md): 보고서 수치 수정 시 반드시 CSV 데이터와 1:1 대조 후 수정, verify_report.py로 96개 항목 자동검증. matplotlib ncol=2 legend는 column-by-column 순서 (col1+col2 단순 연결). 감소폭 순위: 하동(-45.1%) > 창녕(-43.8%) > 고성(-43.3%) > 함안(-42.7%) > 통영(-41.0%) > 합천(-40.9%), 밀양은 12위(-29.1%)
- [sequential-thinking 사용 규칙](feedback_sequential_thinking.md): 시각화 검토 또는 분석 결과 검토 시 sequential-thinking MCP 항상 사용

## 연령 정의 — 전 데이터 20~39세로 통일 (2026-03-20 완료)
- **모든 데이터소스**: KT/KB/KCB/주민등록 모두 20~39세로 통일
- preprocess_all.py 상수: YOUTH_M=['m20','m25','m30','m35'], YOUTH_F=['f20','f25','f30','f35']
- KB_YOUTH_AGES=['2.2024','3.2529','4.3034','5.3539'], KCB_YOUTH_AP=[21,22,31,32]
- POP_YOUTH_AGES=['20 - 24세','25 - 29세','30 - 34세','35 - 39세']
- LIVING50_YOUTH_M=['M20','M30'], FLOAT50_YOUTH_M=['M20','M25','M30','M35']

## KT OD 데이터 구조
- `4. 유입인구/` 폴더: 신형(2023~) = `{ym}_경남_구단위유입.csv`, 구형(~2022) = `gn_inflow_pop_si_{ym}.csv`
- `5. 유출인구/` 폴더: 신형(2023~) = `{ym}_경남_구단위유출.csv`, 구형(~2022) = `gn_outflow_pop_si_{ym}.csv`
- **주의**: `gn_inflow_pop_si_` (실제 파일) vs `gn_inflow_pop_sgg_` (코드에서 탐색) → 2018~2022 구형 데이터는 연도별 통합본 서브폴더에서 읽힘
- 08_kt_od_sido_monthly.csv: 2026-03-19 재처리 완료, 201801~202512 (69,586행)

## 50cell 연간 파일 재생성 방법
- `C:\Users\bc\rebuild_annual.py` — monthly → annual 집계 (청크 방식)
- 결과: `10_kt_50cell_living_annual.csv`, `11_kt_50cell_floating_annual.csv`
- 컬럼: `cell_id | admi_cd | youth | youth_m | youth_f | year | longitude | latitude`
- ⚠️ 원래 rebuild_annual.py(Python 루프)는 너무 느림 → **rebuild_annual_fast.py** 사용 (pandas 벡터화, 약 10분)
- 생활인구 결과: 201.3MB, 2,954,067행 / 유동인구 결과: 121.4MB, 2,070,332행

## 전처리 최종 상태 (2026-03-20 전체 재처리 완료)
| 파일 | 상태 | 비고 |
|------|------|------|
| 01_kt_living_sgg | ✅ 재처리 | 20~39세 (m20~m35) |
| 02_kt_migration_sgg | ✅ 재처리 | 20~39세 |
| 03_kcb_youth_sgg | ✅ 재처리 | age_grp [21,22,31,32] |
| 04_kt_living_dong | ✅ 재처리 | 20~39세 |
| 06_kb_youth_sexage | ✅ 재처리 | age_cd [2.2024~5.3539] |
| 08_kt_od_sido | ✅ 재처리 | 20~39세 |
| 09_population_sgg | ✅ 재처리 | 20~39세 |
| 10,11 monthly | ✅ 재처리 완료 | 2026-03-20 완료 (20~39세, 좌표 100% 커버) |
| 10,11 annual | ✅ 재생성 완료 | rebuild_annual_fast.py 실행 완료 (2026-03-21) |
- analyze_youth.py: 재실행 완료, output/ 폴더 갱신, verify_report.py 96/96 OK

## 2026-03-20 세션 완료 작업
- preprocess_all.py 연령 상수 전체 20~39세로 수정 (9개 상수)
- 데이터 재처리: KB(06), KT이동(02), KT OD(08), 주민등록(01), KCB(03), KT생활인구(01,04)
- analyze_youth.py 내 잘못된 "20~34세" 표기 3곳 수정 (L726, L735, L983)
- 보고서 [210] "30대 초반(30~34세)" → "30대 후반(35~39세)" 수정
- verify_report.py: 96/96 OK
- 보고서 수치와 데이터 완전 일치 확인

## 2026-03-21 세션 완료 작업
- 50cell monthly 재처리 완료 (20~39세, 좌표 100% 커버)
- rebuild_annual_fast.py: 생활인구(211MB) + 유동인구(127MB) annual 재생성
- analyze_50cell_v39.py: data39→data로 변경, 차트 15~18 재생성 및 보고서 이미지 9개 교체
- 보고서 텍스트 수정: [175] 22,762개→404,219개, [177] 격자수, [178] 비율, [179] 변화율
- verify_report.py: 96/96 OK

## 50cell 최종 수치 (2026-03-21 기준)
- 2025년 경남 격자: 404,219개 (좌표 100% 커버)
- 유동/생활 비율 상위: 의령군(150%)·합천군(142%)·남해군(142%)·산청군(136%)·밀양시(132%)
- 유동/생활 비율 하위: 양산시(90%)·거창군(72%)
- 2022→2025 변화율 상위: 김해시(+29.6%)·거창군(+22.8%)·창원시(+20.6%)·양산시(+19.7%)
- 모든 18개 시군 증가 (음수 없음)

## 향후 작업 예정
- [50cell 상위 5개 구역 표](project_50cell_top5_table.md): 격자 분포 차트의 밀도 상위 5개 구역(읍면동명·밀도)을 표로 정리해 보고서에 추가

## KT 데이터 특성
- [KT 데이터 스냅샷 특성](project_kt_snapshot.md) — 체류인일은 일별 기지국 관측 스냅샷 누적; 실제 이동인구 수(명)와 다름; 보고서에 반드시 명시
- [민간데이터 전처리 학습](project_minsdata_preprocessing.md) — KT/KB/KCB 파일 구조, 인코딩, 함정 패턴, 만족스러운 해결책 총정리 (2026-03)

## 멀티에이전트 레포
- [agents 레포 및 동기화](reference_agents_repo.md) — D:/업무/agents, your-email@example.com, pull 위주 운용

## API 키
- [카카오 REST API 키](reference_kakao_api.md): 지오코딩 등 카카오 API 사용 시 참조

## 스크립트 위치
- `C:\Users\bc\run_kb_only.py` — KB 단독 재처리 (ms 보정 포함)
- `C:\Users\bc\run_kcb_only.py` — KCB 단독 재처리
- `C:\Users\bc\run_kcb_reprocess.py` — KCB 재처리 (2026-03-20 생성)
- `C:\Users\bc\run_kt_living.py` — KT 생활인구(01,04) 재처리 (2026-03-20 생성)
- `C:\Users\bc\run_50cell.py` — 50cell 강제 재처리 (기존 파일 삭제 후 사용)
- `C:\Users\bc\run_od_with_log.py` — KT OD 단독 재처리 (로그: out_od.log)
- `C:\Users\bc\run_reprocess_selective.py` — KB/KT이동/KT OD/주민등록 일괄 재처리
- `C:\Users\bc\rebuild_annual_fast.py` — 50cell annual 재생성 (빠른 버전, pandas 벡터화 ~10분)
- `C:\Users\bc\analyze_youth.py` — 최종 분석 시각화 (22개 PNG)
- `D:\업무\분석_청년생활인구\preprocess_all.py` — 전처리 통합 스크립트 (폴더명은 실제 디스크 경로 그대로)
- `C:\Users\bc\make_youth_report2.py` — 최종 분석계획서 생성 스크립트 (파일명은 실제 디스크 경로 그대로)
- `C:\Users\bc\check_kcb_spec2.py` — KCB 명세서 확인용
- `C:\Users\bc\verify_report.py` — 보고서 수치 96개 자동검증 스크립트
- `C:\Users\bc\finish_all.py` — 50cell 완료 후 전체 마무리 자동화
