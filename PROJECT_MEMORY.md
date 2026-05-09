# MT5 AI Trading Planner - Project Memory

Use this file to continue the project in future chats.

## Current Goal

Build a free/local MT5 terminal-based AI trading planner for `XAUUSDm M5` on Exness demo USD account.

## Current Flow

```text
MT5 EA ChartDataExporter -> xauusdm_m5.csv -> Python planner -> terminal live -> journal.sqlite
```

## How To Run

In VSCode:

1. `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. Choose `001 MT5 Planner Live`

Other tasks:

- `002 MT5 Planner Run Once`
- `003 MT5 Planner History`
- `004 MT5 Planner Track Results`
- `005 MT5 Planner Stats`
- `006 MT5 Planner Export Dataset`
- `007 MT5 Planner Backtest`
- `008 MT5 Planner Analyze Backtest`
- `009 MT5 Planner Check CSV`

## Strategy Philosophy

Trade less, filter more.

`NO TRADE` is valid.

Risk first:

- show real USD risk
- warn when min lot exceeds target risk
- never rely on one indicator

## Logic Layers

The system should not require every layer to pass. Use them as scoring/context layers:

1. Trend Following
   - EMA stack
   - EMA slope
   - trend strength = EMA gap / ATR

2. Scalping Momentum
   - last 3 candles
   - close change / ATR
   - candle body quality

3. SMC MVP
   - BOS up/down
   - liquidity sweep high/low
   - prior high/low
   - SMC flow: liquidity sweep / Wyckoff trap -> CHoCH -> FVG or OB proxy

4. Fibo Context
   - swing high/low retracement
   - golden zone 0.382-0.618
   - breakout zone near high/low

5. VCP / Base
   - range contraction
   - flat base
   - breakout/retest confirmation

## Important Design Decision

Do not require all signals at once. That makes conditions too strict.

Recommended:

- Trend context is mandatory, but not EMA-based.
- Direction is now based on price action structure by default:
  - BOS up/down
  - liquidity sweep / Wyckoff trap
  - higher-high/higher-low or lower-low/lower-high
  - price position inside recent structure
- Spread must be acceptable.
- Quality score must pass.
- Entry confirmation needs one of:
  - breakout
  - retest
  - SMC + fibo alignment
  - VCP/base + momentum
  - pullback fibo in trend, if not chasing near swing extreme

Current tuning:

- `direction_method` is `structure`; EMA is no longer the main entry gate.
- EMA columns still exist for historical comparison, but live output hides them and the strategy does not require EMA stack.
- aggressive and mid modes disabled in config until backtest improves; safe only for now.
- avoid chasing near swing extremes.
- safe uses pullback entry.
- mid uses current close.
- TP uses structure or target RR, whichever is farther in trade direction.
- Session adaptive profiles are enabled; do not disable sessions, adjust TP/SL/hold/TP1 per session.
- Backtest simulates TP1/BE management.
- SMC flow from user-supplied videos is added: sweep/spring/upthrust + CHoCH + FVG/OB entry zone.
- Current 400-bar backtest did not trigger strict SMC flow much; collect/export more MT5 history before judging it.
- Long backtest showed plain fibo pullback is weak; enabled low-edge setup filter.
- Current high-edge setup tokens: vcp, retest, breakout, sweep_, wyckoff, choch.
- Setup allowlist/denylist added from 10k-bar backtest. Prefer VCP+BOS+Fibo, VCP+scalp, retest+scalp, and SMC/Wyckoff flow. Block plain fibo pullbacks.

## Current Files

- `mt5_planner/strategy.py`
- `mt5_planner/setups.py`
- `mt5_planner/market_features.py`
- `mt5_planner/quality.py`
- `mt5_planner/tracker.py`
- `mt5_planner/journal.py`
- `config.json`
- `strategy_champion_prompt.md`
- `youtube_notes/strategy_takeaways.md`

## Next Ideas

1. Review exported and backtest datasets.
2. Add ML confidence model.
3. Add dashboard only after terminal logic is stable.
4. Use analyze-backtest output before changing strategy.

## Dataset Export

Run:

```text
006 MT5 Planner Export Dataset
```

Output:

```text
datasets/signals_dataset.csv
```

Includes:

- signal plan fields
- quality/session/spread
- MFE/MAE
- setup
- scalping/trend/SMC/fibo features

## Backtest

Run:

```text
007 MT5 Planner Backtest
```

Output:

```text
datasets/backtest_dataset.csv
```

Backtest creates simulated signals even if no real/demo trade was opened. This lets the AI learn from recommended plans that the user did not execute.

Current best backtest after setup allowlist:

```text
rows: 140
tp1: 84
sl: 30
timeout: 26
WR: 73.7%
expectancy_R: +0.295
profit_factor: 2.38
```

Next metric added:

- expectancy_R
- profit_factor
- avg_win_R
- avg_loss_R

## New Chat Handoff

If context runs out, start a new chat with:

```text
อ่าน PROJECT_MEMORY.md แล้วทำต่อจาก MT5 AI Trading Planner
```

Then run:

```text
008 MT5 Planner Analyze Backtest
```

Use current files and do not restart from scratch.

## Forward Test

Live terminal tags saved signals as `source=forward`.

Live output is planner only:

```text
mode: FORWARD TEST | paper signal tracked even if skipped | real execution: manual only
```

No auto order execution is enabled.

Signals are saved and tracked from chart data even if the user does not manually enter the trade.
Use skipped signals as paper forward-test data.

Manual demo rule:

- A signal is optional, not a command to enter.
- If manually testing, do not chase after `valid_for_bars` closed candles.
- Current `valid_for_bars` is `2` for XAUUSDm and BTCUSDm.
- If price has already moved far away from entry, skip it and let the journal track the paper result.
- User mentioned possible `$100` starting account and `0.1 lot`; this is too large for current stop sizes:
  - XAUUSDm 0.1 lot average SL risk is around `$187`, more than the whole `$100` account.
  - BTCUSDm 0.1 lot average SL risk is around `$37`, about 37% of a `$100` account.
  - Use much smaller lot or cent account before any auto execution.
- User changed preference to fixed `0.01 lot`.
  - `config.json` and `config_btc.json` now use `position_sizing.fixed_lot = 0.01`.
  - XAUUSDm 0.01 lot average SL risk is still around `$18.7`, about 18.7% of `$100`.
  - BTCUSDm 0.01 lot average SL risk is around `$3.7`, about 3.7% of `$100`.
  - For a `$100` non-cent account, BTC 0.01 is more reasonable than XAU 0.01; XAU still needs caution or a cent account.
- `run_xauusdm_live.ps1` and `run_btcusdm_live.ps1` now retry CSV copy when MT5 is writing the file, instead of killing the VSCode task.
- User wants trading allowed across sessions.
  - BTC `blocked_sessions` is now `[]`.
  - XAU has no blocked session setting.
  - Session profiles still adjust TP1/SL/hold behavior, but they no longer block trading by session.
  - Market closed still means no new real XAU data/orders; BTC can continue on weekends if Exness feed is active.
- Terminal layout now shows:
  - 💹 MARKET
  - 🧱 STRUCTURE
  - 📍 LEVELS
  - ⏳ WAIT PLAN
- `mt5_planner/terminal.py` forces UTF-8 stdout so VSCode terminal can render icons/emoji instead of failing on Windows cp874.
- Fibo 38.2 / 50.0 / 61.8 levels are displayed as analysis-only reference zones.
  - They do not make entry conditions stricter by themselves.
  - Use them to explain whether price is in pullback/value zone or chasing near support/resistance.
- Added `forward-report` command and VSCode tasks:
  - `010 MT5 Planner Forward Report`
  - `106 BTC Planner Forward Report`
- Added simplified main runner:
  - `MT5_PLANNER.ps1`
  - `START_HERE.bat`
- VSCode tasks were simplified. In the task picker, use:
  - `01 MAIN BTC Live`
  - `02 MAIN XAU Live`
  - `03 MAIN Report All`
  - `04 MAIN Daily Summary All`
  - `05 MAIN Dashboard Open`
  - `06 MAIN Execution Status All`
  - `07 MAIN BTC Backtest+Analyze`
  - `08 MAIN XAU Backtest+Analyze`
  - `09 MAIN BTC Once`
  - `10 MAIN XAU Once`
- The old numbered VSCode tasks were removed from `.vscode/tasks.json` to reduce clutter. Old `.bat` files still remain as backup outside the VSCode picker.
- Forward reports start from `2026-05-09T00:00:00+00:00` to avoid mixing old journal signals from previous strategy versions.
- Report shows signals, wins/losses/open/timeout, win rate, expectancy, profit factor, average risk, progress to 50/100 signals, session/mode split, and recent signals.
- Added `daily-report` command and VSCode tasks:
  - `MAIN BTC Daily Summary`
  - `MAIN XAU Daily Summary`
- Added `QUICK_RUN_GUIDE.md`.
- Added user/AI guide split:
  - `USER_PLAYBOOK.md` is for the user to run the system day to day.
  - `AI_RUNBOOK.md` is for future AI chats to continue the project without restarting.
- Added demo/cent config separation:
  - demo USD: `config.json`, `config_btc.json`
  - real cent: `config_xau_cent.json`, `config_btc_cent.json`
  - `MT5_PLANNER.ps1` supports `-Account demo` or `-Account cent`.
- Clean journal enabled for current logic:
  - XAU demo now uses `journal_xau_current.sqlite`.
  - BTC demo now uses `journal_btc_current.sqlite`.
  - Old files `journal.sqlite` and `journal_btc.sqlite` remain as archive and are not used by default tasks.
  - Cent files remain separate: `journal_xau_cent.sqlite`, `journal_btc_cent.sqlite`.
- Added risk warning support:
  - XAU demo guard: warn above `$20` or 20% equity.
  - BTC demo guard: warn above `$5` or 5% equity.
  - Cent configs have their own journal files and risk guards.

## BTCUSDm Mode

BTC support added for weekend/crypto testing.

Files:

- `config_btc.json`
- `mt5_exporter/ChartDataExporter_BTCUSDm.mq5`
- `run_btcusdm_live.ps1`

VSCode tasks:

- `101 BTC Planner Live`
- `102 BTC Planner Run Once`
- `103 BTC Planner Check CSV`
- `104 BTC Planner Backtest`
- `105 BTC Planner Analyze Backtest`

MT5 setup:

Attach `ChartDataExporter_BTCUSDm.mq5` to `BTCUSDm M5`, export file `btcusdm_m5.csv`.

BTC spread note:

- User reported BTC spread around 1400.
- CSV spread is in price units; user-reported 1400 points appeared as around `14.0`.
- `config_btc.json` now sets `spread_filter.max_spread_price` to `20.0`.

BTC current tuning:

- `safe` only.
- `quality_filter.min_score` is `70`.
- `London AM` is blocked because historical result was weak.
- Setup filter is stricter than XAUUSD:
  - prefer `vcp+bos_up+fibo_breakout`
  - prefer `retest+scalp_momentum`
  - prefer bullish SMC/Wyckoff flow: `sweep_low`, `wyckoff_spring`, `choch_up`
  - allow short only when it looks like clear sweep/upthrust/CHoCH flow
  - block weak BTC setups such as plain fibo pullback, flat-base fibo, weak breakout-retest, and weak VCP/flat-base combinations

BTC latest backtest after BTC-specific filter and fixed TP1 simulation:

```text
rows: 81
tp1: 48
sl: 17
timeout: 16
WR: 73.8%
expectancy_R: +0.322
profit_factor: 2.53
```

Important backtest engine note:

- `mt5_planner/backtester.py` was fixed so TP1/BE management is simulated in candle order before final TP/SL classification.
- This makes the result closer to the intended partial-profit/manual management style.

Auto execution rule:

- Do not enable real/demo auto execution yet.
- First collect forward-test signals from live mode.
- Minimum gate before writing order execution:
  - backtest expectancy_R > +0.20
  - profit_factor > 1.30
  - at least 50-100 forward-test signals
  - forward test remains positive after spread/slippage
  - daily max loss and max open trades are coded
  - demo only first

## Historical Data

`ChartDataExporter.mq5` is set to export 10,000 M5 bars. After recompiling and reattaching the EA in MT5, run:

```text
009 MT5 Planner Check CSV
```

Then rerun:

```text
007 MT5 Planner Backtest
008 MT5 Planner Analyze Backtest
```

## Current Non-Logic Utilities

- VSCode task picker simplified:
  - visible tasks are now `01 Gloc BTC Live` through `08 Gloc Dashboard Open`
  - helper tasks remain in `.vscode/tasks.json` but are hidden
  - XAU task is named `02 Gloc XAU Live Weekdays` because gold is normally closed on Saturday/Sunday
- Old root `.bat` launchers moved to `scripts/legacy_launchers/`; keep `START_HERE.bat` and `MT5_PLANNER.ps1` as main entrypoints.

- New signal alert:
  - `mt5_planner/alerts.py`
  - writes `reports/alerts.log`
  - writes `reports/latest_signal.txt`
  - enabled in `config.json` and `config_btc.json`
- Daily report file:
  - `daily-report`
  - `MT5_PLANNER.ps1 -Action daily`
  - saves `reports/daily_btc.txt` or `reports/daily_xau.txt`
- Dashboard:
  - `MT5_PLANNER.ps1 -Action dashboard`
  - writes `reports/dashboard.html`
  - `05 MAIN Dashboard Open` builds and opens it
- Auto execution skeleton:
  - `execution-status`
  - execution remains OFF with `execution.enabled = false`

## Manual Journal / Backup Utilities

- Manual trade journal:
  - journal columns added for manual status/entry/exit/note
  - `manual-list` and `manual-mark` commands
  - VSCode tasks `08 MAIN BTC Manual List`, `09 MAIN XAU Manual List`
- Dashboard now has auto-refresh and manual status column.
- Daily reports also save dated files in `reports/daily/`.
- Backup added:
  - `07 MAIN Backup`
  - saves key configs, memory/playbooks, and journal files under `backups/YYYYMMDD_HHMMSS/`

## Live Dashboard / Guard Updates

- Live dashboard server added:
  - `dashboard-serve`
  - `07 MAIN Dashboard Live Server`
  - local URL `http://127.0.0.1:8765`
  - buttons for `taken`, `skipped`, `missed`, `watch`
