# ChatGPT Image 2.0 — 에이전트 3D 캐릭터 생성 프롬프트

## 사용 방법
1. `avatar_reference.html`을 브라우저에서 열어 현재 픽셀아트 버전 확인
2. 아래 **STEP 0 스타일 레퍼런스** 먼저 생성 → 마음에 들면 나머지 진행
3. 각 프롬프트를 ChatGPT Image 2.0에 그대로 복붙
4. 생성된 이미지에서 각 캐릭터 개별 크롭 → `assets/avatars/[id].png` 저장
5. 최종 크기: 256×256px (또는 512×512 후 리사이즈)

---

## 공통 스타일 정의 (모든 프롬프트에 포함)

```
Style: 3D chibi toon render, soft cel-shading, rounded proportions,
big expressive eyes, pastel-accented dark background (#0D1117 style),
professional AI agent theme, clean studio lighting from above-left,
slight drop shadow, transparent-ready white padding border around each character,
each character in a separate labeled circular frame.
Consistent art style across all characters: same head-to-body ratio (1:1.2),
same lighting angle, same rendering quality.
Output: character sheet grid layout, white labels below each character.
```

---

## STEP 0 — 스타일 레퍼런스 테스트 (1장 먼저 생성)

> 이걸 먼저 생성해서 스타일을 검토하세요. OK면 나머지 6장 진행.

```
Create a 3D chibi character sheet with 2 AI agent characters for a Korean public data analytics team dashboard.

Style: 3D chibi toon render, soft cel-shading, rounded proportions (head:body = 1:1.2),
big expressive eyes, dark navy background (#0D1117), professional tech-office theme,
clean studio lighting from upper-left, slight drop shadow, each character in a circular frame.
Same rendering quality and lighting for all characters.

Character 1 — "Orchestrator" (총괄 오케스트레이터):
- Golden crown on head, authoritative pose with one hand raised conducting
- Royal blue and gold color scheme, confident smiling expression
- Label below: "orchestrator"

Character 2 — "Data Collector" (데이터 수집가):
- Brown detective hat, holding a magnifying glass
- Dark trench coat, curious searching expression
- Label below: "data-collector"

Layout: 2 characters side by side, circular frames, white text labels below each.
High quality, 1024x512px.
```

---

## IMAGE 1 — 리드팀 (4명)

```
Create a 3D chibi character sheet with 4 AI team leader characters for a Korean data analytics platform.

Style: 3D chibi toon render, soft cel-shading, head:body ratio 1:1.2,
big expressive eyes, dark navy background (#0D1117), professional leadership theme,
clean studio lighting upper-left, slight drop shadow, each in a circular frame with label.

Character 1 — "Orchestrator" (오케스트레이터):
- Golden crown on head, royal purple cape, conducting pose with baton
- Gold and royal blue color scheme, confident authoritative expression
- Label: "orchestrator"

Character 2 — "Data Lead" (빅데이터팀 리드):
- Sleek blue-framed glasses, navy blue blazer with data chart pin
- Holding tablet showing graphs, analytical focused expression
- Label: "lead-data"

Character 3 — "Dev Lead" (개발팀 리드):
- Premium wireless headset (green LED), dark hoodie with circuit pattern
- Typing pose, determined sharp expression, green accent colors
- Label: "lead-dev"

Character 4 — "Design Lead" (디자인팀 리드):
- Purple artist beret tilted sideways, lilac blazer
- Holding color palette, creative cheerful expression, purple accent colors
- Label: "lead-pptx"

Layout: 4 characters in 2×2 grid, circular frames, white text labels.
1024×1024px high quality.
```

---

## IMAGE 2 — 빅데이터팀 A (6명)

