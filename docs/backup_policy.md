# 백업 정책

> 본 레포의 백업 전략과 보존 규칙을 명시한다. 모든 PC에서 동일하게 적용.

## 1. 백업 위치

| 종류 | 위치 | git 추적 |
|---|---|---|
| 일시 작업 백업 | `_backup/YYYY-MM-DD_{작업명}/` | 아니오 (.gitignore) |
| 영구 양식 보관 | `docs/analysis-templates/` | 예 |
| 표본 보고서 | `docs/analysis-templates/samples/` | 예 |

## 2. 백업 시기

다음 작업 직전에는 반드시 `_backup/` 에 사본 보관:
- `role.md` 또는 `memory.md` 대규모 재작성
- 양식 명세(`docs/analysis-templates/`) 변경
- 보고서 작성 스크립트 (build_report*.py 등) 구조 변경
- 다른 PC와 충돌 가능성이 큰 머지 직전

## 3. 백업 명명 규칙

```
_backup/{YYYY-MM-DD}_{작업명}/{원래파일경로}.bak
```

예시:
- `_backup/2026-05-22_reporter_realty_split/reporter_role.md.bak`
- `_backup/2026-05-23_memory_split/realty-analyst_memory.md.bak`

## 4. 백업 보존 기간

- **로컬 보관**: 작업 PC에 무기한 보존 (사용자 판단)
- **git 미추적**: `_backup/`는 .gitignore — 다른 PC와 자동 동기화 안 됨
- 사용자가 명시적으로 백업을 git에 포함하려면 `git add -f _backup/{경로}` 명령 사용 필요

## 5. 영구 보관용 백업 (특수 케이스)

특정 보고서·산출물을 영구 보관해야 할 경우:
- `docs/archive/{YYYYMM}_{설명}/` 폴더 사용 (git 추적됨)
- `_backup/`이 아님 — `_backup/`은 일시 작업 보호용

## 6. 백업 복원

```bash
cp _backup/2026-05-22_reporter_realty_split/reporter_role.md.bak \
   agents/reporter/role.md
```

복원 후 반드시 `scripts/sync.py` 재실행으로 MD_CONTENT 갱신.

## 7. 정책 위반 사례 (피해야 할 패턴)

- 백업 없이 200줄 이상 파일 재작성 (금지)
- `_backup/` 폴더를 직접 삭제 (`rm -rf _backup/`) — 다른 PC에 백업이 없을 수 있음 (금지)
- 영구 보관용을 `_backup/`에 두기 (시간 지나면 잊히고 git에도 없어 손실 위험) (금지)
- 영구 보관은 `docs/archive/`, 일시 작업 백업은 `_backup/` (권장)

---

## 한자·일본어 절대 금지
본 정책 문서를 포함하여 모든 레포 파일은 순한글 작성.
