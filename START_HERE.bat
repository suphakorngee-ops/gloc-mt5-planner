@echo off
title MT5 Planner Main Menu
cd /d "C:\Users\jiasny\Documents\New project 2"

:menu
cls
echo ==================================================
echo MT5 Planner - Main Menu
echo ==================================================
echo.
echo BTCUSDm - use while XAU market is closed
echo 1. BTC Live
echo 2. BTC Run Once
echo 3. BTC Forward Report
echo 4. BTC Daily Summary
echo 5. BTC Track Results
echo 6. BTC Backtest
echo 7. BTC Analyze Backtest
echo.
echo XAUUSDm - use when gold market is open
echo 11. XAU Live
echo 12. XAU Run Once
echo 13. XAU Forward Report
echo 14. XAU Daily Summary
echo 15. XAU Track Results
echo 16. XAU Backtest
echo 17. XAU Analyze Backtest
echo.
echo Tools
echo 21. Open VSCode
echo 22. Open Project Folder
echo 0. Exit
echo ==================================================
set /p choice=Choose: 

if "%choice%"=="1" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action live
if "%choice%"=="2" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action once
if "%choice%"=="3" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action report
if "%choice%"=="4" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action daily
if "%choice%"=="5" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action track
if "%choice%"=="6" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action backtest
if "%choice%"=="7" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action analyze

if "%choice%"=="11" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action live
if "%choice%"=="12" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action once
if "%choice%"=="13" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action report
if "%choice%"=="14" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action daily
if "%choice%"=="15" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action track
if "%choice%"=="16" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action backtest
if "%choice%"=="17" powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action analyze

if "%choice%"=="21" code "C:\Users\jiasny\Documents\New project 2"
if "%choice%"=="22" explorer "C:\Users\jiasny\Documents\New project 2"
if "%choice%"=="0" exit

pause
goto menu
