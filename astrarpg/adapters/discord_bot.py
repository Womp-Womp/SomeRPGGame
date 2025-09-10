import asyncio
import os

from ..config import DISCORD_BOT_TOKEN


def main() -> int:
    try:
        import discord  # type: ignore
    except Exception:
        print("py-cord is not installed. Install dependencies from requirements.txt.")
        return 1

    from ..engine.commands import GameState, dispatch
    from ..engine.models import Player

    intents = discord.Intents.default()
    bot = discord.Bot(intents=intents)

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")

    @bot.slash_command(description="Play AstraRPG commands")
    async def rpg(ctx, command: str):
        pid = f"discord:{ctx.author.id}"
        gs = GameState(Player(id=pid, name=ctx.author.display_name))
        msg, _ = dispatch(gs, command)
        await ctx.respond(msg[:1900])

    token = DISCORD_BOT_TOKEN or os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Set DISCORD_BOT_TOKEN in your environment to run the bot.")
        return 1
    bot.run(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

