---
name: method-multi-pc-knowledge-sync
type: method
domain: agents시스템
updated: 2026-06-07
tags: [multi-pc, sync, hook, wiki]
---

# 다중 PC 지식 자동 공유 방법

**결론**: 한 사람이 여러 PC를 번갈아 쓸 때, 위키 지식을 **이벤트 기반 훅**으로 자동 공유한다. SessionStart=pull(다른 PC 지식 받기) / SessionEnd=capture+push(내 지식 공유) / PreCompact=capture(압축 전 저장).

## 이유
- 30분 폴링 데몬보다 세션 경계 동기화가 순차 사용 패턴에 더 신선·효율적.
- 지식 파일(wiki·memory·role)만 자동 커밋 → 코드 WIP는 안 건드림.

## 적용법
- 새 PC 1회: `git clone <repo> <원하는경로>` → `git pull` → `python scripts/install_sync_hooks.py`
- 설치기는 `__file__`·`sys.executable`로 **그 PC의 실제 경로를 자동 인식** → PC마다 경로 달라도 OK
- 재실행하면 경로 자동 교정(멱등, 우리 훅만 제거 후 재주입, 타 훅 보존)

## 함정 (반드시 같이 볼 것)
- **settings.json은 sync 제외(SKIP_NAMES)** = 머신별 → git으로 안 퍼짐 → PC마다 install_sync_hooks 1회 필수
- 훅에서 git/stdin 멈춤 → [[feedback-claude-hook-git-hang]] (detach + GIT_TERMINAL_PROMPT=0)
- 세션노트는 **PC별 파일명**(`세션-날짜-PC.md`)으로 git 충돌 원천 차단
- 관련: [[reference-llm-wiki-architecture]]
