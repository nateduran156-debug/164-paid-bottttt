import discord
from discord.ext import commands
from discord import app_commands
from utils.help_data import build_help_embed, HelpView
from utils.storage import get_prefix


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="164", description="browse all bot commands")
    async def help_164(self, interaction: discord.Interaction):
        prefix = get_prefix(str(interaction.guild_id)) if interaction.guild_id else ">"
        embed = build_help_embed("ranks", prefix)
        view = HelpView("ranks", prefix)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="help", description="browse all bot commands")
    async def help_slash(self, interaction: discord.Interaction):
        prefix = get_prefix(str(interaction.guild_id)) if interaction.guild_id else ">"
        embed = build_help_embed("ranks", prefix)
        view = HelpView("ranks", prefix)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
