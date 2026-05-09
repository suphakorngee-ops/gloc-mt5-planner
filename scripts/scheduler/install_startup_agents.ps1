$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\jiasny\Documents\New project 2"
$Runner = Join-Path $ProjectDir "scripts\scheduler\run_agent_loop.ps1"
$StartupDir = [Environment]::GetFolderPath("Startup")

function Write-StartupAgent {
    param(
        [string]$Name,
        [string]$Agent,
        [int]$IntervalSeconds
    )

    $Path = Join-Path $StartupDir "$Name.vbs"
    $Command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$Runner"" -Agent $Agent -IntervalSeconds $IntervalSeconds"
    $Content = @"
Set shell = CreateObject("WScript.Shell")
shell.Run "$Command", 0, False
"@
    $Content | Out-File -FilePath $Path -Encoding ascii -Force
    Write-Host "installed startup agent: $Path"
}

Write-StartupAgent -Name "Gloc-Rloc-Loop" -Agent "rloc" -IntervalSeconds 30
Write-StartupAgent -Name "Gloc-Oloc-Loop" -Agent "oloc" -IntervalSeconds 60

Write-Host ""
Write-Host "Done. These agents start hidden when this Windows user logs in."
Write-Host "Startup folder: $StartupDir"
Write-Host "Logs: $ProjectDir\agents\gloc\logs\scheduler"
Write-Host "Auto execution remains OFF."
