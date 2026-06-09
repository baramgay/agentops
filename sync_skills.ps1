# sync_skills.ps1 — union.json 기준으로 이 PC의 스킬을 동기화
#
# 사용법:
#   .\sync_skills.ps1           # 누락 스킬 목록 조회 (설치 안 함)
#   .\sync_skills.ps1 --install # 누락 스킬을 archive에서 복원
#   .\sync_skills.ps1 --show    # union 전체 목록 출력
#
# 사전 조건: git pull 후 cc_status/union.json 이 최신 상태여야 합니다.

param(
    [switch]$install,
    [switch]$show
)

$repoRoot    = $PSScriptRoot
$unionPath   = Join-Path $repoRoot "cc_status\union.json"
$skillsDir   = "$env:USERPROFILE\.claude\skills"
$archiveDir  = "$env:USERPROFILE\.claude\skills_archived"

if (-not (Test-Path $unionPath)) {
    Write-Host "union.json 이 없습니다. 먼저 merge_skills.py 를 실행하거나 git pull 하세요." -ForegroundColor Red
    exit 1
}

$union       = Get-Content $unionPath -Raw | ConvertFrom-Json
$unionSkills = $union.union_skills
$installed   = if (Test-Path $skillsDir) {
    Get-ChildItem $skillsDir -Directory | Select-Object -ExpandProperty Name
} else { @() }

$missing = $unionSkills | Where-Object { $_ -notin $installed }
$extra   = $installed   | Where-Object { $_ -notin $unionSkills }

if ($show) {
    Write-Host "=== union.json 스킬 목록 (합집합 $($unionSkills.Count)개) ===" -ForegroundColor Cyan
    foreach ($m in $union.machines) {
        Write-Host "  $($m.hostname): $($m.skill_count)개  (보고: $($m.reported_at))"
    }
    Write-Host ""
    foreach ($s in $union.skill_presence.PSObject.Properties) {
        $hosts = $s.Value -join ", "
        Write-Host "  $($s.Name.PadRight(40)) $hosts"
    }
    exit
}

Write-Host "=== 이 PC: $env:COMPUTERNAME ===" -ForegroundColor Cyan
Write-Host "설치됨:  $($installed.Count)개"
Write-Host "합집합:  $($unionSkills.Count)개"
Write-Host ""

if ($missing.Count -eq 0) {
    Write-Host "누락 스킬 없음 — 합집합과 일치합니다." -ForegroundColor Green
} else {
    Write-Host "합집합에 있지만 미설치 ($($missing.Count)개):" -ForegroundColor Yellow
    foreach ($s in $missing) {
        $inArchive = Test-Path (Join-Path $archiveDir $s)
        $tag = if ($inArchive) { "[아카이브]" } else { "[미보유]" }
        Write-Host "  $tag $s"
    }
}

if ($extra.Count -gt 0) {
    Write-Host ""
    Write-Host "이 PC에만 있는 스킬 ($($extra.Count)개) — 합집합에 없음:" -ForegroundColor DarkYellow
    foreach ($s in $extra) { Write-Host "  $s" }
}

if ($install) {
    Write-Host ""
    if ($missing.Count -eq 0) {
        Write-Host "복원할 스킬이 없습니다." -ForegroundColor Green
        exit
    }
    $restored = 0; $skipped = 0
    foreach ($s in $missing) {
        $src = Join-Path $archiveDir $s
        $dst = Join-Path $skillsDir  $s
        if (Test-Path $src) {
            Move-Item $src $dst -Force
            Write-Host "  복원: $s" -ForegroundColor Green
            $restored++
        } else {
            Write-Host "  건너뜀 (아카이브 없음): $s" -ForegroundColor DarkGray
            $skipped++
        }
    }
    Write-Host ""
    Write-Host "복원 $restored개 완료  |  건너뜀 $skipped개 (Claude Code에서 재설치 필요)" -ForegroundColor Cyan
}
