import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.storage import get_guild, set_guild, is_superuser
from utils.roblox import get_user_by_username, get_user_groups, get_user_avatar_url


def admin_or_super(interaction: discord.Interaction) -> bool:
    return is_superuser(interaction.user.id) or interaction.user.guild_permissions.administrator


class GroupsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gc", description="run a group check on a roblox user")
    @app_commands.describe(username="roblox username to check")
    async def gc(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""

        user = await get_user_by_username(username)
        if not user:
            embed = discord.Embed(
                description=f"no roblox account found for **{username}**",
                color=PURPLE,
            )
            await interaction.followup.send(embed=embed)
            return

        groups = await get_user_groups(user["id"])
        s = get_guild(guild_id) if guild_id else {}
        flagged_groups = set(s.get("flagged_groups", []))
        avatar_url = await get_user_avatar_url(user["id"])

        normal_lines = []
        flagged_lines = []

        for entry in groups:
            g = entry.get("group", {})
            role = entry.get("role", {})
            gid = str(g.get("id", ""))
            gname = g.get("name", "unknown")
            rname = role.get("name", "")
            if gid in flagged_groups:
                flagged_lines.append(f"`{gid}`  {gname}  —  {rname}")
            else:
                normal_lines.append(f"`{gid}`  {gname}  —  {rname}")

        embed = discord.Embed(color=PURPLE)

        if avatar_url:
            embed.set_author(
                name=user["name"],
                icon_url=avatar_url,
                url=f"https://www.roblox.com/users/{user['id']}/profile",
            )
            embed.set_thumbnail(url=avatar_url)
        else:
            embed.set_author(
                name=user["name"],
                url=f"https://www.roblox.com/users/{user['id']}/profile",
            )

        embed.add_field(
            name="user id",
            value=f"`{user['id']}`",
            inline=True,
        )
        embed.add_field(
            name="groups",
            value=str(len(groups)) if groups else "0",
            inline=True,
        )
        embed.add_field(
            name="flagged",
            value=str(len(flagged_lines)) if flagged_lines else "none",
            inline=True,
        )

        if flagged_lines:
            chunk = "\n".join(flagged_lines[:10])
            if len(flagged_lines) > 10:
                chunk += f"\n... and {len(flagged_lines) - 10} more"
            embed.add_field(name="flagged groups", value=chunk, inline=False)

        if normal_lines:
            # split into chunks of 20 to avoid hitting 1024 char field limit
            chunk_size = 20
            for i in range(0, min(len(normal_lines), 40), chunk_size):
                chunk = "\n".join(normal_lines[i:i + chunk_size])
                label = "groups" if i == 0 else "groups (cont.)"
                embed.add_field(name=label, value=chunk, inline=False)
        elif not groups:
            embed.add_field(name="groups", value="not in any groups", inline=False)

        embed.set_footer(text="group check")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gid", description="set the main roblox group id for this server")
    @app_commands.describe(groupid="the roblox group id")
    async def gid(self, interaction: discord.Interaction, groupid: str):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        set_guild(str(interaction.guild_id), {"group_id": groupid})
        embed = discord.Embed(description=f"main group id set to `{groupid}`", color=PURPLE)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="flag", description="flag a roblox group — shows a warning when members are in it")
    @app_commands.describe(groupid="the roblox group id to flag")
    async def flag(self, interaction: discord.Interaction, groupid: str):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        guild_id = str(interaction.guild_id)
        s = get_guild(guild_id)
        flagged = list(s.get("flagged_groups", []))
        if groupid in flagged:
            await interaction.response.send_message(f"`{groupid}` is already flagged", ephemeral=True)
            return
        flagged.append(groupid)
        set_guild(guild_id, {"flagged_groups": flagged})
        embed = discord.Embed(description=f"group `{groupid}` is now flagged", color=PURPLE)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unflag", description="remove a group from the flagged list")
    @app_commands.describe(groupid="the group id to unflag")
    async def unflag(self, interaction: discord.Interaction, groupid: str):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        guild_id = str(interaction.guild_id)
        s = get_guild(guild_id)
        flagged = list(s.get("flagged_groups", []))
        if groupid not in flagged:
            await interaction.response.send_message(f"`{groupid}` is not flagged", ephemeral=True)
            return
        flagged.remove(groupid)
        set_guild(guild_id, {"flagged_groups": flagged})
        embed = discord.Embed(description=f"group `{groupid}` removed from the flagged list", color=PURPLE)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="flist", description="list all flagged groups for this server")
    async def flist(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        s = get_guild(guild_id)
        flagged = s.get("flagged_groups", [])
        if not flagged:
            embed = discord.Embed(description="no groups flagged yet", color=PURPLE)
            await interaction.response.send_message(embed=embed)
            return
        lines = [f"`{i+1}.`  `{gid}`" for i, gid in enumerate(flagged)]
        embed = discord.Embed(description="\n".join(lines), color=PURPLE)
        embed.set_footer(text=f"flagged groups  {len(flagged)}")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(GroupsCog(bot))