```
Create a 3D chibi character sheet with 6 data analyst characters for a Korean AI agent dashboard.

Style: 3D chibi toon render, soft cel-shading, head:body ratio 1:1.2,
big expressive eyes, dark navy background, blue accent theme for data team,
clean studio lighting upper-left, slight drop shadow, each in a circular frame with label.

Character 1 — "Data Collector" (데이터 수집가):
- Brown detective hat, magnifying glass in hand, dark trench coat
- Curious investigative expression, warm brown tones
- Label: "data-collector"

Character 2 — "Data Cleaner" (데이터 정제사):
- White lab apron over casual outfit, holding cleaning spray bottle
- Focused tidy expression, clean white and light blue tones
- Label: "data-cleaner"

Character 3 — "EDA Analyst" (EDA 분석가):
- Oversized round glasses, casual blazer with scatter plot badge
- Thoughtful curious expression, looking slightly upward, teal accent
- Label: "eda-analyst"

Character 4 — "Statistician" (통계 전문가):
- Gold wire-rimmed glasses, dark academic vest, holding formula notepad
- Serious calculating expression, gold and navy tones
- Label: "statistician"

Character 5 — "ML Engineer" (ML 엔지니어):
- Blue baseball cap worn backwards, neural network hoodie
- Excited enthusiastic expression, electric blue accent colors
- Label: "ml-engineer"

Character 6 — "Deep Learning Engineer" (딥러닝 엔지니어):
- Cool dark sunglasses, dark tech jacket with brain circuit pattern
- Mysterious cool expression, deep purple and electric blue tones
- Label: "deep-learning"

Layout: 6 characters in 3×2 grid, circular frames, white text labels.
1024×768px high quality.
```

---

## IMAGE 3 — 빅데이터팀 B (5명)

```
Create a 3D chibi character sheet with 5 data specialist characters for a Korean AI agent dashboard.

Style: 3D chibi toon render, soft cel-shading, head:body ratio 1:1.2,
big expressive eyes, dark navy background, blue accent theme,
clean studio lighting upper-left, each in a circular frame with label.

Character 1 — "GIS Specialist" (GIS 전문가):
- Khaki field shirt with world map pattern, holding rolled map
- Adventurous exploring expression, earth tones (brown, green, tan)
- Label: "gis-specialist"

Character 2 — "Text Analyst" (텍스트 분석가):
- Pencil tucked behind ear, reading glasses on nose, book in arm
- Focused reading expression, warm amber and cream tones
- Label: "text-analyst"

Character 3 — "Visualizer" (시각화 전문가):
- Artist's color palette in hand, paint-splattered smock
- Creative excited expression, multi-color accent (rainbow highlights)
- Label: "visualizer"

Character 4 — "Reporter" (보고서 작성가):
- Blue necktie, crisp white dress shirt, holding printed report
- Professional composed expression, blue and white tones
- Label: "reporter"

Character 5 — "Realty Analyst" (부동산동향분석가):
- Red necktie, smart blazer, holding miniature house model
- Thoughtful analytical expression, warm skin tone (slightly tan),
  brown hair, orange-red accent colors
- Label: "realty-analyst"

Layout: 5 characters in row of 3 + row of 2 (centered), circular frames.
1024×640px high quality.
```

---

## IMAGE 4 — 웹앱팀 A (6명)

```
Create a 3D chibi character sheet with 6 web development characters for a Korean AI agent dashboard.

Style: 3D chibi toon render, soft cel-shading, head:body ratio 1:1.2,
big expressive eyes, dark navy background, green accent theme for dev team,
clean studio lighting upper-left, each in a circular frame with label.

Character 1 — "Requirements Analyst" (요구사항 분석가):
- Large clipboard held up with checklist, business casual outfit
- Methodical organized expression, gray and blue professional tones
- Label: "requirements"

Character 2 — "UX Designer" (UX 디자이너):
- Pink beret tilted on head, holding wireframe sketch pad
- Creative playful expression, pink and coral accent colors
- Label: "ux-designer"

Character 3 — "Frontend Developer" (프론트엔드):
- Green hoodie, laptop with UI components visible on screen
- Energetic enthusiastic expression, bright green and white tones
- Label: "frontend"

Character 4 — "Backend Developer" (백엔드):
- Black t-shirt with server rack badge/pin on chest, serious posture
- Calm efficient expression, dark gray and electric green tones
- Label: "backend"

Character 5 — "DBA" (데이터베이스 관리자):
- Red-framed glasses, dark vest, holding database cylinder icon
- Precise meticulous expression, red and dark navy tones
- Label: "dba"

Character 6 — "Security Expert" (보안 전문가):
- Black hoodie with hood up, shield badge on chest, crossed arms pose
- Vigilant mysterious expression, black and electric yellow tones
- Label: "security"

Layout: 6 characters in 3×2 grid, circular frames.
1024×768px high quality.
```

