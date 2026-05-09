# Discord Bot Setup

Webhook sends alerts. Bot reads chat and replies.

## Commands

```text
/help
/status
/latest
/report btc
/report xau
/daily all
/execution-status all
/lesson
```

Blocked:

```text
order
close
enable execution
modify position
```

## Setup

1. Create a Discord application/bot in Discord Developer Portal.
2. Enable Message Content Intent.
3. Invite bot to the server.
4. Put token in `DISCORD_WEBHOOK.local.ps1`:

```powershell
$env:MT5_PLANNER_DISCORD_BOT_TOKEN = "..."
```

5. Install dependency:

```powershell
pip install -r requirements-discord-bot.txt
```

6. Run:

```powershell
powershell -ExecutionPolicy Bypass -File START_DISCORD_BOT.ps1
```

Safety:

```text
Read-only first.
Vloc Executor remains OFF.
```
