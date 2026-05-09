import os

from .cli import load_config
from .discord_bot import build_discord_reply


def main() -> None:
    token = os.environ.get("MT5_PLANNER_DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("MT5_PLANNER_DISCORD_BOT_TOKEN is missing")

    try:
        import discord
    except ImportError as exc:
        raise SystemExit(
            "discord.py is not installed. Run: pip install -r requirements-discord-bot.txt"
        ) from exc

    configs = [load_config("config_btc.json"), load_config("config.json")]
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Gloc Discord bot logged in as {client.user}")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        text = (message.content or "").strip()
        if not text.startswith("/"):
            return
        reply = build_discord_reply(text, configs)
        for chunk in split_discord(reply):
            await message.channel.send(chunk)

    client.run(token)


def split_discord(text: str, limit: int = 1900) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    current = []
    size = 0
    for line in text.splitlines():
        if size + len(line) + 1 > limit and current:
            chunks.append("\n".join(current))
            current = []
            size = 0
        current.append(line)
        size += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


if __name__ == "__main__":
    main()
