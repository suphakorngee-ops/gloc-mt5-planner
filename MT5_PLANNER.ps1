param(
    [ValidateSet("xau", "btc", "all")]
    [string]$Symbol = "btc",

    [ValidateSet("demo", "cent")]
    [string]$Account = "demo",

    [ValidateSet("live", "once", "report", "daily", "dashboard", "dashboard-open", "dashboard-live", "execution", "lock", "unlock", "manual-list", "backup", "save-state", "safe-automation", "discord-reply", "test-discord", "resend-latest", "track", "stats", "check", "backtest", "analyze")]
    [string]$Action = "live",

    [string]$Message = "/status"
)

$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\jiasny\Documents\New project 2"
$TerminalId = "D0E8209F77C8CF37AD8BF550E51FF075"
$Mt5FilesDir = "C:\Users\jiasny\AppData\Roaming\MetaQuotes\Terminal\$TerminalId\MQL5\Files"
$Python = "C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$DiscordSecret = Join-Path $ProjectDir "DISCORD_WEBHOOK.local.ps1"
if (Test-Path -LiteralPath $DiscordSecret) {
    . $DiscordSecret
}

$Profiles = @{
    xau = @{
        DemoConfig = "config.json"
        CentConfig = "config_xau_cent.json"
        Csv = "xauusdm_m5.csv"
        Backtest = "datasets/backtest_dataset.csv"
    }
    btc = @{
        DemoConfig = "config_btc.json"
        CentConfig = "config_btc_cent.json"
        Csv = "btcusdm_m5.csv"
        Backtest = "datasets/backtest_btc_dataset.csv"
    }
}

Set-Location $ProjectDir

if ($Symbol -eq "all") {
    switch ($Action) {
        "report" {
            Write-Host "===== BTC REPORT ====="
            & $Python -m mt5_planner forward-report --config config_btc.json --target 50
            Write-Host ""
            Write-Host "===== XAU REPORT ====="
            & $Python -m mt5_planner forward-report --config config.json --target 50
            exit
        }
        "daily" {
            & $Python -m mt5_planner daily-report --config config_btc.json --days 7 --output "reports\daily_btc.txt" --dated-output-dir "reports\daily"
            Write-Host ""
            & $Python -m mt5_planner daily-report --config config.json --days 7 --output "reports\daily_xau.txt" --dated-output-dir "reports\daily"
            exit
        }
        "dashboard" {
            & $Python -m mt5_planner dashboard --config config_btc.json --config config.json --output reports/dashboard.html
            exit
        }
        "dashboard-open" {
            & $Python -m mt5_planner dashboard --config config_btc.json --config config.json --output reports/dashboard.html
            Invoke-Item (Join-Path $ProjectDir "reports\dashboard.html")
            exit
        }
        "dashboard-live" {
            & $Python -m mt5_planner dashboard-serve --config config_btc.json --config config.json --host 127.0.0.1 --port 8765
            exit
        }
        "execution" {
            Write-Host "===== BTC EXECUTION ====="
            & $Python -m mt5_planner execution-status --config config_btc.json
            Write-Host ""
            Write-Host "===== XAU EXECUTION ====="
            & $Python -m mt5_planner execution-status --config config.json
            exit
        }
        "lock" {
            & $Python -m mt5_planner execution-lock --config config_btc.json --reason "manual all lock"
            & $Python -m mt5_planner execution-lock --config config.json --reason "manual all lock"
            exit
        }
        "unlock" {
            & $Python -m mt5_planner execution-unlock --config config_btc.json
            & $Python -m mt5_planner execution-unlock --config config.json
            exit
        }
        "backup" {
            & $Python -m mt5_planner backup --output-dir backups
            exit
        }
        "save-state" {
            & $Python -m mt5_planner save-state --config config_btc.json --config config.json --output PROJECT_STATE.md
            exit
        }
        "safe-automation" {
            & $Python -m mt5_planner safe-automation --config config_btc.json --config config.json --send-discord
            exit
        }
        "discord-reply" {
            & $Python -m mt5_planner discord-reply --config config_btc.json --config config.json --message $Message
            exit
        }
        "test-discord" {
            & $Python -m mt5_planner test-discord --config config_btc.json --message "Gloc test alert from MT5 Planner"
            exit
        }
        "resend-latest" {
            & $Python -m mt5_planner resend-latest --config config_btc.json
            exit
        }
        default {
            throw "Symbol all supports only report, daily, dashboard, dashboard-open, dashboard-live, execution, lock, unlock, backup, save-state, safe-automation, discord-reply, test-discord, resend-latest."
        }
    }
}

$Profile = $Profiles[$Symbol]
$Config = if ($Account -eq "cent") { $Profile.CentConfig } else { $Profile.DemoConfig }
$LocalCsv = Join-Path $ProjectDir $Profile.Csv
$Mt5Csv = Join-Path $Mt5FilesDir $Profile.Csv
$BacktestFile = $Profile.Backtest

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

function Sync-CsvIfExists {
    if (Test-Path -LiteralPath $Mt5Csv) {
        Copy-CsvWithRetry -Source $Mt5Csv -Destination $LocalCsv | Out-Null
    }
    elseif (-not (Test-Path -LiteralPath $LocalCsv)) {
        throw "CSV not found in MT5 or project folder: $Mt5Csv"
    }
}

switch ($Action) {
    "live" {
        while ($true) {
            Sync-CsvIfExists
            & $Python -m mt5_planner csv --config $Config --once
            Start-Sleep -Seconds 10
        }
    }
    "once" {
        Sync-CsvIfExists
        & $Python -m mt5_planner csv --config $Config --once --no-clear
    }
    "report" {
        & $Python -m mt5_planner forward-report --config $Config --target 50
    }
    "daily" {
        $DailyFile = "reports\daily_$Symbol.txt"
        & $Python -m mt5_planner daily-report --config $Config --days 7 --output $DailyFile --dated-output-dir "reports\daily"
    }
    "dashboard" {
        & $Python -m mt5_planner dashboard --config config_btc.json --config config.json --output reports/dashboard.html
    }
    "execution" {
        & $Python -m mt5_planner execution-status --config $Config
    }
    "lock" {
        & $Python -m mt5_planner execution-lock --config $Config --reason "manual lock"
    }
    "unlock" {
        & $Python -m mt5_planner execution-unlock --config $Config
    }
    "manual-list" {
        & $Python -m mt5_planner manual-list --config $Config --limit 30
    }
    "backup" {
        & $Python -m mt5_planner backup --output-dir backups
    }
    "save-state" {
        & $Python -m mt5_planner save-state --config $Config --output PROJECT_STATE.md
    }
    "safe-automation" {
        & $Python -m mt5_planner safe-automation --config $Config --send-discord
    }
    "discord-reply" {
        & $Python -m mt5_planner discord-reply --config $Config --message $Message
    }
    "test-discord" {
        & $Python -m mt5_planner test-discord --config $Config --message "Gloc test alert from MT5 Planner"
    }
    "resend-latest" {
        & $Python -m mt5_planner resend-latest --config $Config
    }
    "track" {
        Sync-CsvIfExists
        & $Python -m mt5_planner track --config $Config
    }
    "stats" {
        & $Python -m mt5_planner stats --config $Config
    }
    "check" {
        Sync-CsvIfExists
        & $Python -m mt5_planner check-csv --config $Config
    }
    "backtest" {
        Sync-CsvIfExists
        & $Python -m mt5_planner backtest --config $Config --output $BacktestFile
    }
    "analyze" {
        & $Python -m mt5_planner analyze-backtest --input $BacktestFile
    }
}
