from utils.storage import read_json, write_json


def get_guild_vanity(guild_id: str) -> dict:
    all_data = read_json("vanity.json")
    return all_data.get(guild_id, {
        "enabled": False,
        "log_channel": None,
        "opp_vanities": [],
        "whitelisted_vanities": [],
        "silent_vanities": [],
        "flagged_members": {},
        "ping_role": None,
    })


def save_guild_vanity(guild_id: str, data: dict):
    all_data = read_json("vanity.json")
    all_data[guild_id] = data
    write_json("vanity.json", all_data)


def is_vanity_enabled(guild_id: str) -> bool:
    return get_guild_vanity(guild_id).get("enabled", False)


def toggle_vanity(guild_id: str) -> bool:
    s = get_guild_vanity(guild_id)
    s["enabled"] = not s.get("enabled", False)
    save_guild_vanity(guild_id, s)
    return s["enabled"]


def get_vanity_log_channel(guild_id: str) -> str | None:
    return get_guild_vanity(guild_id).get("log_channel")


def set_vanity_log_channel(guild_id: str, channel_id: str | None):
    s = get_guild_vanity(guild_id)
    s["log_channel"] = channel_id
    save_guild_vanity(guild_id, s)


def get_opp_vanities(guild_id: str) -> list:
    return get_guild_vanity(guild_id).get("opp_vanities", [])


def add_opp_vanity(guild_id: str, vanity: str) -> bool:
    s = get_guild_vanity(guild_id)
    v = vanity.lower().lstrip("/")
    if v in s.get("opp_vanities", []):
        return False
    s.setdefault("opp_vanities", []).append(v)
    save_guild_vanity(guild_id, s)
    return True


def remove_opp_vanity(guild_id: str, vanity: str) -> bool:
    s = get_guild_vanity(guild_id)
    v = vanity.lower().lstrip("/")
    if v not in s.get("opp_vanities", []):
        return False
    s["opp_vanities"].remove(v)
    save_guild_vanity(guild_id, s)
    return True


def get_whitelisted_vanities(guild_id: str) -> list:
    return get_guild_vanity(guild_id).get("whitelisted_vanities", [])


def add_whitelisted_vanity(guild_id: str, vanity: str) -> bool:
    s = get_guild_vanity(guild_id)
    v = vanity.lower().lstrip("/")
    if v in s.get("whitelisted_vanities", []):
        return False
    s.setdefault("whitelisted_vanities", []).append(v)
    save_guild_vanity(guild_id, s)
    return True


def remove_whitelisted_vanity(guild_id: str, vanity: str) -> bool:
    s = get_guild_vanity(guild_id)
    v = vanity.lower().lstrip("/")
    if v not in s.get("whitelisted_vanities", []):
        return False
    s["whitelisted_vanities"].remove(v)
    save_guild_vanity(guild_id, s)
    return True


def get_silent_vanities(guild_id: str) -> list:
    return get_guild_vanity(guild_id).get("silent_vanities", [])


def add_silent_vanity(guild_id: str, vanity: str) -> bool:
    s = get_guild_vanity(guild_id)
    v = vanity.lower().lstrip("/")
    if v in s.get("silent_vanities", []):
        return False
    s.setdefault("silent_vanities", []).append(v)
    save_guild_vanity(guild_id, s)
    return True


def remove_silent_vanity(guild_id: str, vanity: str) -> bool:
    s = get_guild_vanity(guild_id)
    v = vanity.lower().lstrip("/")
    if v not in s.get("silent_vanities", []):
        return False
    s["silent_vanities"].remove(v)
    save_guild_vanity(guild_id, s)
    return True


def get_flagged_members(guild_id: str) -> dict:
    return get_guild_vanity(guild_id).get("flagged_members", {})


def is_member_flagged(guild_id: str, user_id: str) -> bool:
    return user_id in get_guild_vanity(guild_id).get("flagged_members", {})


def flag_member(guild_id: str, user_id: str, vanity: str):
    s = get_guild_vanity(guild_id)
    s.setdefault("flagged_members", {})[user_id] = {"vanity": vanity}
    save_guild_vanity(guild_id, s)


def unflag_member(guild_id: str, user_id: str) -> bool:
    s = get_guild_vanity(guild_id)
    flagged = s.get("flagged_members", {})
    if user_id not in flagged:
        return False
    del flagged[user_id]
    s["flagged_members"] = flagged
    save_guild_vanity(guild_id, s)
    return True


def get_ping_role(guild_id: str) -> str | None:
    return get_guild_vanity(guild_id).get("ping_role")


def set_ping_role(guild_id: str, role_id: str | None):
    s = get_guild_vanity(guild_id)
    s["ping_role"] = role_id
    save_guild_vanity(guild_id, s)
