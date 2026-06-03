import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE, ALL_TAGS
from utils.storage import (
    get_guild, set_guild, member_has_tag_manager_role,
    get_whitelist, get_roblox_cookie, is_superuser,
)
from utils.roblox import give_roblox_tag


class TagSelectMenu(discord.ui.Select):
    def __init__(self, roblox_username: str, requester_id: int):
        self.roblox_username = roblox_username
        self.requester_id = requester_id
        options = [discord.SelectOption(label=t, value=t.lower()) for t in ALL_TAGS]
        super().__init__(placeholder="pick a tag", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not is_superuser(interaction.user.id) and interaction.user.id != self.requester_id:
            await interaction.response.send_message("that menu isn't yours", ephemeral=True)
            return

        tag = self.values[0]
        await interaction.response.defer(ephemeral=True)
        result = await give_roblox_tag(self.roblox_username, tag)

        if result["ok"]:
            embed = discord.Embed(
                description=f"done\nuser: **{self.roblox_username}**\ntag: **{tag}**",
                color=PURPLE,
            )
        else:
            embed = discord.Embed(
                description=f"couldn't assign the tag\nuser: **{self.roblox_username}**\nreason: {result.get('reason', 'unknown')}",
                color=PURPLE,
            )
        embed.set_footer(text="tags")
        await interaction.edit_original_response(embed=embed, view=None)


class TagSelectView(discord.ui.View):
    def __init__(self, roblox_username: str, requester_id: int):
        super().__init__(timeout=60)
        self.add_item(TagSelectMenu(roblox_username, requester_id))


class TagsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def can_use_role(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            return False
        member = interaction.user
        guild_id = str(interaction.guild_id)
        if is_superuser(member.id):
            return True
        if member.guild_permissions.administrator:
            return True
        if member_has_tag_manager_role(member, guild_id):
            return True
        return False

    @app_commands.command(name="role", description="assign a roblox tag to a user")
    @app_commands.describe(roblox="their roblox username")
    async def role_command(self, interaction: discord.Interaction, roblox: str):
        if not self.can_use_role(interaction):
            await interaction.response.send_message("you don't have access to that", ephemeral=True)
            return
        if not get_roblox_cookie():
            await interaction.response.send_message("no roblox cookie set — use /cookie first", ephemeral=True)
            return
        embed = discord.Embed(
            description=f"pick a tag to give **{roblox}**",
            color=PURPLE,
        )
        embed.set_footer(text="tags")
        view = TagSelectView(roblox, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="cookie", description="set the roblox bot cookie used for ranking")
    @app_commands.describe(cookie="your .ROBLOSECURITY cookie value")
    async def cookie_command(self, interaction: discord.Interaction, cookie: str):
        if not is_superuser(interaction.user.id) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        from utils.storage import set_roblox_cookie
        set_roblox_cookie(cookie)
        await interaction.response.send_message("cookie saved", ephemeral=True)

    @app_commands.command(name="tmr", description="set the tag manager role")
    @app_commands.describe(role="the role that can use /role")
    async def tmr_command(self, interaction: discord.Interaction, role: discord.Role):
        if not is_superuser(interaction.user.id) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        set_guild(str(interaction.guild_id), {"tag_manager_role": str(role.id)})
        embed = discord.Embed(
            description=f"tag manager role set to {role.mention}",
            color=PURPLE,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wlrole", description="give a role access to a command or all tag commands")
    @app_commands.describe(role="the role", command="command name — skip this for tag manager access")
    async def wlrole_command(self, interaction: discord.Interaction, role: discord.Role, command: str = None):
        if not is_superuser(interaction.user.id) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("only admins can do that", ephemeral=True)
            return
        guild_id = str(interaction.guild_id)
        s = get_guild(guild_id)
        if not command:
            roles = list(s.get("tag_manager_roles", []))
            if str(role.id) in roles:
                await interaction.response.send_message(f"{role.mention} is already a tag manager role", ephemeral=True)
                return
            roles.append(str(role.id))
            set_guild(guild_id, {"tag_manager_roles": roles})
            embed = discord.Embed(description=f"{role.mention} can now use /role", color=PURPLE)
        else:
            command_roles = dict(s.get("command_roles", {}))
            command_roles.setdefault(command, [])
            if str(role.id) in command_roles[command]:
                await interaction.response.send_message(f"{role.mention} already has that", ephemeral=True)
                return
            command_roles[command].append(str(role.id))
            set_guild(guild_id, {"command_roles": command_roles})
            embed = discord.Embed(description=f"{role.mention} can now use /{command}", color=PURPLE)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TagsCog(bot))
