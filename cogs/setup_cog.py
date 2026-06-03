import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.storage import get_guild, set_guild, get_whitelist, set_whitelist, is_superuser


def admin_or_super(interaction: discord.Interaction) -> bool:
    return is_superuser(interaction.user.id) or interaction.user.guild_permissions.administrator


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="botlogset", description="set the channel where the bot logs its actions")
    @app_commands.describe(channel="the log channel")
    async def botlogset(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        set_guild(str(interaction.guild_id), {"bot_log_channel": str(channel.id)})
        embed = discord.Embed(description=f"bot logs going to {channel.mention}", color=PURPLE)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="prefix", description="change the command prefix for this server")
    @app_commands.describe(new="the new prefix")
    async def prefix(self, interaction: discord.Interaction, new: str):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        if len(new) > 5:
            await interaction.response.send_message("prefix can be max 5 characters", ephemeral=True)
            return
        set_guild(str(interaction.guild_id), {"prefix": new})
        embed = discord.Embed(description=f"prefix set to `{new}`", color=PURPLE)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setstatus", description="set the bot playing status — use 'clear' to remove it")
    @app_commands.describe(text="the status text, or 'clear' to remove")
    async def setstatus(self, interaction: discord.Interaction, text: str):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        if text.lower() == "clear":
            await self.bot.change_presence(activity=None)
            await interaction.response.send_message("status cleared", ephemeral=True)
        else:
            await self.bot.change_presence(activity=discord.Game(name=text))
            await interaction.response.send_message(f"status set to **{text}**", ephemeral=True)

    @app_commands.command(name="setpresence", description="set the bot presence status")
    @app_commands.describe(status="online, idle, dnd, or invisible")
    @app_commands.choices(status=[
        app_commands.Choice(name="online", value="online"),
        app_commands.Choice(name="idle", value="idle"),
        app_commands.Choice(name="dnd", value="dnd"),
        app_commands.Choice(name="invisible", value="invisible"),
    ])
    async def setpresence(self, interaction: discord.Interaction, status: str):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.do_not_disturb,
            "invisible": discord.Status.invisible,
        }
        await self.bot.change_presence(status=status_map.get(status, discord.Status.online))
        await interaction.response.send_message(f"presence set to **{status}**", ephemeral=True)

    @app_commands.command(name="setnickname", description="change the bot nickname in this server")
    @app_commands.describe(name="the new nickname — leave blank to reset")
    async def setnickname(self, interaction: discord.Interaction, name: str = None):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        try:
            bot_member = interaction.guild.get_member(self.bot.user.id)
            await bot_member.edit(nick=name)
            msg = f"nickname set to **{name}**" if name else "nickname cleared"
            await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"could not set nickname: {e}", ephemeral=True)

    @app_commands.command(name="wl", description="manage bot whitelist")
    @app_commands.describe(
        action="bot (full access) or command (one command)",
        user="the user to whitelist",
        command_name="command name — only needed for the command action",
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="bot", value="bot"),
        app_commands.Choice(name="command", value="command"),
    ])
    async def wl(self, interaction: discord.Interaction, action: str, user: discord.User, command_name: str = None):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        wl_data = get_whitelist()
        if action == "bot":
            wl_data.setdefault("bot", [])
            if str(user.id) in wl_data["bot"]:
                await interaction.response.send_message(f"{user.mention} already has full access", ephemeral=True)
                return
            wl_data["bot"].append(str(user.id))
            set_whitelist(wl_data)
            embed = discord.Embed(description=f"{user.mention} now has full access to all commands", color=PURPLE)
        else:
            if not command_name:
                await interaction.response.send_message("give me a command name too — `/wl command @user commandname`", ephemeral=True)
                return
            wl_data.setdefault(command_name, [])
            if str(user.id) in wl_data[command_name]:
                await interaction.response.send_message(f"{user.mention} can already use /{command_name}", ephemeral=True)
                return
            wl_data[command_name].append(str(user.id))
            set_whitelist(wl_data)
            embed = discord.Embed(description=f"{user.mention} can now use /{command_name}", color=PURPLE)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="whitelisted", description="see all whitelisted users and roles")
    async def whitelisted(self, interaction: discord.Interaction):
        if not admin_or_super(interaction):
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        wl_data = get_whitelist()
        guild_id = str(interaction.guild_id)
        s = get_guild(guild_id)
        lines = []
        for key, ids in wl_data.items():
            if ids:
                mentions = ", ".join(f"<@{i}>" for i in ids)
                lines.append(f"**/{key}**\n{mentions}")
        cmd_roles = s.get("command_roles", {})
        for key, role_ids in cmd_roles.items():
            if role_ids:
                mentions = ", ".join(f"<@&{r}>" for r in role_ids)
                lines.append(f"**/{key}** (roles)\n{mentions}")
        tag_mgr_roles = s.get("tag_manager_roles", [])
        if tag_mgr_roles:
            mentions = ", ".join(f"<@&{r}>" for r in tag_mgr_roles)
            lines.append(f"**tag manager** (roles)\n{mentions}")
        if not lines:
            await interaction.response.send_message("nothing whitelisted yet", ephemeral=True)
            return
        embed = discord.Embed(description="\n\n".join(lines), color=PURPLE)
        embed.set_footer(text="whitelist")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SetupCog(bot))
