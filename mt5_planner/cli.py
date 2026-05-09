import argparse
import json
import time
from pathlib import Path

import pandas as pd

from .indicators import add_indicators
from .journal import Journal
from .mt5_client import MT5Client
from .csv_client import get_rates_from_csv
from .strategy import analyze_trade, build_trade_plans
from .spread_filter import spread_status
from .terminal import clear_screen, print_report
from .tracker import evaluate_open_signals
from .quality import market_quality, session_label
from .market_features import compute_market_features
from .exporter import export_signals
from .exporter import export_rows
from .backtester import run_backtest
from .backtest_analyzer import analyze_backtest
from .forward_report import build_forward_report
from .daily_report import build_daily_report
from .alerts import emit_signal_alert
from .alerts import resend_latest_signal
from .alerts import send_discord_alert
from .dashboard import build_dashboard
from .dashboard_server import serve_dashboard
from .execution import clear_daily_lock, execution_status, set_daily_lock
from .project_state import save_project_state
from .backup import run_backup
from .automation import run_safe_automation
from .discord_bot import build_discord_reply
from .agent_runtime import agent_status, enqueue_task, run_agent_loop, run_agent_once


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        config = json.load(file)
    parent = config.pop("extends", None)
    if parent:
        base_path = str(Path(path).parent / parent)
        base = load_config(base_path)
        return deep_merge(base, config)
    return config


def deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def print_plans(plans: list[dict]) -> None:
    for plan in plans:
        print(
            f"{plan['mode']:>10} | {plan['direction']:>5} | "
            f"entry {plan['entry']:.3f} | sl {plan['stop_loss']:.3f} | "
            f"tp {plan['take_profit']:.3f} | rr {plan['risk_reward']:.2f} | "
            f"risk {plan['risk_pct']:.2%}"
        )
        print(f"           reason: {plan['reason']}")


def run_once(config: dict):
    client = MT5Client()
    client.connect()
    df = client.get_rates(
        symbol=config["symbol"],
        timeframe=config["timeframe"],
        bars=int(config.get("bars", 400)),
    )
    df = add_indicators(df, config.get("strategy", {}))
    return df, analyze_trade(df, config)


def command_run(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))

    while True:
        df, analysis = run_once(config)
        plans = analysis["plans"]
        spread = spread_status(df, config)
        if not spread["ok"]:
            plans = []
        features = compute_market_features(df, analysis.get("direction"))
        quality = market_quality(df.dropna().iloc[-1], spread, features)
        block_reason = quality_block_reason(config, quality)
        plans = attach_context(plans, quality, session_label(df.dropna().iloc[-1]["time"]), spread, features)
        if block_reason:
            plans = []
        session = session_label(df.dropna().iloc[-1]["time"])
        tracker_count = track_results(journal, df)
        saved_count = save_plans(journal, config, plans)
        emit_signal_alert(config["symbol"], config["timeframe"], plans, saved_count, config)
        if not args.no_clear:
            clear_screen()
        print_report(
            config["symbol"],
            config["timeframe"],
            df,
            plans,
            saved_count,
            tracker_count,
            spread,
            quality,
            session,
            block_reason,
            analysis.get("block_reason"),
            features,
        )

        if args.once:
            break
        time.sleep(int(config.get("poll_seconds", 10)))


def command_csv(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))

    while True:
        df = get_rates_from_csv(config.get("csv_path", "xauusdm_m5.csv"))
        df = add_indicators(df, config.get("strategy", {}))
        analysis = analyze_trade(df, config)
        plans = analysis["plans"]
        spread = spread_status(df, config)
        if not spread["ok"]:
            plans = []
        features = compute_market_features(df, analysis.get("direction"))
        quality = market_quality(df.dropna().iloc[-1], spread, features)
        block_reason = quality_block_reason(config, quality)
        plans = attach_context(plans, quality, session_label(df.dropna().iloc[-1]["time"]), spread, features)
        if block_reason:
            plans = []
        session = session_label(df.dropna().iloc[-1]["time"])
        tracker_count = track_results(journal, df)
        saved_count = save_plans(journal, config, plans)
        emit_signal_alert(config["symbol"], config["timeframe"], plans, saved_count, config)
        if not args.no_clear:
            clear_screen()
        print_report(
            config["symbol"],
            config["timeframe"],
            df,
            plans,
            saved_count,
            tracker_count,
            spread,
            quality,
            session,
            block_reason,
            analysis.get("block_reason"),
            features,
        )

        if args.once:
            break
        time.sleep(int(config.get("poll_seconds", 10)))


