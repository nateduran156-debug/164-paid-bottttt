import asyncio
import discord
from utils.roblox import get_user_presence, get_game_name, get_universe_name, get_user_avatar_url
from utils.tracker_storage import get_all_tracks, update_last_game, get_dm_on_join, get_notify_channel
from config import PURPLE


async def send_alert(client, discord_user_id, notify_channel_id, dm_on, payload):
    if notify_channel_id:
        try:
            ch = client.get_channel(int(notify_channel_id))
            if ch:
                await ch.send(content=f"<@{discord_user_id}>", **payload)
                return
        except Exception:
            pass
    if dm_on:
        try:
            user = await client.fetch_user(int(discord_user_id))
            await user.send(**payload)
        except Exception:
            pass


async def run_tracker_cycle(client):
    try:
        tracks = get_all_tracks()
        if not tracks:
            return

        grouped = {}
        for t in tracks:
            uid = t["roblox_user_id"]
            grouped.setdefault(uid, []).append(t)

        for roblox_user_id, entries in grouped.items():
            try:
                presence = await get_user_presence(roblox_user_id)
                if not presence:
                    continue

                in_game = presence.get("userPresenceType") == 2
                place_id = presence.get("placeId")
                universe_id = presence.get("universeId")
                raw_game_id = presence.get("gameId")
                session_key = raw_game_id or (f"p:{place_id}" if place_id else None)

                for entry in entries:
                    was_in_game = entry.get("last_game_id") is not None
                    discord_user_id = entry["discord_user_id"]
                    session_changed = was_in_game and entry.get("last_game_id") != session_key

                    if in_game and (not was_in_game or session_changed):
                        update_last_game(discord_user_id, roblox_user_id, session_key, place_id)

                        notify_ch = get_notify_channel(discord_user_id)
                        dm_on = get_dm_on_join(discord_user_id)
                        if not dm_on and not notify_ch:
                            continue

                        game_name = "Unknown Game"
                        if universe_id:
                            game_name = await get_universe_name(universe_id) or game_name
                        elif place_id:
                            game_name = await get_game_name(place_id)

                        alert_game = entry.get("alert_game")
                        if alert_game and alert_game.lower() not in game_name.lower():
                            continue

                        avatar = await get_user_avatar_url(roblox_user_id)
                        username = entry["roblox_username"]

                        embed = discord.Embed(
                            description=f"**{username}** hopped in a game\ngame: `{game_name}`",
                            color=PURPLE,
                        )
                        embed.set_footer(text="tracker")
                        if avatar:
                            embed.set_author(
                                name=username,
                                icon_url=avatar,
                                url=f"https://www.roblox.com/users/{roblox_user_id}/profile",
                            )

                        if raw_game_id and place_id:
                            join_url = f"https://www.roblox.com/games/start?placeId={place_id}&gameInstanceId={raw_game_id}"
                            btn = discord.ui.Button(label="join server", style=discord.ButtonStyle.link, url=join_url)
                            view = discord.ui.View()
                            view.add_item(btn)
                            await send_alert(client, discord_user_id, notify_ch, dm_on, {"embeds": [embed], "view": view})
                        else:
                            await send_alert(client, discord_user_id, notify_ch, dm_on, {"embeds": [embed]})

                    elif not in_game and was_in_game:
                        update_last_game(discord_user_id, roblox_user_id, None, None)

            except Exception:
                continue

    except Exception as e:
        print(f"[tracker] cycle error: {e}")
