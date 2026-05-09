$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\jiasny\Documents\New project 2"
$Runner = Join-Path $ProjectDir "scripts\scheduler\run_agent_loop.ps1"
$PowerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function Register-GlocTask {
    param(
        [string]$TaskName,
        [string]$Agent,
        [int]$IntervalSeconds
    )

    $ActionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" -Agent $Agent -IntervalSeconds $IntervalSeconds"
    $Action = New-ScheduledTaskAction -Execute $PowerShell -Argument $ActionArgs -WorkingDirectory $ProjectDir
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Gloc local agent worker loop: $Agent" `
        -Force | Out-Null

    Write-Host "registered: $TaskName"
}

Register-GlocTask -TaskName "Gloc Rloc Loop" -Agent "rloc" -IntervalSeconds 30
Register-GlocTask -TaskName "Gloc Oloc Loop" -Agent "oloc" -IntervalSeconds 60

Write-Host ""
Write-Host "Done. These tasks start when the current Windows user logs in."
Write-Host "Logs: $ProjectDir\agents\gloc\logs\scheduler"
Write-Host "Auto execution remains OFF."
