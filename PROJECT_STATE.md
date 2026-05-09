# MT5 Planner Project State

saved_at: 2026-05-10T04:45:43

## Current Mode

- Forward test / paper signal only
- Auto execution OFF
- Fixed lot 0.01
- Clean current journals

## BTCUSDm M5

- config: config_btc.json
- journal: journal_btc_current.sqlite
- csv: btcusdm_m5.csv
- fixed_lot: 0.01
- execution_enabled: False

```text
FORWARD TEST REPORT
========================================================================
start_at: 2026-05-09T00:00:00+00:00
signals: 34
trade ideas: 11 grouped from 34 raw signals | wins 4 | losses 1 | closed WR 80.0%
wins: 21 | losses: 7 | open: 6 | timeout: 0 | be: 0
closed win rate: 75.0%
expectancy: 0.721R/signal | profit factor: 4.50
avg win: 1.50R | avg loss: -1.00R | avg $risk: 2.25
progress: 34/50 (16 left) | 34/100 (66 left)
decision: WAIT - collect at least 50 forward signals

SESSION
session          win    sl   open  timeout       wr
London/NY         21     7      0        0    75.0%
NY                 0     0      6        0     0.0%

MODE
mode             win    sl   open  timeout       wr
safe              21     7      6        0    75.0%

RECENT
created_at                   side   status        entry         sl         tp
2026-05-09T15:53:02.818804+00:00 long   tp        80504.059  80218.230  80932.802
2026-05-09T15:54:23.984804+00:00 long   tp        80503.649  80218.230  80931.777
2026-05-09T15:54:35.496285+00:00 long   tp        80503.129  80218.230  80930.477
2026-05-09T15:54:47.079350+00:00 long   tp        80502.969  80218.230  80930.077
2026-05-09T17:05:55.007147+00:00 long   open      80701.242  80401.450  81105.962
2026-05-09T17:06:06.451904+00:00 long   open      80705.542  80401.450  81116.067
2026-05-09T17:07:36.069588+00:00 long   open      80701.562  80401.450  81106.714
2026-05-09T17:08:21.057154+00:00 long   open      80704.542  80401.450  81113.717
2026-05-09T17:13:21.544100+00:00 long   open      80730.450  80432.800  81132.277
2026-05-09T17:13:54.977165+00:00 long   open      80729.364  80432.800  81129.726
```

```text
DAILY FORWARD SUMMARY
============================================================================
timezone: Asia/Bangkok | days: 7
start_at: 2026-05-09T00:00:00+00:00

date         signals   win    sl   open  timeout       wr     expR      pf
2026-05-04         0     0     0      0        0     0.0%    0.000    0.00
2026-05-05         0     0     0      0        0     0.0%    0.000    0.00
2026-05-06         0     0     0      0        0     0.0%    0.000    0.00
2026-05-07         0     0     0      0        0     0.0%    0.000    0.00
2026-05-08         0     0     0      0        0     0.0%    0.000    0.00
2026-05-09        28    21     7      0        0    75.0%    0.875    4.50
2026-05-10         6     0     0      6        0     0.0%    0.000    0.00

TOTAL
signals 34 | win 21 | sl 7 | open 6 | timeout 0 | wr 75.0% | expectancy 0.721R | PF 4.50

NEXT
- keep collecting until 50-100 current-logic forward signals
- do not enable auto execution until forward expectancy and PF stay positive
```

## XAUUSDm M5

- config: config.json
- journal: journal_xau_current.sqlite
- csv: xauusdm_m5.csv
- fixed_lot: 0.01
- execution_enabled: False

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
2026-05-04         0     0     0      0        0     0.0%    0.000    0.00
2026-05-05         0     0     0      0        0     0.0%    0.000    0.00
2026-05-06         0     0     0      0        0     0.0%    0.000    0.00
2026-05-07         0     0     0      0        0     0.0%    0.000    0.00
2026-05-08         0     0     0      0        0     0.0%    0.000    0.00
2026-05-09         0     0     0      0        0     0.0%    0.000    0.00
2026-05-10         0     0     0      0        0     0.0%    0.000    0.00

TOTAL
signals 0 | win 0 | sl 0 | open 0 | timeout 0 | wr 0.0% | expectancy 0.000R | PF 0.00

NEXT
- no forward signals in this period; keep Live running
```

## Next Recommended Actions

1. Keep `01 Gloc BTC Live` running while BTC feed is active.
2. Use `02 Gloc XAU Live Weekdays` only when the gold market is open.
3. Use `03 Gloc Dashboard Live` for live view and manual marks.
4. Use `04 Gloc Safe Automation` for report, daily, save-state, backup, and Discord digest.
5. Collect 50-100 forward signals before strategy or execution changes.
6. Keep auto execution disabled until forward data passes the gate.
