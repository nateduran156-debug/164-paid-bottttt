import discord
from config import PURPLE


def build_leaderboard_embed(pts: dict, guild_name: str) -> discord.Embed | None:
    if not pts:
        return None
    sorted_pts = sorted(pts.items(), key=lambda x: x[1], reverse=True)[:15]
    lines = []
    for i, (user_id, p) in enumerate(sorted_pts, 1):
        lines.append(f"`{i}.`  <@{user_id}>  —  **{p}** pt{'s' if p != 1 else ''}")
    embed = discord.Embed(
        title=f"{guild_name} leaderboard",
        description="\n".join(lines),
        color=PURPLE,
    )
    embed.set_footer(text=f"top {len(sorted_pts)} players")
    return embed
