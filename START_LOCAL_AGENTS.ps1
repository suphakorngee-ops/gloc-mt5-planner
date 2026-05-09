param(
    [ValidateSet("status", "enqueue-report", "run-rloc", "run-oloc", "loop-rloc", "loop-oloc")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"
$ProjectDir = "C:\Users\jiasny\Documents\New project 2"
$Python = "C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $ProjectDir

switch ($Action) {
    "status" {
        & $Python -m mt5_planner agent-status
    }
    "enqueue-report" {
        & $Python -m mt5_planner agent-enqueue --agent rloc --action report --note "manual local report"
    }
    "run-rloc" {
        & $Python -m mt5_planner agent-run-once --agent rloc --config config_btc.json --config config.json
    }
    "run-oloc" {
        & $Python -m mt5_planner agent-run-once --agent oloc --config config_btc.json --config config.json
    }
    "loop-rloc" {
        & $Python -m mt5_planner agent-run-loop --agent rloc --config config_btc.json --config config.json --interval 30
    }
    "loop-oloc" {
        & $Python -m mt5_planner agent-run-loop --agent oloc --config config_btc.json --config config.json --interval 60
    }
}