- Task numbering changed:
  - Backup is now `08 MAIN Backup`
  - Manual list tasks are `09 MAIN BTC Manual List`, `10 MAIN XAU Manual List`
- Execution guard files added:
  - daily lock files in `guards/`
  - duplicate seen file paths in `guards/`
  - tasks `11 MAIN Guard Lock All`, `12 MAIN Guard Unlock All`
- Project state saver added:
  - `09 MAIN Save Project State`
  - writes `PROJECT_STATE.md`
  - intended to reduce token use in future chats by giving AI a concise state file
- Discord alert support added:
  - `alerts.discord.enabled` default false
  - webhook from config or `MT5_PLANNER_DISCORD_WEBHOOK`
  - docs in `DISCORD_ALERT_SETUP.md`
- User provided Discord webhook and local secret file was created:
  - `DISCORD_WEBHOOK.local.ps1`
  - loaded by `MT5_PLANNER.ps1`
  - file is ignored by `.gitignore`
  - `config.json` and `config_btc.json` have Discord alert enabled with blank webhook URL, relying on env secret
  - `10 MAIN Test Discord` sends a test alert
- Safe automation command added:
  - `mt5_planner/automation.py`
  - `MT5_PLANNER.ps1 -Symbol all -Action safe-automation`
  - VSCode task `11 MAIN Safe Automation + Discord Digest`
  - writes forward/daily reports, `PROJECT_STATE.md`, backup, and Discord digest
  - does not send orders; auto execution remains OFF
