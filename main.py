import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.logger import init_logger
from handlers.tracker_handler import run_tracker_cycle
from config import DEFAULT_PREFIX

load_dotenv()

token = os.environ.get("DISCORD_BOT_TOKEN")
if not token:
    print("DISCORD_BOT_TOKEN is not set in your .env file")
    exit(1)


async def get_prefix(bot, message):
    if message.guild:
        from utils.storage import get_prefix
        return get_prefix(str(message.guild.id))
    return DEFAULT_PREFIX


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

COGS = [
    "cogs.help_cog",
    "cogs.tags_cog",
    "cogs.ranks_cog",
    "cogs.points_cog",
    "cogs.groups_cog",
    "cogs.tracker_cog",
    "cogs.vanity_cog",
    "cogs.setup_cog",
    "cogs.prefix_cog",
]


@bot.event
async def on_ready():
    init_logger(bot)
    print(f"logged in as {bot.user} — {bot.user.id}")
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} slash commands")
    except Exception as e:
        print(f"failed to sync commands: {e}")

    # start tracker loop
    async def tracker_loop():
        await asyncio.sleep(5)
        while True:
            await run_tracker_cycle(bot)
            await asyncio.sleep(30)

    asyncio.create_task(tracker_loop())


@bot.event
async def on_presence_update(before, after):
    from handlers.vanity_handler import check_member_vanity
    if before.activities != after.activities:
        await check_member_vanity(bot, after)


async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"loaded {cog}")
            except Exception as e:
                print(f"failed to load {cog}: {e}")
        await bot.start(token)


asyncio.run(main())
