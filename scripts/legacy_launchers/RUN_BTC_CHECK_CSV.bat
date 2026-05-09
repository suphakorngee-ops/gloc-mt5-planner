@echo off
cd /d "C:\Users\jiasny\Documents\New project 2"
copy /Y "C:\Users\jiasny\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\btcusdm_m5.csv" "C:\Users\jiasny\Documents\New project 2\btcusdm_m5.csv"
"C:\Users\jiasny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m mt5_planner check-csv --config config_btc.json
pause
