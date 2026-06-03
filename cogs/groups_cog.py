import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.storage import get_guild, set_guild, is_superuser
from utils.roblox import get_user_by_username, get_user_groups


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
            embed = discord.Embed(description=f"could not find **{username}** on roblox", color=PURPLE)
            await interaction.followup.send(embed=embed)
            return
        groups = await get_user_groups(user["id"])
        s = get_guild(guild_id) if guild_id else {}
        flagged_groups = set(s.get("flagged_groups", []))
        group_lines = []
        flagged_hits = []
        for entry in groups:
            g = entry.get("group", {})
            role = entry.get("role", {})
            gid = str(g.get("id", ""))
            gname = g.get("name", "unknown group")
            rname = role.get("name", "")
            is_flagged = gid in flagged_groups
            flag_label = "  [FLAGGED]" if is_flagged else ""
            group_lines.append(f"`{gid}`  {gname}  —  {rname}{flag_label}")
            if is_flagged:
                flagged_hits.append(gname)
        if not group_lines:
            group_lines = ["not in any groups"]
        description = f"**{user['name']}** — id `{user['id']}`\ngroups: **{len(groups)}**"
        if flagged_hits:
            description += f"\nflagged: {', '.join(flagged_hits)}"
        chunks = []
        current = ""
        for line in group_lines:
            if len(current) + len(line) + 1 > 3800:
                chunks.append(current)
                current = line
            else:
                current = (current + "\n" + line) if current else line
        if current:
            chunks.append(current)
        embed = discord.Embed(
            title=f"group check  —  {user['name']}",
            description=description + "\n\n" + (chunks[0] if chunks else ""),
            color=PURPLE,
        )
        embed.set_footer(text=f"user id: {user['id']}")
        await interaction.followup.send(embed=embed)
        for chunk in chunks[1:]:
            extra = discord.Embed(description=chunk, color=PURPLE)
            await interaction.channel.send(embed=extra)

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
