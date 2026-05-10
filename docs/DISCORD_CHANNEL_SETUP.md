# Discord Channel Setup

Goal:

```text
MT5 -> VSCode/BTC Live planner -> journal -> Discord alerts/reports/chat
```

## Recommended Channels

Create these Discord text channels:

```text
#signals   = strategy signals and resend-latest
#reports   = forward, daily, safe automation digest
#ops       = Vloc execution, manager, guard, scheduler status
#chat      = future read-only Q&A bot and manual notes
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
$env:MT5_PLANNER_DISCORD_CHAT_WEBHOOK = "https://discord.com/api/webhooks/..."

# fallback if the route-specific webhook is blank
$env:MT5_PLANNER_DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."
```

Current fallback behavior:

```text
signals webhook -> fallback general webhook
reports webhook -> fallback general webhook
ops webhook     -> fallback general webhook
chat webhook    -> fallback general webhook
```

## Test One Channel

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action test-discord -DiscordRoute signals
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action test-discord -DiscordRoute reports
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action test-discord -DiscordRoute ops
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action test-discord -DiscordRoute chat
```

## Message Style

```text
signals = compact embed: entry, SL, TP, RR, lot, risk, quality, setup, notes
reports = short digest: grouped paper ideas + actual MT5 order result
ops     = only important execution/manager events; normal max-open blocks are logged but not spammed
chat    = reserved for read-only Q&A later
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
