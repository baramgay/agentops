# 에이전트 공유 스킬 저장소

이 폴더는 에이전트 시스템 전용 스킬을 Git으로 관리하여 **모든 PC에서 동일한 스킬을 사용**할 수 있도록 한다.

## 구조

```
skills/
  {skill-name}/
    SKILL.md        ← Claude Code 스킬 정의 (필수)
    README.md       ← 스킬 설명 (선택)
```

## PC 간 스킬 동기화

```powershell
# 레포 pull 후 실행 — 레포 스킬을 ~/.claude/skills/에 복사
powershell -ExecutionPolicy Bypass -File scripts/sync_repo_skills.ps1

# 또는 pull + 스킬 동기화 한 번에
cd AGENTS_HOME
git pull origin master
powershell -ExecutionPolicy Bypass -File scripts/sync_repo_skills.ps1
```

## 스킬 목록

| 스킬 | 담당 에이전트 | 설명 |
|------|------------|------|
| `realty-pipeline` | realty-analyst | 경남 부동산 동향 월보 6단계 파이프라인 |
| `bigdata-analysis-report` | reporter | 빅데이터 분석 보고서 7블록 양식 (표지→요약→Ⅰ~Ⅴ) |

## 새 스킬 추가 절차

1. `skills/{skill-name}/SKILL.md` 작성 (SKILL.md 형식 준수)
2. `git add -A && git commit && git push`
3. 다른 PC에서 `git pull` 후 `sync_repo_skills.ps1` 실행
