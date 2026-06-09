---
name: chart_style_rules
description: 시각화 차트 스타일 규칙 (제목 금지, 폰트 크기)
type: feedback
---

차트 제목(ax.set_title)을 절대 사용하지 말 것. 폰트 사이즈는 크게 유지할 것.

**Why:** 사용자가 여러 번 강조한 규칙. 나중에 수정 편의성을 위해 제목 없이 축 레이블과 범례만으로 차트 내용을 설명.

**How to apply:** analyze_youth.py 등 시각화 코드 작성 시 ax.set_title() 호출 금지. 축 레이블(xlabel, ylabel), 범례(legend), 주석(annotate)으로 대신 설명. 폰트 크기는 xlabel/ylabel 22+, tick 18+, legend 17+ 유지.
