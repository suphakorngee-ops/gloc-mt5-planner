param(
    [ValidateSet("rloc", "oloc")]
    [string]$Agent = "rloc",

    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Stop"
$ProjectDir = "C:\Users\jiasny\Documents\New project 2"
$Python = "C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$LogDir = Join-Path $ProjectDir "agents\gloc\logs\scheduler"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectDir

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "$Stamp-$Agent-loop.log"

"[$(Get-Date -Format o)] starting $Agent loop interval=$IntervalSeconds" | Out-File -FilePath $LogFile -Encoding utf8 -Append

try {
    & $Python -m mt5_planner agent-run-loop --agent $Agent --config config_btc.json --config config.json --interval $IntervalSeconds *>> $LogFile
}
catch {
    "[$(Get-Date -Format o)] ERROR: $($_.Exception.Message)" | Out-File -FilePath $LogFile -Encoding utf8 -Append
    throw
}
