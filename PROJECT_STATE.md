# MT5 Planner Project State

saved_at: 2026-05-10T04:51:26

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
trade ideas: 6 grouped from 34 raw signals | wins 4 | losses 1 | open 1 | timeout 0 | closed WR 80.0%
raw signals: wins 21 | losses 7 | open 6 | timeout 0 | be 0
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
2026-05-09T14:43:19.789562+00:00 long   sl        80311.164  80235.141  80433.000
2026-05-09T15:42:38.369551+00:00 long   tp        80478.257  80218.230  80868.298
2026-05-09T15:42:50.735949+00:00 long   tp        80497.487  80218.230  80916.373
2026-05-09T15:43:25.864966+00:00 long   tp        80424.474  80218.230  80733.840
2026-05-09T15:50:21.884131+00:00 long   tp        80506.164  80218.230  80938.065
2026-05-09T17:05:55.007147+00:00 long   open      80701.242  80401.450  81105.962
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
