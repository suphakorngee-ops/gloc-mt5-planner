$ErrorActionPreference = "Stop"
$ProjectDir = "C:\Users\jiasny\Documents\New project 2"
$Python = "C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$DiscordSecret = Join-Path $ProjectDir "DISCORD_WEBHOOK.local.ps1"

Set-Location $ProjectDir
if (Test-Path -LiteralPath $DiscordSecret) {
    . $DiscordSecret
}

& $Python -m mt5_planner.discord_service