---

## IMAGE 5 — 웹앱팀 B (5명)

```
Create a 3D chibi character sheet with 5 software engineering characters for a Korean AI agent dashboard.

Style: 3D chibi toon render, soft cel-shading, head:body ratio 1:1.2,
big expressive eyes, dark navy background, green accent theme,
clean studio lighting upper-left, each in a circular frame with label.

Character 1 — "Unit Tester" (단위 테스터):
- White lab coat, holding checklist clipboard with red check marks
- Careful precise expression, white and red accent tones
- Label: "tester-unit"

Character 2 — "QA Tester" (QA 테스터):
- Green and black plaid vest, holding tablet running test suite
- Thorough bug-hunting expression, plaid pattern, dark green tones
- Label: "tester-qa"

Character 3 — "DevOps" (DevOps 엔지니어):
- Rocket ship enamel badge pinned to jacket, wearing headset
- Dynamic action-ready expression, orange and dark tones, rocket motif
- Label: "devops"

Character 4 — "Tech Writer" (기술 문서 작가):
- Brown rectangular glasses, smart cardigan, holding open notebook
- Thoughtful articulate expression, warm brown and cream tones
- Label: "tech-writer"

Character 5 — "StatWorkbench Developer" (SW 개발자):
- White lab coat with SPSS/statistics chart sleeve patch
- Focused analytical expression, white and deep blue tones, academic feel
- Label: "statworkbench"

Layout: 5 characters row of 3 + row of 2 (centered), circular frames.
1024×640px high quality.
```

---

## IMAGE 6 — 디자인팀 (5명)

```
Create a 3D chibi character sheet with 5 design team characters for a Korean AI agent dashboard.

Style: 3D chibi toon render, soft cel-shading, head:body ratio 1:1.2,
big expressive eyes, dark navy background, purple accent theme for design team,
clean studio lighting upper-left, each in a circular frame with label.

Character 1 — "PPTX Planner" (디자인 기획자):
- Colorful sticky notes (post-its) stuck all over outfit and nearby
- Planning thinking pose, hand on chin, warm yellow and purple tones
- Label: "pptx-planner"

Character 2 — "Content Writer" (콘텐츠 작성가):
- Large over-ear headphones (purple), typing on floating keyboard
- Creative flowing expression, purple and pink tones
- Label: "pptx-content"

Character 3 — "Slide Designer" (슬라이드 디자이너):
- Colorful fabric headband, artist smock, stylus pen in hand
- Aesthetic design-focused expression, vibrant multi-color palette
- Label: "pptx-designer"

Character 4 — "Design Builder" (디자인 빌더):
- Wrench tucked in pocket, construction vest over casual outfit
- Constructive builder expression, yellow and dark tones
- Label: "pptx-builder"

Character 5 — "Design Reviewer" (디자인 검토자):
- Laser pointer in hand, smart blazer, monocle-style single eyeglass
- Critical discerning review expression, silver and purple tones
- Label: "pptx-reviewer"

Layout: 5 characters row of 3 + row of 2 (centered), circular frames.
1024×640px high quality.
```

---

## 크롭 가이드

생성 후 각 이미지를 크롭하는 기준:
- 원형 프레임 기준으로 정사각형 크롭
- 저장: `assets/avatars/[id].png`
- 권장 크기: **256×256px** (레티나 디스플레이 대응)
- 현재 코드에서 `64px`로 렌더링되므로 256px이면 충분히 선명

### 크롭 후 적용 방법
```powershell
cd AGENTS_HOME
python assets/apply_all_avatars.py   # 이미 img 태그 방식이라 자동 반영
python scripts/build_html.py
python scripts/validate.py
git add -A && git commit -m "feat: 3D 치비 아바타 교체" && git push origin master
```

---

## 팁

- **일관성 유지**: 6장을 같은 ChatGPT 대화 세션에서 생성하면 스타일이 더 일치합니다
- **재생성 기준**: 얼굴이 뭉개지거나 라벨이 깨지면 해당 캐릭터만 단독으로 재요청
- **단독 요청 예시**: `"Regenerate only Character 3 (EDA Analyst) from the previous style, same circular frame format"`
- **배경 제거**: 필요하면 remove.bg 또는 Photoshop으로 원형 프레임 배경 제거 가능
