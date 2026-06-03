import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.storage import (
    get_points, save_points, get_registered, set_registered,
    get_guild, member_has_points_role, member_has_psr,
    get_whitelist, has_full_access,
)
from utils.leaderboard import build_leaderboard_embed
from cogs.ranks_cog import sync_rank_roles
from utils.roblox import get_user_by_username


class ConfirmResetView(discord.ui.View):
    def __init__(self, guild_id: str, requester_id: int):
        super().__init__(timeout=15)
        self.guild_id = guild_id
        self.requester_id = requester_id

    @discord.ui.button(label="reset all points", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("this is not yours", ephemeral=True)
            return
        save_points(self.guild_id, {})
        embed = discord.Embed(description="done — all points cleared", color=PURPLE)
        embed.set_footer(text="points")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("this is not yours", ephemeral=True)
            return
        embed = discord.Embed(description="cancelled — nothing changed", color=PURPLE)
        embed.set_footer(text="points")
        await interaction.response.edit_message(embed=embed, view=None)


class PointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def can_manage_points(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        guild_id = str(interaction.guild_id)
        if member.guild_permissions.administrator:
            return True
        wl = get_whitelist()
        if str(member.id) in wl.get("bot", []):
            return True
        if member_has_points_role(member, guild_id):
            return True
        return False

    def can_support_points(self, interaction: discord.Interaction) -> bool:
        if self.can_manage_points(interaction):
            return True
        return member_has_psr(interaction.user, str(interaction.guild_id))

    @app_commands.command(name="register", description="link your discord to your roblox username")
    @app_commands.describe(username="your roblox username")
    async def register(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer(ephemeral=True)
        user = await get_user_by_username(username)
        if not user:
            embed = discord.Embed(
                description=f"could not find **{username}** on roblox — double check the spelling",
                color=PURPLE,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        set_registered(str(interaction.user.id), user["name"])
        embed = discord.Embed(
            description=f"linked\ndiscord: **{interaction.user.name}**\nroblox: **{user['name']}**",
            color=PURPLE,
        )
        embed.set_footer(text="register")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="rankup", description="add raid points to a member")
    @app_commands.describe(user="the member to give points to", amount="how many to add (default 1)")
    async def rankup(self, interaction: discord.Interaction, user: discord.Member, amount: int = 1):
        if not self.can_manage_points(interaction):
            await interaction.response.send_message("you don't have permission to do that", ephemeral=True)
            return
        if amount < 1:
            await interaction.response.send_message("amount has to be at least 1", ephemeral=True)
            return
        await interaction.response.defer()
        guild_id = str(interaction.guild_id)
        pts = get_points(guild_id)
        pts[str(user.id)] = pts.get(str(user.id), 0) + amount
        save_points(guild_id, pts)
        s = get_guild(guild_id)
        gained, _ = await sync_rank_roles(interaction.guild, str(user.id), pts[str(user.id)], s.get("rank_roles", []))
        promo = f"\nrank unlocked: {', '.join(gained)}" if gained else ""
        embed = discord.Embed(
            description=f"+**{amount}** to {user.mention}\ntotal: **{pts[str(user.id)]}** pts{promo}",
            color=PURPLE,
        )
        embed.set_footer(text=f"given by {interaction.user.name}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="removepoints", description="remove raid points from a member")
    @app_commands.describe(user="the member to remove points from", amount="how many to remove (default 1)")
    async def removepoints(self, interaction: discord.Interaction, user: discord.Member, amount: int = 1):
        if not self.can_manage_points(interaction):
            await interaction.response.send_message("you don't have permission to do that", ephemeral=True)
            return
        if amount < 1:
            await interaction.response.send_message("amount has to be at least 1", ephemeral=True)
            return
        await interaction.response.defer()
        guild_id = str(interaction.guild_id)
        pts = get_points(guild_id)
        pts[str(user.id)] = max(0, pts.get(str(user.id), 0) - amount)
        save_points(guild_id, pts)
        s = get_guild(guild_id)
        _, lost = await sync_rank_roles(interaction.guild, str(user.id), pts[str(user.id)], s.get("rank_roles", []))
        demotion = f"\nrank removed: {', '.join(lost)}" if lost else ""
        embed = discord.Embed(
            description=f"-**{amount}** from {user.mention}\ntotal: **{pts[str(user.id)]}** pts{demotion}",
            color=PURPLE,
        )
        embed.set_footer(text=f"removed by {interaction.user.name}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="check", description="check your or someone else's point total")
    @app_commands.describe(user="who to check (default: yourself)")
    async def check(self, interaction: discord.Interaction, user: discord.Member = None):
        subject = user or interaction.user
        if user and user.id != interaction.user.id:
            if not self.can_support_points(interaction):
                await interaction.response.send_message("you don't have permission to check other people", ephemeral=True)
                return
        guild_id = str(interaction.guild_id)
        pts = get_points(guild_id)
        p = pts.get(str(subject.id), 0)
        embed = discord.Embed(
            description=f"{subject.mention}  —  **{p}** pt{'s' if p != 1 else ''}",
            color=PURPLE,
        )
        embed.set_footer(text="points")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="see the top 15 point holders")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        pts = get_points(guild_id)
        embed = build_leaderboard_embed(pts, interaction.guild.name)
        if not embed:
            await interaction.response.send_message("nobody has any points yet", ephemeral=True)
            return
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetall", description="wipe all raid points in the server")
    async def resetall(self, interaction: discord.Interaction):
        if not self.can_manage_points(interaction):
            await interaction.response.send_message("you don't have permission to do that", ephemeral=True)
            return
        embed = discord.Embed(
            description="this will wipe every point in the server and cannot be undone",
            color=PURPLE,
        )
        embed.set_footer(text="points")
        view = ConfirmResetView(str(interaction.guild_id), interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="wlp", description="give a role full access to all point commands")
    @app_commands.describe(role="the role to whitelist")
    async def wlp(self, interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        from utils.storage import set_guild
        set_guild(str(interaction.guild_id), {"points_role": str(role.id)})
        embed = discord.Embed(
            description=f"{role.mention} can now manage all point commands",
            color=PURPLE,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="psr", description="set the points support role — they can view points and check leaderboard")
    @app_commands.describe(role="the points support role")
    async def psr(self, interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        from utils.storage import set_guild
        set_guild(str(interaction.guild_id), {"points_support_role": str(role.id)})
        embed = discord.Embed(
            description=f"{role.mention} can now use /check and /leaderboard",
            color=PURPLE,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PointsCog(bot))
