# MT5 Planner Project State

saved_at: 2026-05-11T00:19:23

## Current Mode

- Forward tracking remains enabled
- BTC demo auto execution may be ON if `config_btc.json` says enabled
- XAU demo auto execution may be ON if `config.json` says enabled
- BTC and XAU each use independent max_open_trades per symbol
- Fixed lot 0.01
- Clean current journals

## BTCUSDm M5

- config: config_btc.json
- journal: journal_btc_current.sqlite
- csv: btcusdm_m5.csv
- fixed_lot: 0.01
- execution_enabled: True

```text
FORWARD TEST REPORT
========================================================================
start_at: 2026-05-09T00:00:00+00:00
STRATEGY / PAPER IDEAS
------------------------------------------------------------------------
raw signals: 40
grouped trade ideas: 12 from 40 raw signals | wins 10 | losses 1 | open 1 | timeout 0 | closed WR 90.9%
raw signals: wins 32 | losses 7 | open 1 | timeout 0 | be 0
closed win rate: 82.1%
expectancy: 0.850R/signal | profit factor: 5.86
avg win: 1.28R | avg loss: -1.00R | avg $risk: 2.34
progress: 40/50 (10 left) | 40/100 (60 left)
decision: WAIT - collect at least 50 forward signals

VLOC / ACTUAL MT5 ORDERS
------------------------------------------------------------------------
execution: DEMO AUTO ON | max_open_trades 1 | paper ideas do not all become orders
execution log: sent 2 | blocked/rejected 4
MT5 today/history: closed deals 1 | closed P/L $3.03 | open positions 1

SESSION
session          win    sl   open  timeout       wr
London/NY         26     7      0        0    78.8%
NY                 6     0      1        0   100.0%

MODE
mode             win    sl   open  timeout       wr
safe              32     7      1        0    82.1%

RECENT
created_at                   side   status        entry         sl         tp
2026-05-09T15:42:50.735949+00:00 long   tp        80497.487  80218.230  80916.373
2026-05-09T15:43:25.864966+00:00 long   tp        80424.474  80218.230  80733.840
2026-05-09T15:50:21.884131+00:00 long   tp        80506.164  80218.230  80938.065
2026-05-09T17:05:55.007147+00:00 long   tp1       80701.242  80401.450  81105.962
2026-05-10T15:05:13.582242+00:00 long   tp1       81021.104  80803.050  81348.186
2026-05-10T15:05:27.744869+00:00 long   tp1       81029.412  80803.050  81368.956
2026-05-10T15:05:51.690541+00:00 long   tp1       81040.452  80803.050  81396.556
2026-05-10T15:41:38.235625+00:00 long   tp1       81103.797  80803.050  81554.917
2026-05-10T15:44:58.420489+00:00 long   tp1       81100.665  80803.050  81547.087
2026-05-10T17:05:12.426597+00:00 long   open      81362.089  80938.720  81933.638
```

```text
DAILY FORWARD SUMMARY
============================================================================
timezone: Asia/Bangkok | days: 7
start_at: 2026-05-09T00:00:00+00:00

date         signals   win    sl   open  timeout       wr     expR      pf
2026-05-05         0     0     0      0        0     0.0%    0.000    0.00
2026-05-06         0     0     0      0        0     0.0%    0.000    0.00
2026-05-07         0     0     0      0        0     0.0%    0.000    0.00
2026-05-08         0     0     0      0        0     0.0%    0.000    0.00
2026-05-09        28    21     7      0        0    75.0%    0.875    4.50
2026-05-10        11    11     0      0        0   100.0%    0.864    0.00
2026-05-11         1     0     0      1        0     0.0%    0.000    0.00

TOTAL
signals 40 | win 32 | sl 7 | open 1 | timeout 0 | wr 82.1% | expectancy 0.850R | PF 5.86

NEXT
- keep collecting until 50-100 current-logic forward signals
- keep execution state as configured: BTC demo auto guarded, XAU off unless explicitly changed
```

```text
ACTUAL MT5 ORDER LEDGER
========================================================================
symbol: BTCUSDm | ledger: orders_btcusdm_current.sqlite
start_at: 2026-05-09T00:00:00+00:00
orders: 2 | closed 1 | open 1 | wins 1 | losses 0 | be 0 | WR 100.0%
closed P/L: $3.03 | open P/L: $-0.69 | marked total: $2.34
gross win $3.03 | gross loss $0.00 | PF inf

RECENT MT5 ORDERS
    position side  status     vol      entry         sl         tp       p/l
  1917700232 BUY   closed    0.01  81045.020      0.000      0.000      3.03
  1917830363 BUY   open      0.01  81398.530  80938.720  81933.640     -0.69
```

## XAUUSDm M5

- config: config.json
- journal: journal_xau_current.sqlite
- csv: xauusdm_m5.csv
- fixed_lot: 0.01
- execution_enabled: True

```text
FORWARD TEST REPORT
========================================================================
start_at: 2026-05-09T00:00:00+00:00
no forward signals yet
progress: 0/50
status: collect more signals before judging strategy
```

```text
DAILY FORWARD SUMMARY
============================================================================
timezone: Asia/Bangkok | days: 7
start_at: 2026-05-09T00:00:00+00:00

date         signals   win    sl   open  timeout       wr     expR      pf
2026-05-05         0     0     0      0        0     0.0%    0.000    0.00
2026-05-06         0     0     0      0        0     0.0%    0.000    0.00
2026-05-07         0     0     0      0        0     0.0%    0.000    0.00
2026-05-08         0     0     0      0        0     0.0%    0.000    0.00
2026-05-09         0     0     0      0        0     0.0%    0.000    0.00
2026-05-10         0     0     0      0        0     0.0%    0.000    0.00
2026-05-11         0     0     0      0        0     0.0%    0.000    0.00

TOTAL
signals 0 | win 0 | sl 0 | open 0 | timeout 0 | wr 0.0% | expectancy 0.000R | PF 0.00

NEXT
- no forward signals in this period; keep Live running
```

```text
ACTUAL MT5 ORDER LEDGER
========================================================================
symbol: XAUUSDm | ledger: orders_xauusdm_current.sqlite
start_at: 2026-05-09T00:00:00+00:00
no MT5 orders in ledger yet
run order-sync while MT5 is open
```

## Next Recommended Actions

1. Keep `LIVE 01 / BTC Demo Auto` running while BTC feed is active.
2. Use `LIVE 02 / XAU Weekdays` only when the gold market is open.
3. Use `OPS 00 / Health Check` after opening the PC/MT5.
4. Use `EXEC 04 / Order Ledger All` to check actual MT5 P/L.
5. Use `OPS 01 / Safe Automation` for report, daily, order ledger, save-state, backup, and Discord digest.
6. Keep BTC/XAU auto execution demo-only with fixed lot 0.01 and guards.
