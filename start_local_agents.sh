#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
cd "$(dirname "$0")"

case "$ACTION" in
  status)
    python -m mt5_planner agent-status
    ;;
  enqueue-report)
    python -m mt5_planner agent-enqueue --agent rloc --action report --note "manual local report"
    ;;
  run-rloc)
    python -m mt5_planner agent-run-once --agent rloc --config config_btc.json --config config.json
    ;;
  run-oloc)
    python -m mt5_planner agent-run-once --agent oloc --config config_btc.json --config config.json
    ;;
  loop-rloc)
    python -m mt5_planner agent-run-loop --agent rloc --config config_btc.json --config config.json --interval 30
    ;;
  loop-oloc)
    python -m mt5_planner agent-run-loop --agent oloc --config config_btc.json --config config.json --interval 60
    ;;
  *)
    echo "usage: ./start_local_agents.sh [status|enqueue-report|run-rloc|run-oloc|loop-rloc|loop-oloc]"
    exit 1
    ;;
esac
