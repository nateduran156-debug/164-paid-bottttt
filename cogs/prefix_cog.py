import discord
from discord.ext import commands
from config import PURPLE
from utils.storage import (
    get_points, save_points, get_guild, get_whitelist,
    member_has_points_role, get_prefix,
)
from utils.leaderboard import build_leaderboard_embed
from utils.roblox import get_user_by_username, get_user_groups
from cogs.ranks_cog import sync_rank_roles


def ts():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


class PrefixCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def can_manage_points(self, ctx) -> bool:
        member = ctx.author
        guild_id = str(ctx.guild.id)
        if member.guild_permissions.administrator:
            return True
        wl = get_whitelist()
        if str(member.id) in wl.get("bot", []):
            return True
        if member_has_points_role(member, guild_id):
            return True
        return False

    @commands.command(name="rankup")
    async def rankup(self, ctx, user: discord.Member = None, amount: int = 1):
        if not self.can_manage_points(ctx):
            return await ctx.reply("you don't have permission to do that")
        if not user:
            return await ctx.reply("mention a user to give points to")
        if amount < 1:
            return await ctx.reply("amount has to be at least 1")
        guild_id = str(ctx.guild.id)
        pts = get_points(guild_id)
        pts[str(user.id)] = pts.get(str(user.id), 0) + amount
        save_points(guild_id, pts)
        s = get_guild(guild_id)
        gained, _ = await sync_rank_roles(ctx.guild, str(user.id), pts[str(user.id)], s.get("rank_roles", []))
        promo = f"\nrank unlocked: {', '.join(gained)}" if gained else ""
        embed = discord.Embed(
            description=f"+**{amount}** to {user.mention}\ntotal: **{pts[str(user.id)]}** pts{promo}",
            color=PURPLE,
        )
        embed.set_footer(text=f"given by {ctx.author.name}")
        await ctx.reply(embed=embed)

    @commands.command(name="remove")
    async def remove_points(self, ctx, user: discord.Member = None, amount: int = 1):
        if not self.can_manage_points(ctx):
            return await ctx.reply("you don't have permission to do that")
        if not user:
            return await ctx.reply("mention a user to remove points from")
        if amount < 1:
            return await ctx.reply("amount has to be at least 1")
        guild_id = str(ctx.guild.id)
        pts = get_points(guild_id)
        pts[str(user.id)] = max(0, pts.get(str(user.id), 0) - amount)
        save_points(guild_id, pts)
        s = get_guild(guild_id)
        _, lost = await sync_rank_roles(ctx.guild, str(user.id), pts[str(user.id)], s.get("rank_roles", []))
        demotion = f"\nrank removed: {', '.join(lost)}" if lost else ""
        embed = discord.Embed(
            description=f"-**{amount}** from {user.mention}\ntotal: **{pts[str(user.id)]}** pts{demotion}",
            color=PURPLE,
        )
        embed.set_footer(text=f"removed by {ctx.author.name}")
        await ctx.reply(embed=embed)

    @commands.command(name="check")
    async def check(self, ctx, user: discord.Member = None):
        subject = user or ctx.author
        guild_id = str(ctx.guild.id)
        pts = get_points(guild_id)
        p = pts.get(str(subject.id), 0)
        embed = discord.Embed(
            description=f"{subject.mention}  —  **{p}** pt{'s' if p != 1 else ''}",
            color=PURPLE,
        )
        embed.set_footer(text="points")
        await ctx.reply(embed=embed)

    @commands.command(name="lb")
    async def lb(self, ctx):
        guild_id = str(ctx.guild.id)
        pts = get_points(guild_id)
        embed = build_leaderboard_embed(pts, ctx.guild.name)
        if not embed:
            return await ctx.reply("nobody has any points yet")
        await ctx.reply(embed=embed)

    @commands.command(name="gc")
    async def gc(self, ctx, username: str = None):
        if not username:
            return await ctx.reply(f"usage: `{get_prefix(str(ctx.guild.id))}gc <roblox username>`")
        msg = await ctx.reply("looking up groups...")
        guild_id = str(ctx.guild.id)
        user = await get_user_by_username(username)
        if not user:
            return await msg.edit(content=f"could not find **{username}** on roblox")
        groups = await get_user_groups(user["id"])
        s = get_guild(guild_id)
        flagged_groups = set(s.get("flagged_groups", []))
        lines = []
        flagged_hits = []
        for entry in groups:
            g = entry.get("group", {})
            role = entry.get("role", {})
            gid = str(g.get("id", ""))
            gname = g.get("name", "unknown")
            rname = role.get("name", "")
            is_flagged = gid in flagged_groups
            flag_label = "  [FLAGGED]" if is_flagged else ""
            lines.append(f"`{gid}`  {gname}  —  {rname}{flag_label}")
            if is_flagged:
                flagged_hits.append(gname)
        if not lines:
            lines = ["not in any groups"]
        description = f"**{user['name']}**  —  {len(groups)} groups"
        if flagged_hits:
            description += f"\nflagged: {', '.join(flagged_hits)}"
        embed = discord.Embed(
            title=f"group check  —  {user['name']}",
            description=description + "\n\n" + "\n".join(lines[:30]),
            color=PURPLE,
        )
        embed.set_footer(text=f"user id: {user['id']}")
        await msg.edit(content=None, embed=embed)

    @commands.command(name="ranks")
    async def ranks(self, ctx):
        guild_id = str(ctx.guild.id)
        s = get_guild(guild_id)
        rank_list = sorted(s.get("rank_roles", []), key=lambda r: r["points"])
        if not rank_list:
            return await ctx.reply("no ranks set up yet")
        lines = [
            f"`{i+1}.`  <@&{r['role_id']}>  —  **{r['points']}** pts  —  `{r['name']}`"
            for i, r in enumerate(rank_list)
        ]
        embed = discord.Embed(description="\n".join(lines), color=PURPLE)
        embed.set_footer(text=f"ranks  {len(rank_list)}/30")
        await ctx.reply(embed=embed)

    @commands.command(name="help")
    async def help_prefix(self, ctx):
        from utils.help_data import build_help_embed, HelpView
        prefix = get_prefix(str(ctx.guild.id))
        embed = build_help_embed("ranks", prefix)
        view = HelpView("ranks", prefix)
        await ctx.reply(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(PrefixCog(bot))
