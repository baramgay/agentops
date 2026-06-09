# sync_repo_skills.ps1
# 레포의 skills/ 폴더를 ~/.claude/skills/에 동기화
# 사용법: powershell -ExecutionPolicy Bypass -File scripts/sync_repo_skills.ps1

$ErrorActionPreference = "Stop"

$RepoRoot   = Split-Path $PSScriptRoot -Parent
$RepoSkills = Join-Path $RepoRoot "skills"
$LocalSkills = Join-Path $env:USERPROFILE ".claude\skills"

if (-not (Test-Path $RepoSkills)) {
    Write-Host "[WARN] 레포 skills/ 폴더 없음: $RepoSkills"
    exit 0
}

if (-not (Test-Path $LocalSkills)) {
    New-Item -ItemType Directory -Force $LocalSkills | Out-Null
}

$skills = Get-ChildItem -Path $RepoSkills -Directory
$synced = 0
$updated = 0

foreach ($skill in $skills) {
    $skillMd = Join-Path $skill.FullName "SKILL.md"
    if (-not (Test-Path $skillMd)) { continue }

    $dest = Join-Path $LocalSkills $skill.Name
    $destMd = Join-Path $dest "SKILL.md"

    if (-not (Test-Path $dest)) {
        New-Item -ItemType Directory -Force $dest | Out-Null
    }

    # 내용이 다를 때만 복사
    $needsCopy = $true
    if (Test-Path $destMd) {
        $srcHash  = (Get-FileHash $skillMd  -Algorithm MD5).Hash
        $dstHash  = (Get-FileHash $destMd   -Algorithm MD5).Hash
        if ($srcHash -eq $dstHash) { $needsCopy = $false }
    }

    if ($needsCopy) {
        Copy-Item -Path $skillMd -Destination $destMd -Force
        Write-Host "[SYNC] $($skill.Name) → $destMd"
        $updated++
    } else {
        Write-Host "[ OK] $($skill.Name) (최신)"
    }
    $synced++
}

Write-Host ""
Write-Host "레포 스킬 동기화 완료: $synced 개 확인, $updated 개 갱신"
Write-Host "경로: $LocalSkills"
