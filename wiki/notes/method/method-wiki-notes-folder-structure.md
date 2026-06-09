---
name: method-wiki-notes-folder-structure
type: method
domain: agents시스템
updated: 2026-06-08
---
결론: wiki/notes/ 를 type 기반 하위 폴더(feedback/, project/, reference/, method/, agents/, sessions/)로 분리하면 Obsidian 탐색성과 스크립트 일관성이 동시에 향상된다.

**Why:** 121개 파일이 flat 구조에 몰려 있어 Obsidian에서 유형별 탐색이 불가능했고, agents/ 내 memory 파일 경로를 스크립트가 하드코딩해 불일치가 발생함.

**How to apply:**
- 신규 노트 생성 시 반드시 `notes/<type>/` 하위 저장 (루트에 직접 생성 금지)
- 스크립트는 `glob("*.md")` 대신 `rglob("*.md")` 사용 (token_health.py, precompact_wiki_guide.py, api_server.py 등 이미 적용됨)
- Obsidian `[[wikilink]]`는 폴더 이동 후에도 단일 파일명이 고유하면 자동 해결 → MoC 링크 재작성 불필요
- `귀촌지.md` 같이 type=moc 파일은 `wiki/MoC/`로 이동 (notes 하위가 아님)