def save_plans(journal: Journal, config: dict, plans: list[dict]) -> int:
    saved_count = 0
    for plan in plans:
        if journal.save_signal(config["symbol"], config["timeframe"], plan):
            saved_count += 1
    return saved_count


def track_results(journal: Journal, df) -> int:
    rows = journal.open_signals()
    updates = evaluate_open_signals(rows, df)
    return journal.update_results(updates)


def quality_block_reason(config: dict, quality: dict) -> str | None:
    min_score = int(config.get("quality_filter", {}).get("min_score", 0))
    if min_score and int(quality["score"]) < min_score:
        return f"quality too low: {quality['score']} < {min_score}"
    return None


def attach_context(plans: list[dict], quality: dict, session: str, spread: dict, features: dict) -> list[dict]:
    for plan in plans:
        plan["source"] = "forward"
        plan["quality_score"] = quality["score"]
        plan["quality_label"] = quality["label"]
        plan["quality_notes"] = quality["notes"]
        plan["session"] = session
        plan["idea_key"] = trade_idea_key(plan)
        plan["duplicate_window_seconds"] = duplicate_window_seconds(plan)
        if spread.get("available"):
            plan["spread"] = spread["spread"]
        plan["features"] = features
    return plans


def trade_idea_key(plan: dict) -> str:
    setup = str(plan.get("setup") or "-")
    return "|".join(
        [
            str(plan.get("mode") or "-"),
            str(plan.get("direction") or "-"),
            setup,
        ]
    )


def duplicate_window_seconds(plan: dict) -> int:
    valid_for_bars = int(plan.get("valid_for_bars") or 2)
    # Treat repeated planner prints from the same setup as one trade idea.
    return max(max(valid_for_bars, 1) * 5 * 60, 15 * 60)


def command_demo(_: argparse.Namespace) -> None:
    config = {
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "risk_per_trade": 0.005,
        "strategy": {"ema_fast": 20, "ema_slow": 50, "rsi_period": 14, "atr_period": 14},
    }
    close = pd.Series(
        [2300, 2302, 2305, 2307, 2306, 2310, 2312, 2315, 2314, 2318] * 30
    )
    df = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=len(close), freq="5min"),
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close + 2,
            "low": close - 2,
            "close": close,
            "tick_volume": 100,
        }
    )
    df = add_indicators(df, config["strategy"])
    plans = build_trade_plans(df, config)
    print_report(config["symbol"], config["timeframe"], df, plans)


