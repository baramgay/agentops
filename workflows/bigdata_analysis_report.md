# Your Organization 빅데이터 분석 보고서 파이프라인

> 부동산 동향 월보(realty-analyst 담당, 8섹션)와 **완전히 별개** 입니다.
> 7블록 고정 양식 전용. 단일 진실 소스: `docs/analysis-templates/`

## 양식 구분 (혼용 절대 금지)

| 구분 | 빅데이터 분석 보고서 (이 워크플로우) | 부동산 동향 월보 |
|---|---|---|
| 담당 에이전트 | reporter | realty-analyst |
| 양식 | 7블록 고정 | 8섹션 자유 |
| 빌드 | docx 또는 HTML | build_report_p8.py (HTML+PDF) |
| 발간 주기 | 분석 주제별 1회성 | 매월 정기 |
| 검토 | lead-data 1차 | lead-data 1차 + orchestrator 2차 |
| 스킬 | skills/bigdata-analysis-report | skills/realty-pipeline |

---

## 에이전트 지휘 체계

```
사용자
  └→ orchestrator                (요청 라우팅·우선순위)
       └→ lead-data              (분석 전략·품질 검토)
            └→ reporter          (보고서 조립·납품)
                 ├→ visualizer    (차트 PNG 수령)
                 ├→ gis-specialist (지도 수령)
                 ├→ text-analyst  (텍스트 분석 수령)
                 └→ statistician/ml-engineer (수치 결과 수령)
```

라우팅 검증:
```bash
python scripts/route_report.py "[사용자 요청 문장]"
# → [라우팅] reporter — 빅데이터 분석 보고서 (7블록 양식)
```

---

## PHASE 0: 착수 선언

```bash
python scripts/update_status.py orchestrator working "[분석 주제] 빅데이터 분석 보고서 작업 지시"
python scripts/update_status.py lead-data     working "[분석 주제] 보고서 작업 배정"
python scripts/update_status.py reporter      working "[분석 주제] 7블록 보고서 작성 시작"
```

---

## PHASE 1: 분석 결과 수합

수집할 입력:
- 정제 데이터 CSV (`output/clean/`)
- 시각화 차트 PNG (visualizer로부터, 300DPI)
- GIS 단계구분도 (gis-specialist로부터)
- 통계 결과 (statistician/ml-engineer로부터)
- 텍스트 분석 결과 (text-analyst로부터, 해당 시)

확인사항:
- [ ] 분석 주제명 확정 (표지 줄바꿈 결정)
- [ ] 과제 구분 (자체발굴/수요대응/정기분석) — 기본값 `자체발굴`
- [ ] 작성자 — 기본값 `Your Organization 팀장 이 현 기`
- [ ] 시군별 개별 페이지 포함 여부 (18p 추가)

---

## PHASE 2: 양식 명세 검토

```bash
# 8개 양식 MD 핵심 확인 (사람이 검토)
ls docs/analysis-templates/
# 경남분석보고서.md 01_표지.md 02_요약.md ...

# 표본 보고서 대조 (필요 시)
ls docs/analysis-templates/samples/
```

매 섹션 작성 전 해당 양식 명세 확인:
- [1] 표지: `01_표지.md` — 줄바꿈 기준, "분석" 마지막 위치
- [2] 요약: `02_요약.md` — 200~400자, 4문단 역할, 종결어미
- [3] Ⅰ 개요: `03_분석개요.md` — 추진배경 / 필요성 / 활용처 3소제목
- [4] Ⅱ 설계: `04_분석설계.md` — 요구사항 / 분석방법 / 데이터표 6열
- [5] Ⅲ 프로세스: `05_분석프로세스.md` — 수집·전처리 / 분석·시각화
- [6] Ⅳ 결과: `06_분석결과.md` — 4가지 페이지 패턴(A~D), 6불릿 표준
- [7] Ⅴ 결론: `07_결론및시사점.md` — ▢블록 3개, y불릿, 종결어미

