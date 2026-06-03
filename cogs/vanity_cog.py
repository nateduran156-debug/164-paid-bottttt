import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.vanity_storage import (
    toggle_vanity, is_vanity_enabled, set_vanity_log_channel,
    add_opp_vanity, remove_opp_vanity, get_opp_vanities,
    add_whitelisted_vanity, remove_whitelisted_vanity, get_whitelisted_vanities,
    get_flagged_members, unflag_member, set_ping_role,
    add_silent_vanity, remove_silent_vanity, is_member_flagged,
)
from handlers.vanity_handler import scan_all_members


class VanityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    vanity = app_commands.Group(name="vanity", description="discord vanity url monitoring")

    def is_admin(self, interaction: discord.Interaction) -> bool:
        from utils.storage import is_superuser
        if is_superuser(interaction.user.id):
            return True
        return interaction.user.guild_permissions.administrator

    @vanity.command(name="toggle", description="turn the vanity watcher on or off")
    async def vanity_toggle(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        guild_id = str(interaction.guild_id)
        enabled = toggle_vanity(guild_id)
        state = "on" if enabled else "off"
        embed = discord.Embed(description=f"vanity watcher is now **{state}**", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="setlog", description="set the channel where vanity detections are posted")
    @app_commands.describe(channel="the channel for vanity alerts")
    async def vanity_setlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        set_vanity_log_channel(str(interaction.guild_id), str(channel.id))
        embed = discord.Embed(description=f"vanity alerts going to {channel.mention}", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="flag", description="mark a vanity as an opp vanity")
    @app_commands.describe(vanity="the vanity to flag (with or without the slash)")
    async def vanity_flag(self, interaction: discord.Interaction, vanity: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        ok = add_opp_vanity(str(interaction.guild_id), vanity)
        v = vanity.lower().lstrip("/")
        if not ok:
            await interaction.response.send_message(f"`/{v}` is already flagged", ephemeral=True)
            return
        embed = discord.Embed(description=f"`/{v}` is now marked as an opp vanity", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="unflagvanity", description="remove a vanity from the opp list")
    @app_commands.describe(vanity="the vanity to remove")
    async def vanity_unflagvanity(self, interaction: discord.Interaction, vanity: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        ok = remove_opp_vanity(str(interaction.guild_id), vanity)
        v = vanity.lower().lstrip("/")
        if not ok:
            await interaction.response.send_message(f"`/{v}` is not flagged", ephemeral=True)
            return
        embed = discord.Embed(description=f"`/{v}` removed from the opp list", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="whitelist", description="whitelist a vanity so it never triggers alerts")
    @app_commands.describe(vanity="the vanity to whitelist")
    async def vanity_whitelist(self, interaction: discord.Interaction, vanity: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        ok = add_whitelisted_vanity(str(interaction.guild_id), vanity)
        v = vanity.lower().lstrip("/")
        if not ok:
            await interaction.response.send_message(f"`/{v}` is already whitelisted", ephemeral=True)
            return
        embed = discord.Embed(description=f"`/{v}` whitelisted — will not trigger alerts", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="unwhitelist", description="remove a vanity from the whitelist")
    @app_commands.describe(vanity="the vanity to remove from the whitelist")
    async def vanity_unwhitelist(self, interaction: discord.Interaction, vanity: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        ok = remove_whitelisted_vanity(str(interaction.guild_id), vanity)
        v = vanity.lower().lstrip("/")
        if not ok:
            await interaction.response.send_message(f"`/{v}` is not whitelisted", ephemeral=True)
            return
        embed = discord.Embed(description=f"`/{v}` removed from the whitelist", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="opplist", description="list all opp vanities")
    async def vanity_opplist(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        opps = get_opp_vanities(guild_id)
        if not opps:
            embed = discord.Embed(description="no opp vanities set up yet", color=PURPLE)
        else:
            lines = [f"`/{v}`" for v in opps]
            embed = discord.Embed(description="\n".join(lines), color=PURPLE)
            embed.set_footer(text=f"vanity  {len(opps)} flagged")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="vanities", description="list all whitelisted vanities")
    async def vanity_vanities(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        wl = get_whitelisted_vanities(guild_id)
        if not wl:
            embed = discord.Embed(description="no whitelisted vanities", color=PURPLE)
        else:
            lines = [f"`/{v}`" for v in wl]
            embed = discord.Embed(description="\n".join(lines), color=PURPLE)
            embed.set_footer(text=f"vanity  {len(wl)} whitelisted")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="flagged", description="list all members currently repping an opp vanity")
    async def vanity_flagged(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        flagged = get_flagged_members(guild_id)
        if not flagged:
            embed = discord.Embed(description="no members are currently flagged", color=PURPLE)
        else:
            lines = [f"<@{uid}>  —  `/{data['vanity']}`" for uid, data in flagged.items()]
            embed = discord.Embed(description="\n".join(lines), color=PURPLE)
            embed.set_footer(text=f"vanity  {len(flagged)} flagged members")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="unflag", description="manually remove a vanity flag from a member")
    @app_commands.describe(user="the member to unflag")
    async def vanity_unflag(self, interaction: discord.Interaction, user: discord.Member):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        ok = unflag_member(str(interaction.guild_id), str(user.id))
        if not ok:
            await interaction.response.send_message(f"{user.mention} is not flagged", ephemeral=True)
            return
        embed = discord.Embed(description=f"removed flag from {user.mention}", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="scan", description="scan all members for opp vanities right now")
    async def vanity_scan(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        await interaction.response.defer()
        count = await scan_all_members(self.bot, str(interaction.guild_id))
        embed = discord.Embed(
            description=f"scan complete — {count} new member{'s' if count != 1 else ''} flagged",
            color=PURPLE,
        )
        embed.set_footer(text="vanity")
        await interaction.followup.send(embed=embed)

    @vanity.command(name="pingrole", description="set what role gets pinged when a vanity is detected")
    @app_commands.describe(role="the role to ping — leave blank to use @everyone")
    async def vanity_pingrole(self, interaction: discord.Interaction, role: discord.Role = None):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        set_ping_role(str(interaction.guild_id), str(role.id) if role else None)
        if role:
            desc = f"vanity pings going to {role.mention}"
        else:
            desc = "vanity pings now use @everyone"
        embed = discord.Embed(description=desc, color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="mute", description="mute a vanity — still flags but no ping")
    @app_commands.describe(vanity="the vanity to mute")
    async def vanity_mute(self, interaction: discord.Interaction, vanity: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        ok = add_silent_vanity(str(interaction.guild_id), vanity)
        v = vanity.lower().lstrip("/")
        if not ok:
            await interaction.response.send_message(f"`/{v}` is already muted", ephemeral=True)
            return
        embed = discord.Embed(description=f"`/{v}` muted — still flags, no ping", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)

    @vanity.command(name="unmute", description="unmute a vanity so it pings again")
    @app_commands.describe(vanity="the vanity to unmute")
    async def vanity_unmute(self, interaction: discord.Interaction, vanity: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        ok = remove_silent_vanity(str(interaction.guild_id), vanity)
        v = vanity.lower().lstrip("/")
        if not ok:
            await interaction.response.send_message(f"`/{v}` is not muted", ephemeral=True)
            return
        embed = discord.Embed(description=f"`/{v}` unmuted — will ping again", color=PURPLE)
        embed.set_footer(text="vanity")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(VanityCog(bot))
