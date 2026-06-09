---
name: reference-llm-wiki-architecture
type: reference
domain: agents시스템
updated: 2026-06-07
tags: [wiki, architecture]
---

# LLM 위키 아키텍처 (knowledge base)

**결론**: 업무 지식은 `AGENTS_HOME\wiki`(옵시디언 Vault) 단일 진실 소스에 마크다운+`[[링크]]`로 큐레이션한다. RAG(원문 chunk 검색)가 아니라 **MoC 인덱스 → 링크 탐색**으로 활용.

## 구조
- `00_홈.md` 진입 허브 / `MoC/<도메인>.md` 도메인 지도 / `notes/<슬러그>.md` 원자적 노트
- 에이전트 지식: `notes/agent-<id>-role.md`(미러) + `agent-<id>-memory.md`(위키가 정본)
- 자동 생성: `notes/sessions/`(세션캡처) `notes/projects/`(PRJ) `notes/issues/`(완료이슈) `notes/reports/`(보고서)
- 위키는 `agents` 레포 안에 있어 git으로 같이 동기화됨

## 이유
- 증류된 노트 > chunk 검색. 구조·링크·중복제거로 복리 누적. git 버전관리로 감사 가능.
- 메모리 포맷(frontmatter+`[[링크]]`)이 옵시디언과 동일 → 그대로 호환.

## 적용법
- 작업 시작: 해당 MoC 먼저 읽기(`wiki/_tools/wiki_read.py <도메인>`), Vault 전체 로드 금지
- 작업 끝: 결론·이유·적용법으로 증류해 노트 저장, MoC에 링크
- 메모리→Vault: `wiki/_tools/bootstrap_from_memory.py` (매니페스트 기반 멱등, rmtree 금지)
- 관련: [[method-multi-pc-knowledge-sync]] · [[feedback-claude-hook-git-hang]]
