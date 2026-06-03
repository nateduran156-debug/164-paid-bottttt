import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.storage import get_guild, set_guild, is_superuser


async def sync_rank_roles(guild: discord.Guild, user_id: str, current_points: int, ranks: list) -> tuple[list, list]:
    if not ranks:
        return [], []
    try:
        member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
    except Exception:
        return [], []
    gained = []
    lost = []
    for rank in ranks:
        qualifies = current_points >= rank["points"]
        role = guild.get_role(int(rank["role_id"]))
        if not role:
            continue
        has_role = role in member.roles
        if qualifies and not has_role:
            try:
                await member.add_roles(role)
                gained.append(rank["name"])
            except Exception:
                pass
        elif not qualifies and has_role:
            try:
                await member.remove_roles(role)
                lost.append(rank["name"])
            except Exception:
                pass
    return gained, lost


def admin_or_super(interaction: discord.Interaction) -> bool:
    return is_superuser(interaction.user.id) or interaction.user.guild_permissions.administrator


class RanksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addrank", description="add a rank tier that unlocks at a certain points threshold")
    @app_commands.describe(roleid="the discord role id", points="how many points to unlock this rank", name="custom name for the rank")
    async def addrank(self, interaction: discord.Interaction, roleid: str, points: int, name: str = None):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        if points < 1:
            await interaction.response.send_message("points has to be at least 1", ephemeral=True)
            return
        guild_id = str(interaction.guild_id)
        role_id = roleid.strip().replace("<@&", "").replace(">", "").replace("#", "")
        role = interaction.guild.get_role(int(role_id)) if role_id.isdigit() else None
        if not role:
            await interaction.response.send_message("could not find that role — give me a valid role id", ephemeral=True)
            return
        s = get_guild(guild_id)
        ranks = list(s.get("rank_roles", []))
        if len(ranks) >= 30:
            await interaction.response.send_message("you have hit the 30 rank limit — remove one before adding another", ephemeral=True)
            return
        if any(r["role_id"] == str(role.id) for r in ranks):
            await interaction.response.send_message(f"{role.mention} is already set up as a rank", ephemeral=True)
            return
        rank_name = name or role.name
        ranks.append({"role_id": str(role.id), "points": points, "name": rank_name})
        set_guild(guild_id, {"rank_roles": ranks})
        embed = discord.Embed(
            description=f"rank added\nrole: {role.mention}\npoints needed: **{points}**\nname: **{rank_name}**",
            color=PURPLE,
        )
        embed.set_footer(text=f"ranks  {len(ranks)}/30")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removerank", description="remove a rank tier")
    @app_commands.describe(roleid="the role id of the rank to remove")
    async def removerank(self, interaction: discord.Interaction, roleid: str):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        guild_id = str(interaction.guild_id)
        role_id = roleid.strip().replace("<@&", "").replace(">", "")
        s = get_guild(guild_id)
        ranks = list(s.get("rank_roles", []))
        match = next((r for r in ranks if r["role_id"] == role_id), None)
        if not match:
            await interaction.response.send_message(f"no rank configured with role id `{role_id}`", ephemeral=True)
            return
        ranks.remove(match)
        set_guild(guild_id, {"rank_roles": ranks})
        embed = discord.Embed(description=f"removed rank **{match['name']}**", color=PURPLE)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ranks", description="list all configured rank tiers")
    async def ranks(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        s = get_guild(guild_id)
        rank_list = sorted(s.get("rank_roles", []), key=lambda r: r["points"])
        if not rank_list:
            await interaction.response.send_message("no ranks set up yet — use /addrank to get started", ephemeral=True)
            return
        lines = [
            f"`{i+1}.`  <@&{r['role_id']}>  —  **{r['points']}** pts  —  `{r['name']}`"
            for i, r in enumerate(rank_list)
        ]
        embed = discord.Embed(description="\n".join(lines), color=PURPLE)
        embed.set_footer(text=f"ranks  {len(rank_list)}/30")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(RanksCog(bot))