---

## PHASE 3: 7블록 조립

블록별 작성 순서:
1. **표지** — 주제명 의미 단위 줄바꿈 (예: `청년 정착 / 잠재지역 발굴 분석`)
2. **요약** — 분석 대상→결과→유형 분류→정책 방향 (과거형 서술체)
3. **Ⅰ 개요** — 추진배경(4~5불릿) + 필요성(4~5) + 활용처(4~5) — 명사형 종결
4. **Ⅱ 설계** — 요구사항(4~6) + 분석방법(4~6, 지표 산출식) + 데이터표 6열
5. **Ⅲ 프로세스** — 1. 수집·전처리(가/나/다) + 2. 분석·시각화(가/나/다)
6. **Ⅳ 결과** — 중섹션 5~7개, 패턴 A(불릿 5~6 + 그림 1)/B(그림 2)/C(표)/D(지도)
7. **Ⅴ 결론** — ▢ 분석 결과 종합 + ▢ 정책적 시사점 + ▢ 향후 과제 (y불릿)

각 섹션 작성 후 양식 명세 체크리스트 통과 확인.

---

## PHASE 4: 보고서 빌드

옵션 1: HTML A4 페이지 분리
```bash
# build_html_report.py 등 (개별 분석 프로젝트 스크립트)
```

옵션 2: Word (.docx) 직접 생성
```bash
# python-docx 사용, 표지/요약/Ⅰ~Ⅴ 각 페이지 add_page_break
```

출력: `output/report/report_[주제]_[날짜].{html|docx|pdf}`

---

## PHASE 5: 수치 검증

```bash
python verify_report.py output/report/report_[주제]_[날짜].html
# 모든 수치 (예: 96/96 OK) 자동 검증 통과 후만 납품
```

수치 불일치 시:
- 보고서 텍스트만 수정하지 말 것
- 반드시 원본 CSV 확인 후 수정 (재계산 금지)
- 수정 후 verify_report.py 재실행

---

## PHASE 6: 검토 및 납품

자체 점검:
- [ ] 한자/일본어 0건 (`scripts/validate.py` 한자 검사)
- [ ] 7블록 모두 존재 (표지/요약/Ⅰ/Ⅱ/Ⅲ/Ⅳ/Ⅴ)
- [ ] 캡션 번호 없음 (`[그림]`/`[표]`만)
- [ ] 민간데이터 한계 각주 (KT 체류인일·KB ms 보정·KCB 가입자) 포함
- [ ] 단정 표현 없음
- [ ] 그래프 n수·출처 표기

lead-data 1차 검토 요청 → 통과 후 납품:
```bash
python scripts/finish_phase.py bigdata_analysis_report PHASE6 \
    --learn "[이번 보고서에서 발견한 패턴·해결책]" \
    --agents reporter,lead-data
```

---

## 산출물 위치

```
output/report/
  ├── report_[주제]_[날짜].html
  ├── report_[주제]_[날짜].docx
  ├── report_[주제]_[날짜].pdf
  └── verify_[주제].log
```

---

## 주의사항

### 양식 명세 위치 일원화
- 모든 양식 규칙은 `docs/analysis-templates/` 에만 있음
- 본 워크플로우/SKILL.md에 복제 금지 — 변경 시 단일 위치만 수정
- reporter agent도 양식 규칙은 docs/에서 항상 최신 참조

### 단정 표현 금지
- 사용 금지: "확실히", "반드시", "최고", "최저" 단정
- 권장: 데이터 근거 인용 + 불확실성 병기

### 한자·일본어 절대 금지
- 모든 보고서 텍스트, 캡션, 파일명 순한글
- "분석"은 U+BD84+U+C11D만 사용 (한자 U+6790 금지)
- 검증: `python scripts/validate.py | grep 한자`

### memory.md 수정 후 필수
```bash
cd {AGENTS_ROOT} && python scripts/sync.py
```
