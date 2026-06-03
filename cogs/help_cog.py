import discord
from discord.ext import commands
from discord import app_commands
from config import PURPLE
from utils.storage import get_prefix

CATEGORIES = {
    "ranks": {
        "label": "Ranks",
        "commands": [
            ("/addrank <roleid> <points> [name]", "sets a rank role that gets given out when someone hits that point amount"),
            ("/removerank <roleid>", "removes a rank from the list"),
            ("/ranks", "shows all rank tiers and their point requirements"),
        ],
    },
    "tags": {
        "label": "Tags",
        "commands": [
            ("/role <roblox>", "pulls up the tag dropdown for a roblox user — pick one and it gets assigned"),
            ("/tmr @role", "sets which role can use /role"),
            ("/wlrole @role [command]", "lets a role use a command, or all tag commands if you leave it blank"),
            ("/cookie <value>", "sets the roblox cookie the bot uses to rank — admin only"),
        ],
    },
    "groups": {
        "label": "Groups",
        "commands": [
            ("/gc <username>", "shows all the groups a roblox user is in and flags any opp groups"),
            ("/gid <groupid>", "sets the main roblox group for this server"),
            ("/flag <groupid>", "flags a group so gc shows it as suspicious"),
            ("/unflag <groupid>", "removes a group from the flagged list"),
            ("/flist", "lists all the groups you have flagged"),
        ],
    },
    "points": {
        "label": "Points",
        "commands": [
            ("/register <username>", "links your discord to your roblox account"),
            ("/rankup @user [amount]", "gives someone raid points — defaults to 1"),
            ("/removepoints @user [amount]", "takes points from someone"),
            ("/check [@user]", "checks your points or someone else's"),
            ("/leaderboard", "shows the top 15 in the server"),
            ("/resetall", "wipes all points — asks you to confirm first"),
            ("/wlp @role", "gives a role access to all point commands"),
            ("/psr @role", "sets a support role that can view points and the lb"),
        ],
    },
    "tracker": {
        "label": "Tracker",
        "commands": [
            ("/track add <username>", "starts tracking a roblox user — get pinged when they hop in a game"),
            ("/track remove <username>", "stops tracking someone"),
            ("/track list", "shows who you're currently tracking"),
            ("/track check <username>", "checks what game a tracked user is in right now"),
            ("/track alert <username> [game]", "only get notified for a specific game — leave blank to reset"),
            ("/track notify [#channel]", "sets where alerts go — leave blank to switch back to dms"),
            ("/track settings", "shows your current tracker setup"),
        ],
    },
    "vanity": {
        "label": "Vanity",
        "commands": [
            ("/vanity toggle", "turns the vanity watcher on or off"),
            ("/vanity setlog #channel", "sets where vanity alerts get sent"),
            ("/vanity flag <vanity>", "adds a vanity to the opp list"),
            ("/vanity unflagvanity <vanity>", "removes a vanity from the opp list"),
            ("/vanity whitelist <vanity>", "whitelists a vanity so it never triggers"),
            ("/vanity unwhitelist <vanity>", "removes something from the whitelist"),
            ("/vanity mute <vanity>", "still flags it but skips the ping"),
            ("/vanity unmute <vanity>", "turns the ping back on for a vanity"),
            ("/vanity opplist", "lists all opp vanities"),
            ("/vanity flagged", "shows everyone currently repping an opp vanity"),
            ("/vanity unflag @user", "clears the flag from a specific member"),
            ("/vanity scan", "scans everyone in the server right now"),
            ("/vanity pingrole @role", "sets the role that gets pinged on a detection"),
        ],
    },
    "setup": {
        "label": "Setup",
        "commands": [
            ("/botlogset #channel", "sets where the bot logs everything"),
            ("/gid <groupid>", "sets the main roblox group id"),
            ("/wl bot @user", "gives someone full bot access — bypasses every permission check"),
            ("/wl command <name> @user", "gives someone access to one specific command"),
            ("/whitelisted", "shows everyone on the whitelist"),
            ("/setstatus <text>", "sets the bot status — type clear to remove it"),
            ("/setpresence <status>", "sets presence to online, idle, dnd, or invisible"),
            ("/setnickname [name]", "changes the bot nickname — leave blank to reset"),
            ("/prefix <new>", "changes the prefix for this server"),
        ],
    },
}

CATEGORY_ORDER = ["ranks", "tags", "groups", "points", "tracker", "vanity", "setup"]


def build_help_embed(category_key: str, prefix: str = ">") -> discord.Embed:
    cat = CATEGORIES.get(category_key, CATEGORIES["ranks"])
    lines = []
    for cmd, desc in cat["commands"]:
        lines.append(f"`{cmd}`\n{desc}")
    embed = discord.Embed(
        title=cat["label"],
        description="\n\n".join(lines),
        color=PURPLE,
    )
    embed.set_footer(text=f"prefix: {prefix}  —  select a category below to browse")
    return embed


class HelpSelect(discord.ui.Select):
    def __init__(self, current_key: str, prefix: str = ">"):
        self.prefix = prefix
        options = [
            discord.SelectOption(
                label=CATEGORIES[k]["label"],
                value=k,
                default=(k == current_key),
            )
            for k in CATEGORY_ORDER
        ]
        super().__init__(
            placeholder=CATEGORIES[current_key]["label"],
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        embed = build_help_embed(key, self.prefix)
        view = HelpView(key, self.prefix)
        await interaction.response.edit_message(embed=embed, view=view)


class HelpView(discord.ui.View):
    def __init__(self, current_key: str = "ranks", prefix: str = ">"):
        super().__init__(timeout=180)
        self.add_item(HelpSelect(current_key, prefix))


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="164", description="browse all bot commands")
    async def help_command(self, interaction: discord.Interaction):
        prefix = get_prefix(str(interaction.guild_id)) if interaction.guild_id else ">"
        embed = build_help_embed("ranks", prefix)
        view = HelpView("ranks", prefix)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
