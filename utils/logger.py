import discord
from config import PURPLE

_client = None


def init_logger(client):
    global _client
    _client = client


async def log_to_channel(guild_id: str, title: str, description: str, fields: list = None):
    if not _client:
        return
    from utils.storage import get_guild
    s = get_guild(guild_id)
    channel_id = s.get("bot_log_channel")
    if not channel_id:
        return
    try:
        channel = _client.get_channel(int(channel_id))
        if not channel:
            return
        embed = discord.Embed(title=title, description=description, color=PURPLE)
        if fields:
            for f in fields:
                embed.add_field(name=f["name"], value=f["value"], inline=f.get("inline", False))
        await channel.send(embed=embed)
    except Exception:
        pass
