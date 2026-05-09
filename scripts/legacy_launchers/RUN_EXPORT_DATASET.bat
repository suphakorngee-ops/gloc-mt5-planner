@echo off
cd /d "C:\Users\jiasny\Documents\New project 2"
"C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m mt5_planner export --config config.json --output datasets/signals_dataset.csv
pause
