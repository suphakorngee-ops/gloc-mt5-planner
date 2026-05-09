$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\jiasny\Documents\New project 2"
$Mt5Csv = "C:\Users\jiasny\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\xauusdm_m5.csv"
$LocalCsv = Join-Path $ProjectDir "xauusdm_m5.csv"
$Python = "C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectDir

function Copy-CsvWithRetry {
    param(
        [string]$Source,
        [string]$Destination
    )

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Copy-Item -LiteralPath $Source -Destination $Destination -Force
            return $true
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    Write-Host "CSV busy, using last local copy for this cycle."
    return $false
}

while ($true) {
    Copy-CsvWithRetry -Source $Mt5Csv -Destination $LocalCsv | Out-Null
    & $Python -m mt5_planner csv --config config.json --once
    Start-Sleep -Seconds 10
}
