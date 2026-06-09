---
type: moc
domain: agents시스템
tags: [moc]
---

# agents시스템 — 지도(MoC)

> 이 도메인 지식 노트의 허브. 새 노트는 아래에 `[[링크]]`로 등록한다.

- [[feedback-agents-always]] — OC→리드→담당(지시) / 담당→리드→OC(검토) 수직 계열화 필수. 건너뛰기 금지. 담당 없으면 즉시 중단 후 생성 여부 문의 (2026-05-21)
- [[feedback-cc-changes-to-index]] — 스킬·훅·규칙 등 Claude Code 변경 시 build_html.py 실행 후 즉시 index.html 반영·push 필수 (2026-05-21)
- [[feedback-ci-dependency-version-safety]] — Python 패키지 푸시 전 미선언 의존성 감사 + 버전 취약 테스트(라이브러리 내부 직접 패치) 회피, 로컬 통과만 믿지 말 것
- [[feedback-cp949-console-guard]] — 이모지·한글 print하는 Windows CLI는 sys.stdout.reconfigure(utf-8) 가드 필수, PYTHONIOENCODING=cp949로 검증
- [[feedback-html-build-safety]] — .md 내용을 HTML script 블록에 삽입 시 </  이스케이프·BOM 제거·Node.js 구문 검증·Playwright 확인 4단계 필수
- [[feedback-sync-after-memory-update]] — agents memory.md 수정 시 반드시 python scripts/sync.py 실행 후 push (누락 시 대시보드 MD 에디터 "(내용 없음)")
- [[project-agents-improvements]] — 메타버스·대시보드·인프라 완료 항목, 재제안 금지 (2026-05-26)
