---
name: "bigdata-analysis-report"
description: "Your Organization 빅데이터 분석 보고서 7블록 양식(표지→요약→개요→설계→프로세스→결과→결론) 작성 파이프라인. Use when reporter starts a big-data analysis report or asks to assemble a new analysis report following the Your Organization 표준 양식."
user-invocable: true
argument-hint: "[분석 주제: 예 '청년정착 잠재지역 발굴' (생략 시 사용자에게 질의)]"
---

# Your Organization 빅데이터 분석 보고서 7블록 파이프라인

부동산 동향 월보(realty-analyst 담당 8섹션)와 **완전히 별도**인 빅데이터 분석 보고서 전용 파이프라인.
담당: `reporter` (빅데이터팀, lead-data 검토)

---

## 핵심 자료 위치

| 자료 | 경로 | 용도 |
|---|---|---|
| 양식 명세 (8종) | `docs/analysis-templates/` | 7블록 각 섹션 상세 규칙 (단일 진실 소스) |
| 표본 보고서 (4종 PDF) | `docs/analysis-templates/samples/` | 실제 작성 양식 참조 |
| 절차 문서 | `workflows/bigdata_analysis_report.md` | PHASE별 작업 순서 |
| 페르소나·학습 패턴 | `agents/reporter/role.md`, `memory.md` | reporter 능력·노하우 |

---

## 7블록 양식 (단일 진실 소스: docs/analysis-templates/)

```
[1] 표지              docs/analysis-templates/01_표지.md
[2] 요약              docs/analysis-templates/02_요약.md
[3] Ⅰ 분석개요         docs/analysis-templates/03_분석개요.md
[4] Ⅱ 분석설계         docs/analysis-templates/04_분석설계.md
[5] Ⅲ 분석 프로세스    docs/analysis-templates/05_분석프로세스.md
[6] Ⅳ 분석결과         docs/analysis-templates/06_분석결과.md
[7] Ⅴ 결론 및 시사점   docs/analysis-templates/07_결론및시사점.md
```

**양식 규칙 변경 시**: `docs/analysis-templates/`만 수정. 본 SKILL.md에는 복제하지 않음 (중복 방지).

---

## 표본 보고서 (학습 완료)

| 보고서 | 페이지 | 특징 |
|---|---|---|
| 고령층 의료접근성 취약지 발굴 분석 | 28p | 등급 5분위 + A·B·C 유형 |
| 경남 청년 정착 잠재지역 발굴 분석 | 41p | 5개 지표 z-score 가중합산 |
| 경남 제조업특화시군 산업활력 진단 분석 | 28p | 분석 한계 추가 블록 |
| 경남 도민 정책 수요 발굴 분석 | 41p | NLP/LDA/TF-IDF |

표본 PDF: `docs/analysis-templates/samples/`

---

## 파이프라인 트리거

```bash
# 절차 실행
cat workflows/bigdata_analysis_report.md

# reporter 상태 시작
python scripts/update_status.py reporter working "[분석 주제] 보고서 작성 시작"

# 라우팅 검증 (모호 키워드 확인)
python scripts/route_report.py "[사용자 요청 문장]"
```

---

## 부동산 동향 월보와의 차이 (혼용 금지)

| 항목 | 빅데이터 분석 보고서 (본 스킬) | 부동산 동향 월보 |
|---|---|---|
| 양식 | 7블록 고정 | 8섹션 자유 |
| 빈도 | 분석 주제별 1회성 | 매월 정기 |
| 담당 | reporter | realty-analyst |
| 스킬 | bigdata-analysis-report | realty-pipeline |
| 워크플로우 | bigdata_analysis_report.md | estate_monthly_report.md |
| 검토 | lead-data 1차 | lead-data 1차 + orchestrator 2차 |

---

## 보고서 수치 검증 (필수)

```bash
# 보고서 내 모든 수치를 분석 출력 CSV와 1:1 자동 대조
python verify_report.py [보고서경로]
# 통과 기준: N/N OK (불일치 0건)
```

---

## 민간데이터 필수 각주

| 데이터 | 보고서 명시 사항 |
|---|---|
| KT 생활인구 | 체류인일(기지국 누적). 실거주 인원수와 구별 |
| KB 카드소비 | ms 보정 적용 여부 각주. 현금·계좌이체 미포함 |
| KCB 신용융합 | 가입자 기반 표본. 비가입자 제외 |
| 연령 정의 | 청년 = 20~39세 통일 |

---

## 완료 처리

```bash
python scripts/finish_phase.py bigdata_analysis_report PHASE6 \
    --learn "[이번 보고서에서 발견한 새 패턴·실수·해결책]" \
    --agents reporter,lead-data
```