- Forward duplicate control added:
  - new signals get an `idea_key`
  - repeated same trade idea inside the current valid window is not saved again
  - forward report now shows raw `signals` plus grouped `trade ideas`
  - this prevents one market idea from being counted as many losses when the planner refreshes every few seconds
- Discord bot preparation added:
  - `mt5_planner/discord_bot.py`
  - `MT5_PLANNER.ps1 -Symbol all -Action discord-reply -Message "/status"`
  - VSCode task `12 MAIN Discord Bot Dry Reply`
  - read-only commands prepared: `/status`, `/report`, `/daily`, `/latest`, `/execution-status`
- Alert follow-up added:
  - new saved signals append to `reports/signal_inbox.txt`
  - command `resend-latest`
  - VSCode task `09 Gloc Resend Latest Signal`
  - use this to resend `reports/latest_signal.txt` to Discord if the user missed it
  - Discord messages are compact and icon-based: header, entry/SL/TP, RR/lot/risk/quality, setup
  - Discord route support added: `signals`, `reports`, `ops`
  - env vars: `MT5_PLANNER_DISCORD_SIGNALS_WEBHOOK`, `MT5_PLANNER_DISCORD_REPORTS_WEBHOOK`, `MT5_PLANNER_DISCORD_OPS_WEBHOOK`
  - docs: `DISCORD_CHANNEL_SETUP.md`
