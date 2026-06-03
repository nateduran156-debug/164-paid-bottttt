import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE

CATEGORIES = {
    "ranks": {
        "label": "Ranks",
        "commands": [
            ("/addrank <roleid> <points> [name]", "add a rank tier — members get the role when they hit that points threshold"),
            ("/removerank <roleid>", "remove a rank tier"),
            ("/ranks", "list all rank tiers sorted by points needed"),
        ],
    },
    "tags": {
        "label": "Tags",
        "commands": [
            ("/role <roblox>", "gives a roblox user a tag — shows a dropdown to pick which one"),
            ("/tmr @role", "set the role that can use the /role command"),
            ("/wlrole @role [command]", "let a role use a specific command, or all tag commands if left blank"),
            ("/cookie <value>", "set the roblox bot cookie used for ranking (owner only)"),
        ],
    },
    "groups": {
        "label": "Groups",
        "commands": [
            ("/gc <username>", "check all roblox groups a user is in, with flagged group warnings"),
            ("/gid <groupid>", "set the main roblox group id for this server"),
            ("/flag <groupid>", "flag a roblox group — shows a warning when members are in it"),
            ("/unflag <groupid>", "remove a group from the flagged list"),
            ("/flist", "list all flagged groups for this server"),
        ],
    },
    "points": {
        "label": "Points",
        "commands": [
            ("/register <username>", "link your discord to your roblox username"),
            ("/rankup @user [amount]", "give a member raid points"),
            ("/removepoints @user [amount]", "take raid points from a member"),
            ("/check [@user]", "check point total — yours or someone else's"),
            ("/leaderboard", "see the top 15 point holders"),
            ("/resetall", "wipe all points (asks for confirmation)"),
            ("/wlp @role", "give a role full access to all point commands"),
            ("/psr @role", "set the points support role — they can use check and leaderboard"),
        ],
    },
    "tracker": {
        "label": "Tracker",
        "commands": [
            ("/track add <username>", "start tracking a roblox user — get pinged when they join a game"),
            ("/track remove <username>", "stop tracking a user"),
            ("/track list", "see everyone you are tracking"),
            ("/track check <username>", "check what game a tracked user is in right now"),
            ("/track alert <username> [game]", "only get notified for a specific game"),
            ("/track notify [#channel]", "set where alerts go — leave blank to switch back to dms"),
            ("/track settings", "see your current tracker settings"),
        ],
    },
    "vanity": {
        "label": "Vanity",
        "commands": [
            ("/vanity toggle", "turn the vanity watcher on or off"),
            ("/vanity setlog #channel", "set the channel where vanity detections are posted"),
            ("/vanity flag <vanity>", "mark a vanity as an opp vanity"),
            ("/vanity unflagvanity <vanity>", "remove a vanity from the opp list"),
            ("/vanity whitelist <vanity>", "whitelist a vanity so it does not trigger alerts"),
            ("/vanity unwhitelist <vanity>", "remove a vanity from the whitelist"),
            ("/vanity opplist", "list all opp vanities"),
            ("/vanity flagged", "list all members currently repping an opp vanity"),
            ("/vanity unflag @user", "manually remove a vanity flag from a member"),
            ("/vanity scan", "scan all members right now"),
            ("/vanity pingrole @role", "set what role gets pinged on detection"),
        ],
    },
    "setup": {
        "label": "Setup",
        "commands": [
            ("/botlogset #channel", "set where the bot logs its actions"),
            ("/gid <groupid>", "set the main roblox group id"),
            ("/wl bot @user", "give a user full access to all commands"),
            ("/wl command <name> @user", "give a user access to one specific command"),
            ("/whitelisted", "see all whitelisted users and roles"),
            ("/setstatus <text>", "set the bot playing status"),
            ("/setpresence <status>", "set presence to online, idle, dnd, or invisible"),
            ("/setnickname [name]", "change the bot nickname in this server"),
            ("/prefix <new>", "change the command prefix for this server"),
        ],
    },
}


class HelpSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=cat["label"], value=key)
            for key, cat in CATEGORIES.items()
        ]
        super().__init__(placeholder="pick a category", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        embed = build_help_embed(key)
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpSelectMenu())


def build_help_embed(category_key: str) -> discord.Embed:
    cat = CATEGORIES.get(category_key, list(CATEGORIES.values())[0])
    lines = []
    for cmd, desc in cat["commands"]:
        lines.append(f"`{cmd}`\n{desc}")
    embed = discord.Embed(
        title=cat["label"],
        description="\n\n".join(lines),
        color=PURPLE,
    )
    embed.set_footer(text="/164")
    return embed


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="164", description="shows all bot commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = build_help_embed("ranks")
        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
