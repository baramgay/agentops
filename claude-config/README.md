# Claude 설정 동기화

이 디렉토리는 .claude/ 설정을 GitHub을 통해 3대 PC 간 동기화하기 위한 것입니다.

## 구조
- `CLAUDE.md` - 전역 .claude/CLAUDE.md 동기화용
- `memory/` - 프로젝트별 memory 파일
- `skills/` - 커스텀 스킬 (서드파티 제외)

## 사용법
```bash
# 현재 PC의 .claude/ 내용을 여기로 내보내기
python scripts/sync_claude_config.py export

# GitHub에서 pull 후 .claude/에 적용
python scripts/sync_claude_config.py import
```

## 주의사항
- API 키, 토큰 등 민감정보는 절대 포함하지 않음
- .claude/settings.json은 머신별 설정이므로 동기화 대상 아님
- import 시 기존 파일 백업 후 덮어쓰기
