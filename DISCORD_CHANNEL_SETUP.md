# Discord Channel Setup

Goal:

```text
MT5 -> VSCode/BTC Live planner -> journal -> Discord alerts/reports/chat
```

## Recommended Channels

Create these Discord text channels:

```text
#gloc-signals   = new paper signals only
#gloc-reports   = daily/forward/safe automation digest
#gloc-ops       = bot status, errors, scheduler logs
#gloc-chat      = future Q&A bot commands
```

## Webhook Mode

Webhook can send messages out. It cannot read chat.

Create webhook per channel:

1. Discord channel settings
2. Integrations
3. Webhooks
4. New Webhook
5. Copy Webhook URL

Put URLs in `DISCORD_WEBHOOK.local.ps1`:

```powershell
$env:MT5_PLANNER_DISCORD_SIGNALS_WEBHOOK = "https://discord.com/api/webhooks/..."
$env:MT5_PLANNER_DISCORD_REPORTS_WEBHOOK = "https://discord.com/api/webhooks/..."
$env:MT5_PLANNER_DISCORD_OPS_WEBHOOK = "https://discord.com/api/webhooks/..."

# fallback if the route-specific webhook is blank
$env:MT5_PLANNER_DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."
```

Current fallback behavior:

```text
signals webhook -> fallback general webhook
reports webhook -> fallback general webhook
ops webhook     -> fallback general webhook
```

## Chat Q&A Mode

For questions like:

```text
/status
/latest
/report btc
/daily all
/lesson
```

Webhook is not enough. Need Discord Bot token and a small Python bot service.

Planned flow:

```text
Discord /status
-> Rloc Discord Bot
-> mt5_planner.discord_bot.build_discord_reply(...)
-> journal/reports/SOUL.md/TRADE_LESSONS.md
-> reply in #gloc-chat
```

Safety:

```text
Bot is read-only first.
No order commands.
Vloc Executor remains OFF.
```
