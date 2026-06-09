---
name: reference-agents-repo
description: "멀티에이전트 레포 위치, git 설정, 동기화 규칙"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c951dd33-60b9-4259-8742-36ddb86661b5
---

## 레포 정보
- GitHub: https://github.com/your-github-username/agent (master 브랜치)
- 로컬 경로: `D:/업무/agents`
- git user.email: your-email@example.com (이 레포 전용 설정)
- config.local.json: 로컬 전용, git 제외됨

## 동기화 규칙 (SYNC_GUIDE.md 요약)
- 작업 시작 전: `git pull origin master`
- 작업 완료 후: `git add → commit → push`
- config.local.json 절대 push 금지
- memory.md 삭제 금지, 내용 병합 원칙

## 이 PC 역할 (사무실-데스크탑)
- role.md 수정 담당
- memory.md 작성 담당
