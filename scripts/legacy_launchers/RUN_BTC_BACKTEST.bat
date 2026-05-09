@echo off
cd /d "C:\Users\jiasny\Documents\New project 2"
"C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m mt5_planner backtest --config config_btc.json --output datasets/backtest_btc_dataset.csv
pause
