---
name: method-image-clinical-quality
type: method
domain: 합성데이터스튜디오
updated: 2026-06-09
---

# 임상 구강 이미지 합성 품질 개선 방법론

## 결론

확산 i2i 합성 이미지의 비현실성은 (1) 빈약한 프롬프트, (2) strength 미조정, (3) 후처리 부재의 세 원인이 복합된다. 세 층을 모두 개선해야 임상 수준 품질에 도달한다.

## 적용 스택

### 1. 임상 촬영 조건 명시 프롬프트 (buildInstruction)

```
DSLR macro 1:1 magnification, f/16 aperture, standardized dental ring-flash, ISO 100, clinical white balance.
moist intraoral tissue with specular highlights on enamel facets, visible stippling on attached gingiva ...
```

- f/16: 전체 피사계심도 → 전 치아 선명
- ring-flash: 그림자 없는 균일 조명
- 습윤 조직·반사광(specular highlight) 명시 → 생체 사실성 핵심

### 2. strength 최적 범위 (Pisano et al. 1998 + 실험)

| 범위 | 효과 |
|------|------|
| < 0.40 | 원본 복사에 가까움, 다양성 부족 |
| **0.55~0.70** | 구강 해부학 유지 + 병변 다양성 균형 **권장** |
| > 0.80 | 해부학 구조 붕괴 |

기본값 0.65 (UI 슬라이더: 0.30~0.85)

### 3. 클라이언트 후처리 파이프라인 (pipelineImage.js)

```
CLAHE → 언샵마스크 → 임상 색온도 보정
```

**CLAHE** (Contrast Limited Adaptive Histogram Equalization, Pisano 1998):
- tileN=8, clipLimit=3.0, bilinear 보간
- 과도한 대비 억제(clipLimit) + 타일 경계 부드럽게

**언샵마스크** (임상 치과 사진 선명도 강화):
- 가우시안 1D 커널, 수평+수직 패스
- radius=1.5, amount=0.45, threshold=8
- threshold=8로 노이즈 증폭 방지

**임상 색온도 보정** (~5500K):
- R+3, G+1, B-4 오프셋
- 채도 1.08x
- 치과 링플래시의 자연광 색온도 방향

### 4. 강화 네거티브 프롬프트

X-ray·파노라믹·CBCT·해부모형·치과 팬텀·typodont 명시 억제 — 비임상 artifact 방지

### 5. 병변 패턴 10종 (LESION_PATTERNS)

정상 / 초기충치(white spot) / 중등도충치 / 진행성충치 / 경미치석 / 중증치석+치은염 / 치은염 / 교합면마모 / 외인성착색 / 수복치아

### 6. 품질 점수 (computeQualityScore)

Laplacian 분산 기반 선명도 + RMS 대비 → 0~1 종합 점수
UI에 Q값(0~100) 배지로 표시. ≥70 녹색 / 50~69 노랑 / <50 빨강

## 왜 이 순서인가

- 프롬프트가 선행 → 확산 모델이 올바른 분포에서 샘플링
- strength가 구조 보존/다양성 균형을 결정 (모델 입력)
- 후처리는 이미 생성된 이미지의 세부 대비·선명도 보정 (후단)
- 품질 점수는 컬링 기준 제공 (가장 마지막)

## 적용 위치

- `pipelineImage.js`: CLAHE/언샵/색온도/buildInstruction/LESION_PATTERNS/computeQualityScore/applyPostProcess
- `imageGen.ts`: strength 파라미터 전달, DEFAULT_NEGATIVE 강화
- `GenerateStep.jsx`: strength 슬라이더 UI + 후처리 토글 + 품질 점수 배지