def command_history(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    rows = journal.recent_signals(args.limit)
    if not rows:
        print("no journal records")
        return

    print(f"{'created_at':<28} {'symbol':<9} {'tf':<4} {'mode':<12} {'side':<6} {'entry':>10} {'sl':>10} {'tp':>10} {'rr':>5} {'q':>5} {'status':>9}")
    print("-" * 123)
    for row in rows:
        print(
            f"{row['created_at']:<28} {row['symbol']:<9} {row['timeframe']:<4} "
            f"{row['mode']:<12} {row['direction']:<6} {row['entry']:>10.3f} "
            f"{row['stop_loss']:>10.3f} {row['take_profit']:>10.3f} {row['risk_reward']:>5.2f} "
            f"{str(row['quality_label'] or '-') + str(row['quality_score'] or ''):>5} "
            f"{row['status']:>9}"
        )


def command_track(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    df = get_rates_from_csv(config.get("csv_path", "xauusdm_m5.csv"))
    rows = journal.open_signals()
    updates = evaluate_open_signals(rows, df)
    updated_count = journal.update_results(updates)
    print(f"open_signals: {len(rows)}")
    print(f"updated_results: {updated_count}")
    closed_updates = [update for update in updates if update["status"] != "open"]
    for update in closed_updates[:20]:
        print(
            f"id {update['id']} -> {update['status']} "
            f"at {update['closed_at']} price {update['close_price']:.3f}"
        )


def command_stats(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    rows = journal.stats()
    if not rows:
        print("no stats yet")
        return

    print(f"{'mode':<12} {'session':<12} {'open':>6} {'tp':>6} {'sl':>6} {'amb':>6} {'closed_wr':>10}")
    print("-" * 66)
    grouped = {}
    for row in rows:
        key = (row["mode"], row["session"])
        grouped.setdefault(key, {"open": 0, "tp": 0, "tp1": 0, "be": 0, "sl": 0, "ambiguous": 0})
        grouped[key][row["status"]] = row["count"]

    for (mode, session), counts in grouped.items():
        wins = counts.get("tp", 0) + counts.get("tp1", 0)
        losses = counts.get("sl", 0)
        closed = wins + losses
        wr = wins / closed * 100 if closed else 0
        print(
            f"{mode:<12} {session:<12} {counts.get('open', 0):>6} "
            f"{wins:>6} {losses:>6} {counts.get('ambiguous', 0):>6} {wr:>9.1f}%"
        )


def command_manual_list(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    rows = journal.manual_recent(args.limit)
    if not rows:
        print("no signals yet")
        return
    print(f"{'id':>5} {'created_at':<28} {'side':<6} {'paper':<8} {'manual':<8} {'entry':>10} {'sl':>10} {'tp':>10} {'note'}")
    print("-" * 116)
    for row in rows:
        print(
            f"{row['id']:>5} {row['created_at']:<28} {row['direction']:<6} "
            f"{row['status']:<8} {str(row.get('manual_status') or '-'): <8} "
            f"{row['entry']:>10.3f} {row['stop_loss']:>10.3f} {row['take_profit']:>10.3f} "
            f"{row.get('manual_note') or ''}"
        )


def command_manual_mark(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    count = journal.update_manual(
        args.id,
        args.status,
        manual_entry=args.entry,
        manual_exit=args.exit,
        manual_note=args.note,
    )
    print(f"updated: {count}")


def command_forward_report(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    start_at = args.start_at or config.get("report", {}).get("forward_start")
    print(build_forward_report(journal.all_signals(), target_signals=args.target, start_at=start_at))


def command_daily_report(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    start_at = args.start_at or config.get("report", {}).get("forward_start")
    report = build_daily_report(journal.all_signals(), days=args.days, start_at=start_at)
    print(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report + "\n", encoding="utf-8")
        print(f"saved: {output}")
    if args.dated_output_dir:
        dated_dir = Path(args.dated_output_dir)
        dated_dir.mkdir(parents=True, exist_ok=True)
        date_name = pd.Timestamp.now(tz="Asia/Bangkok").strftime("%Y-%m-%d")
        symbol = config["symbol"].lower()
        dated_output = dated_dir / f"daily_{symbol}_{date_name}.txt"
        dated_output.write_text(report + "\n", encoding="utf-8")
        print(f"saved: {dated_output}")


def command_dashboard(args: argparse.Namespace) -> None:
    sections = []
    for config_path in args.config:
        config = load_config(config_path)
        journal = Journal(config.get("journal_path", "journal.sqlite"))
        start_at = config.get("report", {}).get("forward_start")
        rows = journal.all_signals()
        if start_at:
            from .forward_report import parse_time, row_time

            start = parse_time(start_at)
            rows = [row for row in rows if row_time(row) and row_time(row) >= start]
        sections.append({"name": f"{config['symbol']} {config['timeframe']}", "rows": rows})
    output = build_dashboard(sections, args.output, refresh_seconds=args.refresh)
    print(f"dashboard: {output}")


def command_dashboard_serve(args: argparse.Namespace) -> None:
    configs = {}
    for config_path in args.config:
        config = load_config(config_path)
        key = "btc" if "BTC" in config["symbol"].upper() else "xau"
        configs[key] = config
    serve_dashboard(configs, host=args.host, port=args.port)


def command_execution_status(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    print(execution_status(config))


def command_execution_lock(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    print(set_daily_lock(config, args.reason))


def command_execution_unlock(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    print(clear_daily_lock(config))


def command_backup(args: argparse.Namespace) -> None:
    files = [
        "config.json",
        "config_btc.json",
        "config_xau_cent.json",
        "config_btc_cent.json",
        "PROJECT_MEMORY.md",
        "USER_PLAYBOOK.md",
        "AI_RUNBOOK.md",
        "journal_xau_current.sqlite",
        "journal_btc_current.sqlite",
        "journal_xau_cent.sqlite",
        "journal_btc_cent.sqlite",
    ]
    print(run_backup(files, args.output_dir))


def command_test_discord(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    settings = config.get("alerts", {})
    send_discord_alert(settings, [args.message])
    print("discord test sent if webhook is configured")


def command_resend_latest(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    print(resend_latest_signal(config))


def command_save_state(args: argparse.Namespace) -> None:
    configs = []
    for config_path in args.config:
        config = load_config(config_path)
        config["_path"] = config_path
        configs.append(config)
    print(f"saved: {save_project_state(configs, args.output)}")


def command_safe_automation(args: argparse.Namespace) -> None:
    configs = []
    for config_path in args.config:
        config = load_config(config_path)
        config["_path"] = config_path
        configs.append(config)
    print(
        run_safe_automation(
            configs,
            send_discord=args.send_discord,
            output_dir=args.output_dir,
            backup_dir=args.backup_dir,
        )
    )


def command_discord_reply(args: argparse.Namespace) -> None:
    configs = []
    for config_path in args.config:
        config = load_config(config_path)
        config["_path"] = config_path
        configs.append(config)
    print(build_discord_reply(args.message, configs))


def command_agent_status(_: argparse.Namespace) -> None:
    print(agent_status())


def command_agent_enqueue(args: argparse.Namespace) -> None:
    print(enqueue_task(args.agent, args.action, args.note or ""))


def command_agent_run_once(args: argparse.Namespace) -> None:
    config_paths = args.config or ["config_btc.json", "config.json"]
    configs = []
    for config_path in config_paths:
        config = load_config(config_path)
        config["_path"] = config_path
        configs.append(config)
    print(run_agent_once(args.agent, configs))


def command_agent_run_loop(args: argparse.Namespace) -> None:
    config_paths = args.config or ["config_btc.json", "config.json"]
    configs = []
    for config_path in config_paths:
        config = load_config(config_path)
        config["_path"] = config_path
        configs.append(config)
    print(run_agent_loop(args.agent, configs, args.interval, args.max_cycles))


def command_export(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    rows = journal.all_signals()
    count = export_signals(rows, args.output)
    print(f"exported_rows: {count}")
    print(f"output: {args.output}")


def command_backtest(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    df = get_rates_from_csv(config.get("csv_path", "xauusdm_m5.csv"))
    rows = run_backtest(df, config, progress=not args.quiet)
    count = export_rows(rows, args.output)
    print(f"backtest_rows: {count}")
    print(f"output: {args.output}")
    print_backtest_summary(rows)


def command_analyze_backtest(args: argparse.Namespace) -> None:
    print(analyze_backtest(args.input))


def command_check_csv(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    df = get_rates_from_csv(config.get("csv_path", "xauusdm_m5.csv"))
    print(f"csv_path: {config.get('csv_path', 'xauusdm_m5.csv')}")
    print(f"rows: {len(df)}")
    if len(df):
        print(f"first: {df.iloc[0]['time']}")
        print(f"last:  {df.iloc[-1]['time']}")
        if "spread_price" in df.columns:
            print(f"spread_latest: {df.iloc[-1]['spread_price']}")


def print_backtest_summary(rows: list[dict]) -> None:
    if not rows:
        print("no backtest signals")
        return
    grouped = {}
    for row in rows:
        mode = row["mode"]
        grouped.setdefault(mode, {"tp": 0, "tp1": 0, "be": 0, "sl": 0, "timeout": 0, "ambiguous": 0})
        grouped[mode][row["status"]] = grouped[mode].get(row["status"], 0) + 1

    print(f"{'mode':<12} {'tp':>6} {'tp1':>6} {'sl':>6} {'timeout':>8} {'amb':>6} {'wr':>8}")
    print("-" * 52)
    for mode, counts in grouped.items():
        tp_full = counts.get("tp", 0)
        tp1 = counts.get("tp1", 0)
        tp = tp_full + tp1
        sl = counts.get("sl", 0)
        closed = tp + sl
        wr = tp / closed * 100 if closed else 0
        print(
            f"{mode:<12} {tp_full:>6} {tp1:>6} {sl:>6} {counts.get('timeout', 0):>8} "
            f"{counts.get('ambiguous', 0):>6} {wr:>7.1f}%"
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="mt5_planner")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run")
    run_parser.add_argument("--config", default="config.json")
    run_parser.add_argument("--once", action="store_true")
    run_parser.add_argument("--no-clear", action="store_true")
    run_parser.set_defaults(func=command_run)

    csv_parser = sub.add_parser("csv")
    csv_parser.add_argument("--config", default="config.json")
    csv_parser.add_argument("--once", action="store_true")
    csv_parser.add_argument("--no-clear", action="store_true")
    csv_parser.set_defaults(func=command_csv)

    demo_parser = sub.add_parser("demo")
    demo_parser.set_defaults(func=command_demo)

    history_parser = sub.add_parser("history")
    history_parser.add_argument("--config", default="config.json")
    history_parser.add_argument("--limit", type=int, default=20)
    history_parser.set_defaults(func=command_history)

    track_parser = sub.add_parser("track")
    track_parser.add_argument("--config", default="config.json")
    track_parser.set_defaults(func=command_track)

    stats_parser = sub.add_parser("stats")
    stats_parser.add_argument("--config", default="config.json")
    stats_parser.set_defaults(func=command_stats)

    manual_list_parser = sub.add_parser("manual-list")
    manual_list_parser.add_argument("--config", default="config.json")
    manual_list_parser.add_argument("--limit", type=int, default=20)
    manual_list_parser.set_defaults(func=command_manual_list)

    manual_mark_parser = sub.add_parser("manual-mark")
    manual_mark_parser.add_argument("--config", default="config.json")
    manual_mark_parser.add_argument("--id", type=int, required=True)
    manual_mark_parser.add_argument("--status", choices=["taken", "skipped", "missed", "watch"], required=True)
    manual_mark_parser.add_argument("--entry", type=float)
    manual_mark_parser.add_argument("--exit", type=float)
    manual_mark_parser.add_argument("--note")
    manual_mark_parser.set_defaults(func=command_manual_mark)

    report_parser = sub.add_parser("forward-report")
    report_parser.add_argument("--config", default="config.json")
    report_parser.add_argument("--target", type=int, default=50)
    report_parser.add_argument("--start-at")
    report_parser.set_defaults(func=command_forward_report)

    daily_parser = sub.add_parser("daily-report")
    daily_parser.add_argument("--config", default="config.json")
    daily_parser.add_argument("--days", type=int, default=7)
    daily_parser.add_argument("--start-at")
    daily_parser.add_argument("--output")
    daily_parser.add_argument("--dated-output-dir")
    daily_parser.set_defaults(func=command_daily_report)

    dashboard_parser = sub.add_parser("dashboard")
    dashboard_parser.add_argument("--config", action="append", default=[])
    dashboard_parser.add_argument("--output", default="reports/dashboard.html")
    dashboard_parser.add_argument("--refresh", type=int, default=15)
    dashboard_parser.set_defaults(func=command_dashboard)

    dashboard_serve_parser = sub.add_parser("dashboard-serve")
    dashboard_serve_parser.add_argument("--config", action="append", default=[])
    dashboard_serve_parser.add_argument("--host", default="127.0.0.1")
    dashboard_serve_parser.add_argument("--port", type=int, default=8765)
    dashboard_serve_parser.set_defaults(func=command_dashboard_serve)

    execution_parser = sub.add_parser("execution-status")
    execution_parser.add_argument("--config", default="config.json")
    execution_parser.set_defaults(func=command_execution_status)

    execution_lock_parser = sub.add_parser("execution-lock")
    execution_lock_parser.add_argument("--config", default="config.json")
    execution_lock_parser.add_argument("--reason", default="manual lock")
    execution_lock_parser.set_defaults(func=command_execution_lock)

    execution_unlock_parser = sub.add_parser("execution-unlock")
    execution_unlock_parser.add_argument("--config", default="config.json")
    execution_unlock_parser.set_defaults(func=command_execution_unlock)

    backup_parser = sub.add_parser("backup")
    backup_parser.add_argument("--output-dir", default="backups")
    backup_parser.set_defaults(func=command_backup)

    discord_parser = sub.add_parser("test-discord")
    discord_parser.add_argument("--config", default="config_btc.json")
    discord_parser.add_argument("--message", default="Gloc Discord test alert")
    discord_parser.set_defaults(func=command_test_discord)

    resend_parser = sub.add_parser("resend-latest")
    resend_parser.add_argument("--config", default="config_btc.json")
    resend_parser.set_defaults(func=command_resend_latest)

    state_parser = sub.add_parser("save-state")
    state_parser.add_argument("--config", action="append", default=[])
    state_parser.add_argument("--output", default="PROJECT_STATE.md")
    state_parser.set_defaults(func=command_save_state)

    automation_parser = sub.add_parser("safe-automation")
    automation_parser.add_argument("--config", action="append", default=[])
    automation_parser.add_argument("--output-dir", default="reports")
    automation_parser.add_argument("--backup-dir", default="backups")
    automation_parser.add_argument("--send-discord", action="store_true")
    automation_parser.set_defaults(func=command_safe_automation)

    discord_reply_parser = sub.add_parser("discord-reply")
    discord_reply_parser.add_argument("--config", action="append", default=[])
    discord_reply_parser.add_argument("--message", required=True)
    discord_reply_parser.set_defaults(func=command_discord_reply)

    agent_status_parser = sub.add_parser("agent-status")
    agent_status_parser.set_defaults(func=command_agent_status)

    agent_enqueue_parser = sub.add_parser("agent-enqueue")
    agent_enqueue_parser.add_argument("--agent", required=True, choices=["gloc", "kloc", "rloc", "oloc", "vloc"])
    agent_enqueue_parser.add_argument("--action", required=True)
    agent_enqueue_parser.add_argument("--note")
    agent_enqueue_parser.set_defaults(func=command_agent_enqueue)

    agent_run_parser = sub.add_parser("agent-run-once")
    agent_run_parser.add_argument("--agent", required=True, choices=["gloc", "kloc", "rloc", "oloc", "vloc"])
    agent_run_parser.add_argument("--config", action="append", default=[])
    agent_run_parser.set_defaults(func=command_agent_run_once)

    agent_loop_parser = sub.add_parser("agent-run-loop")
    agent_loop_parser.add_argument("--agent", required=True, choices=["gloc", "kloc", "rloc", "oloc", "vloc"])
    agent_loop_parser.add_argument("--config", action="append", default=[])
    agent_loop_parser.add_argument("--interval", type=int, default=30)
    agent_loop_parser.add_argument("--max-cycles", type=int, default=0)
    agent_loop_parser.set_defaults(func=command_agent_run_loop)

    export_parser = sub.add_parser("export")
    export_parser.add_argument("--config", default="config.json")
    export_parser.add_argument("--output", default="datasets/signals_dataset.csv")
    export_parser.set_defaults(func=command_export)

    backtest_parser = sub.add_parser("backtest")
    backtest_parser.add_argument("--config", default="config.json")
    backtest_parser.add_argument("--output", default="datasets/backtest_dataset.csv")
    backtest_parser.add_argument("--quiet", action="store_true")
    backtest_parser.set_defaults(func=command_backtest)

    analyze_bt_parser = sub.add_parser("analyze-backtest")
    analyze_bt_parser.add_argument("--input", default="datasets/backtest_dataset.csv")
    analyze_bt_parser.set_defaults(func=command_analyze_backtest)

    check_csv_parser = sub.add_parser("check-csv")
    check_csv_parser.add_argument("--config", default="config.json")
    check_csv_parser.set_defaults(func=command_check_csv)

    args = parser.parse_args()
    args.func(args)
