---
name: method-harness-engineering-impl
type: method
domain: agents시스템
updated: 2026-06-08
---

결론: Harness Engineering은 말로 하는 규칙이 아니라 코드로 강제하는 환경이다. agent_guard + verify_tool + precompact_wiki_guide 3개 훅이 핵심 구현체.

**Why:** "규칙 지켜라" 메시지는 세션 간 휘발된다. 훅(exit 2 차단)은 세션이 바뀌어도 물리적으로 작동한다.

**How to apply:**
- `agent_guard.py` (PreToolUse Write|Edit): agent_status.json에 working 에이전트 없으면 exit 2로 파일 수정 자체 차단. STALE_MINUTES=120으로 2시간 이상 된 working은 무효 처리.
- `verify_tool.py` (PostToolUse Bash): exit code 2 이상 실패 시 stderr 경고 주입. git exit 1, echo/ls/cat 등 노이즈성 명령 제외.
- `precompact_wiki_guide.py` (PreCompact): 압축 LLM 컨텍스트에 직접 주입. "Write 도구로 wiki 파일 직접 저장 후 압축 요약 작성"을 지시. 기존 슬러그 목록 + 도메인 감지 포함.
- `distill_nudge.py` (UserPromptSubmit): 2MB 임계값 초과 시 `/지식저장` 실행 지시 주입.
- 모두 `settings.json` hooks에 등록.

**예외 경로 (agent_guard)**:
- wiki/notes/, agent_status.json, logs/, sessions/, .claude/memory/ → 항상 허용(선언 없이도 가능)
