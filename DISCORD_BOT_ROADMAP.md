# Discord Bot Roadmap

ตอนนี้ระบบใช้ Discord webhook:

```text
Rloc Reporter -> Discord channel
```

Webhook ส่งข้อความออกได้อย่างเดียว ยังอ่านคำถามจาก Discord ไม่ได้

## ถ้าจะพิมพ์ถามใน Discord แล้วให้บอทตอบ

ต้องเพิ่ม Discord Bot service:

```text
Discord user
  -> slash command/message
  -> Rloc Discord Bot
  -> read PROJECT_STATE.md / journal / reports
  -> reply in Discord
```

## Commands ที่ควรเริ่มก่อน

Read-only:

```text
/status
/signals btc
/signals xau
/report
/daily
/latest
/execution-status
```

Manual journal:

```text
/mark <signal_id> taken
/mark <signal_id> skipped
/mark <signal_id> missed
/mark <signal_id> watch
/clear-mark <signal_id>
```

Safety:

```text
/lock
/unlock
/save-state
```

ห้ามเปิดคำสั่งส่ง order จนกว่า Vloc Executor ผ่าน gate

## สิ่งที่ต้องมีเมื่อเช่า server

```text
Discord Bot Token
Python service หรือ Node service
MT5 data source หรือ copied CSV/journal sync
secret env file
process runner เช่น systemd/pm2/Windows Task Scheduler
backup folder
```

## Security

- อย่า commit bot token หรือ webhook ลง Git
- เก็บ secret ใน `.local.ps1`, `.env`, หรือ server secret manager
- ถ้า webhook/token หลุด ให้ regenerate ทันที
## Prepared Local Bot Router

The project now has a read-only Discord command router:

```text
mt5_planner/discord_bot.py
```

Dry-run it locally:

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action discord-reply -Message "/status"
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action discord-reply -Message "/report btc"
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action discord-reply -Message "/daily all"
```

Supported read-only commands:

```text
/status
/report [btc|xau|all]
/daily [btc|xau|all]
/latest
/execution-status [btc|xau|all]
```

Next server step:

```text
Discord Bot service receives slash command
  -> passes command text to build_discord_reply(...)
  -> replies with the returned text
```

Keep write/trading commands unavailable until Vloc Executor passes the gate.

## Channel Split Added

Discord webhooks can now be routed:

```text
signals -> MT5_PLANNER_DISCORD_SIGNALS_WEBHOOK
reports -> MT5_PLANNER_DISCORD_REPORTS_WEBHOOK
ops     -> MT5_PLANNER_DISCORD_OPS_WEBHOOK
```

Fallback:

```text
MT5_PLANNER_DISCORD_WEBHOOK
```

Read `DISCORD_CHANNEL_SETUP.md`.