- Agent architecture doc added:
  - `AGENT_ARCHITECTURE.md`
  - five-agent model: Gloc Analyst, Vloc Executor, Kloc Journal, Rloc Reporter, Oloc Scheduler
- Gloc themed agent folder added under `agents/gloc/`:
  - Gloc Analyst
  - Vloc Executor
  - Kloc Journal
  - Rloc Reporter
  - Oloc Scheduler

## Current Agent Naming

Use these names from now on:

```text
Gloc Analyst   = วิเคราะห์กราฟ / ออก signal หรือ NO TRADE
Vloc Executor  = ส่ง order ในอนาคต ตอนนี้ OFF
Kloc Journal   = บันทึก signal, TP/SL, taken/skipped
Rloc Reporter  = Discord, dashboard, report, backup
Oloc Scheduler = ปลุกงานรายรอบ เช่น save-state/report
```

Important:

- Current Discord is webhook-only: send alert out, cannot receive user chat.
- Future Discord question/answer needs a real Discord Bot service with bot token.
- Future multi-model can use Gemini/Gemma/GPT, but all models should read/write shared files and reports.
- Vloc Executor remains the only future order gateway and is OFF.
- Local-first real agent runtime started:
  - `SOUL.md`, `AGENT_RULES.md`, `TRADE_LESSONS.md`
  - `agents/gloc/agent_manifest.json`
  - `agents/gloc/queue/pending.jsonl`, `done.jsonl`
  - `agents/gloc/prompts/*.prompt.md`
  - `mt5_planner/agent_runtime.py`
  - commands: `agent-status`, `agent-enqueue`, `agent-run-once`
  - scripts: `START_LOCAL_AGENTS.ps1`, `start_local_agents.sh`
  - tested Rloc queued report -> done log
  - added `agent-run-loop` plus `loop-rloc` and `loop-oloc` scripts
  - added `OPENCLAW_NOTES.md`; OpenClaw is optional and not needed for current CSV/journal workflow
  - added Windows Task Scheduler scripts under `scripts/scheduler/`
  - scheduler tasks: `Gloc Rloc Loop`, `Gloc Oloc Loop`
  - VSCode tasks: `10 Gloc Scheduler Status`, `11 Gloc Install Scheduler`, `12 Gloc Uninstall Scheduler`
  - Task Scheduler registration was blocked by Windows permissions in this session
  - added Startup folder fallback scripts: `install_startup_agents.ps1`, `status_startup_agents.ps1`, `uninstall_startup_agents.ps1`

## Best New Chat Prompt

When token is nearly full, open a new chat and type:

```text
อ่าน PROJECT_STATE.md, PROJECT_MEMORY.md, AI_RUNBOOK.md และ agents/gloc/README.md แล้วทำต่อจากโปรเจกต์ Gloc MT5 Planner ห้ามเริ่มใหม่ ห้ามเปิด auto execution
```

Before moving to a new chat, run:

```text
09 MAIN Save Project State
```
