import re
import discord
from utils.vanity_storage import (
    is_vanity_enabled, get_vanity_log_channel, get_opp_vanities,
    get_whitelisted_vanities, get_silent_vanities, get_ping_role,
    is_member_flagged, flag_member,
)
from config import PURPLE


def extract_vanities(status: str) -> list:
    matches = re.findall(r"/[a-zA-Z0-9_]+", status)
    return [m[1:].lower() for m in matches]


def get_custom_status(member: discord.Member) -> str | None:
    for activity in member.activities:
        if activity.type == discord.ActivityType.custom:
            return activity.state
    return None


async def check_member_vanity(client, member: discord.Member):
    if member.bot:
        return
    guild_id = str(member.guild.id)
    if not is_vanity_enabled(guild_id):
        return

    log_channel_id = get_vanity_log_channel(guild_id)
    if not log_channel_id:
        return

    status = get_custom_status(member)
    if not status:
        return

    opp_vanities = get_opp_vanities(guild_id)
    if not opp_vanities:
        return

    whitelisted = get_whitelisted_vanities(guild_id)
    silent_vanities = get_silent_vanities(guild_id)
    ping_role_id = get_ping_role(guild_id)
    status_vanities = extract_vanities(status)

    for vanity in status_vanities:
        if vanity in whitelisted:
            continue
        if vanity not in opp_vanities:
            continue
        if is_member_flagged(guild_id, str(member.id)):
            return

        flag_member(guild_id, str(member.id), vanity)

        try:
            channel = client.get_channel(int(log_channel_id))
            if not channel:
                return

            embed = discord.Embed(
                description=(
                    f"repping   **/{vanity}**\n"
                    f"status    `{status}`\n"
                    f"id        `{member.id}`"
                ),
                color=PURPLE,
            )
            embed.set_author(
                name=f"{member.display_name}  —  vanity detected",
                icon_url=member.display_avatar.url,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="vanity system")

            is_silent = vanity in silent_vanities
            if is_silent:
                await channel.send(embed=embed)
            elif ping_role_id:
                await channel.send(content=f"<@&{ping_role_id}>", embed=embed)
            else:
                await channel.send(content="@everyone", embed=embed)
        except Exception:
            pass
        return


async def scan_all_members(client, guild_id: str) -> int:
    count = 0
    guild = client.get_guild(int(guild_id))
    if not guild:
        return 0
    if not is_vanity_enabled(guild_id):
        return 0
    try:
        await guild.chunk()
    except Exception:
        pass
    for member in guild.members:
        if member.bot:
            continue
        before = is_member_flagged(guild_id, str(member.id))
        await check_member_vanity(client, member)
        after = is_member_flagged(guild_id, str(member.id))
        if not before and after:
            count += 1
    return count
