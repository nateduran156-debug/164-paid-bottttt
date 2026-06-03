import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.roblox import get_user_by_username, get_user_presence, get_game_name, get_universe_name
from utils.tracker_storage import (
    add_track, remove_track, get_tracks_for_user,
    set_track_alert, get_dm_on_join, set_dm_on_join,
    get_notify_channel, set_notify_channel, MAX_TRACKS,
)


class TrackerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    track = app_commands.Group(name="track", description="roblox player tracking")

    @track.command(name="add", description="start tracking a roblox user")
    @app_commands.describe(username="their roblox username")
    async def track_add(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer(ephemeral=True)
        user = await get_user_by_username(username)
        if not user:
            embed = discord.Embed(
                description=f"could not find **{username}** on roblox",
                color=PURPLE,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        result = add_track(str(interaction.user.id), user["id"], user["name"])
        if result == "exists":
            embed = discord.Embed(
                description=f"you are already tracking **{user['name']}**",
                color=PURPLE,
            )
        elif result == "limit":
            embed = discord.Embed(
                description=f"you have hit the {MAX_TRACKS} track limit — remove one first",
                color=PURPLE,
            )
        else:
            embed = discord.Embed(
                description=f"now tracking **{user['name']}**\nyou will be notified when they join a game",
                color=PURPLE,
            )
        embed.set_footer(text="tracker")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @track.command(name="remove", description="stop tracking a roblox user")
    @app_commands.describe(username="their roblox username")
    async def track_remove(self, interaction: discord.Interaction, username: str):
        removed = remove_track(str(interaction.user.id), username)
        if removed:
            embed = discord.Embed(description=f"stopped tracking **{username}**", color=PURPLE)
        else:
            embed = discord.Embed(description=f"**{username}** is not in your tracking list", color=PURPLE)
        embed.set_footer(text="tracker")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @track.command(name="list", description="see everyone you are currently tracking")
    async def track_list(self, interaction: discord.Interaction):
        tracks = get_tracks_for_user(str(interaction.user.id))
        if not tracks:
            embed = discord.Embed(description="you are not tracking anyone yet — use /track add", color=PURPLE)
            embed.set_footer(text="tracker")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        lines = [f"`{i+1}.`  **{t['roblox_username']}**  —  id `{t['roblox_user_id']}`" for i, t in enumerate(tracks)]
        embed = discord.Embed(description="\n".join(lines), color=PURPLE)
        embed.set_footer(text=f"tracker  {len(tracks)}/{MAX_TRACKS}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @track.command(name="check", description="check what a tracked user is currently doing")
    @app_commands.describe(username="their roblox username")
    async def track_check(self, interaction: discord.Interaction, username: str):
        tracks = get_tracks_for_user(str(interaction.user.id))
        match = next((t for t in tracks if t["roblox_username"].lower() == username.lower()), None)
        if not match:
            embed = discord.Embed(description=f"**{username}** is not in your tracking list", color=PURPLE)
            embed.set_footer(text="tracker")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        presence = await get_user_presence(match["roblox_user_id"])
        if not presence:
            embed = discord.Embed(description=f"could not get presence for **{username}**", color=PURPLE)
            embed.set_footer(text="tracker")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        ptype = presence.get("userPresenceType", 0)
        if ptype == 2:
            place_id = presence.get("placeId")
            universe_id = presence.get("universeId")
            game_name = "Unknown Game"
            if universe_id:
                game_name = await get_universe_name(universe_id) or game_name
            elif place_id:
                game_name = await get_game_name(place_id)
            desc = f"**{username}** is in a game\ngame: `{game_name}`"
        elif ptype == 3:
            desc = f"**{username}** is in roblox studio"
        elif ptype == 1:
            desc = f"**{username}** is on the roblox website"
        else:
            desc = f"**{username}** is offline"
        embed = discord.Embed(description=desc, color=PURPLE)
        embed.set_footer(text="tracker")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @track.command(name="alert", description="only get notified when a tracked user joins a specific game")
    @app_commands.describe(username="their roblox username", game="game name filter — leave blank for all games")
    async def track_alert(self, interaction: discord.Interaction, username: str, game: str = None):
        tracks = get_tracks_for_user(str(interaction.user.id))
        match = next((t for t in tracks if t["roblox_username"].lower() == username.lower()), None)
        if not match:
            embed = discord.Embed(description=f"**{username}** is not in your tracking list", color=PURPLE)
            embed.set_footer(text="tracker")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        set_track_alert(str(interaction.user.id), match["roblox_user_id"], game)
        if game:
            desc = f"filter set for **{username}**\nonly alerting for: `{game}`"
        else:
            desc = f"filter cleared for **{username}**\ngetting alerts for any game"
        embed = discord.Embed(description=desc, color=PURPLE)
        embed.set_footer(text="tracker")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @track.command(name="notify", description="set where tracker alerts go — leave blank for dms")
    @app_commands.describe(channel="the channel to send alerts to")
    async def track_notify(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if channel:
            set_notify_channel(str(interaction.user.id), str(channel.id))
            desc = f"alerts going to {channel.mention}"
        else:
            set_notify_channel(str(interaction.user.id), None)
            desc = "alerts going to your dms"
        embed = discord.Embed(description=desc, color=PURPLE)
        embed.set_footer(text="tracker")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @track.command(name="settings", description="see your current tracker settings")
    async def track_settings(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        dm_on = get_dm_on_join(user_id)
        notify_ch = get_notify_channel(user_id)
        tracks = get_tracks_for_user(user_id)
        desc = (
            f"dms: {'on' if dm_on else 'off'}\n"
            f"alerts go to: {f'<#{notify_ch}>' if notify_ch else 'your dms'}\n"
            f"tracking: **{len(tracks)}/{MAX_TRACKS}** users"
        )
        embed = discord.Embed(description=desc, color=PURPLE)
        embed.set_footer(text="tracker")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TrackerCog(bot))
