# FastAPI 서버를 Windows 로그인 시 자동 시작으로 등록
# 실행: powershell -ExecutionPolicy Bypass -File scripts\register_api_startup.ps1

$taskName  = "AgentAPIServer"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent $scriptDir
$batFile   = Join-Path $scriptDir "start_api.bat"

# 기존 태스크 제거
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batFile`"" -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings= New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "에이전트 FastAPI WebSocket 서버 자동 시작" | Out-Null

Write-Host "등록 완료: '$taskName'"
Write-Host "  실행 파일: $batFile"
Write-Host "  트리거: 로그인 시 자동 시작"
Write-Host ""
Write-Host "제거하려면: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
