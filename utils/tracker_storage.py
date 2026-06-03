from utils.storage import read_json, write_json

MAX_TRACKS = 15


def get_all_tracker_data() -> dict:
    return read_json("tracker.json")


def save_all_tracker_data(data: dict):
    write_json("tracker.json", data)


def get_user_tracker(discord_user_id: str) -> dict:
    all_data = get_all_tracker_data()
    return all_data.get(discord_user_id, {"dm_on_join": True, "notify_channel": None, "tracks": {}})


def add_track(discord_user_id: str, roblox_user_id: int, roblox_username: str) -> str:
    all_data = get_all_tracker_data()
    user = all_data.get(discord_user_id, {"dm_on_join": True, "notify_channel": None, "tracks": {}})
    key = str(roblox_user_id)
    if key in user["tracks"]:
        return "exists"
    if len(user["tracks"]) >= MAX_TRACKS:
        return "limit"
    user["tracks"][key] = {
        "roblox_user_id": roblox_user_id,
        "roblox_username": roblox_username,
        "last_game_id": None,
        "last_place_id": None,
        "alert_game": None,
    }
    all_data[discord_user_id] = user
    save_all_tracker_data(all_data)
    return "added"


def remove_track(discord_user_id: str, roblox_username: str) -> bool:
    all_data = get_all_tracker_data()
    user = all_data.get(discord_user_id)
    if not user:
        return False
    entry = next(
        (v for v in user["tracks"].values() if v["roblox_username"].lower() == roblox_username.lower()),
        None,
    )
    if not entry:
        return False
    del user["tracks"][str(entry["roblox_user_id"])]
    all_data[discord_user_id] = user
    save_all_tracker_data(all_data)
    return True


def get_tracks_for_user(discord_user_id: str) -> list:
    return list(get_user_tracker(discord_user_id)["tracks"].values())


def get_all_tracks() -> list:
    all_data = get_all_tracker_data()
    result = []
    for discord_user_id, user_data in all_data.items():
        for track in user_data["tracks"].values():
            result.append({"discord_user_id": discord_user_id, **track})
    return result


def update_last_game(discord_user_id: str, roblox_user_id: int, game_id: str | None, place_id: int | None):
    all_data = get_all_tracker_data()
    user = all_data.get(discord_user_id)
    if not user:
        return
    key = str(roblox_user_id)
    if key in user["tracks"]:
        user["tracks"][key]["last_game_id"] = game_id
        user["tracks"][key]["last_place_id"] = place_id
        all_data[discord_user_id] = user
        save_all_tracker_data(all_data)


def set_track_alert(discord_user_id: str, roblox_user_id: int, alert_game: str | None):
    all_data = get_all_tracker_data()
    user = all_data.get(discord_user_id)
    if not user:
        return
    key = str(roblox_user_id)
    if key in user["tracks"]:
        user["tracks"][key]["alert_game"] = alert_game
        all_data[discord_user_id] = user
        save_all_tracker_data(all_data)


def get_dm_on_join(discord_user_id: str) -> bool:
    return get_user_tracker(discord_user_id).get("dm_on_join", True)


def set_dm_on_join(discord_user_id: str, value: bool):
    all_data = get_all_tracker_data()
    user = all_data.get(discord_user_id, {"dm_on_join": True, "notify_channel": None, "tracks": {}})
    user["dm_on_join"] = value
    all_data[discord_user_id] = user
    save_all_tracker_data(all_data)


def get_notify_channel(discord_user_id: str) -> str | None:
    return get_user_tracker(discord_user_id).get("notify_channel")


def set_notify_channel(discord_user_id: str, channel_id: str | None):
    all_data = get_all_tracker_data()
    user = all_data.get(discord_user_id, {"dm_on_join": True, "notify_channel": None, "tracks": {}})
    user["notify_channel"] = channel_id
    all_data[discord_user_id] = user
    save_all_tracker_data(all_data)
