import json
import os

DATA_DIR = os.path.join(os.getcwd(), "data")


def read_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def write_json(filename, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_guild(guild_id: str) -> dict:
    all_guilds = read_json("guilds.json")
    return all_guilds.get(guild_id, {})


def set_guild(guild_id: str, data: dict):
    all_guilds = read_json("guilds.json")
    current = all_guilds.get(guild_id, {})
    current.update(data)
    all_guilds[guild_id] = current
    write_json("guilds.json", all_guilds)


def get_points(guild_id: str) -> dict:
    all_points = read_json("points.json")
    return all_points.get(guild_id, {})


def save_points(guild_id: str, pts: dict):
    all_points = read_json("points.json")
    all_points[guild_id] = pts
    write_json("points.json", all_points)


def get_whitelist() -> dict:
    return read_json("whitelist.json")


def set_whitelist(data: dict):
    write_json("whitelist.json", data)


def get_registered() -> dict:
    return read_json("registered.json")


def set_registered(user_id: str, roblox_name: str):
    r = get_registered()
    r[user_id] = roblox_name
    write_json("registered.json", r)


def get_roblox_cookie() -> str | None:
    env_cookie = os.environ.get("ROBLOX_COOKIE")
    if env_cookie:
        return env_cookie
    d = read_json("roblox.json")
    return d.get("cookie")


def set_roblox_cookie(cookie: str):
    write_json("roblox.json", {"cookie": cookie})


def get_prefix(guild_id: str) -> str:
    from config import DEFAULT_PREFIX
    s = get_guild(guild_id)
    return s.get("prefix", DEFAULT_PREFIX)


def member_has_tag_manager_role(member, guild_id: str) -> bool:
    s = get_guild(guild_id)
    roles = list(s.get("tag_manager_roles", []))
    if s.get("tag_manager_role"):
        roles.append(s["tag_manager_role"])
    member_role_ids = {str(r.id) for r in member.roles}
    return bool(set(roles) & member_role_ids)


def member_has_points_role(member, guild_id: str) -> bool:
    s = get_guild(guild_id)
    role_id = s.get("points_role")
    if not role_id:
        return False
    return any(str(r.id) == role_id for r in member.roles)


def member_has_psr(member, guild_id: str) -> bool:
    s = get_guild(guild_id)
    role_id = s.get("points_support_role")
    if not role_id:
        return False
    return any(str(r.id) == role_id for r in member.roles)


def member_has_command_role(member, guild_id: str, cmd: str) -> bool:
    s = get_guild(guild_id)
    command_roles = s.get("command_roles", {})
    allowed = command_roles.get(cmd, [])
    member_role_ids = {str(r.id) for r in member.roles}
    return bool(set(allowed) & member_role_ids)


def has_full_access(interaction, cmd: str = "bot") -> bool:
    member = interaction.user
    guild_id = str(interaction.guild_id) if interaction.guild_id else ""
    if member.guild_permissions.administrator:
        return True
    wl = get_whitelist()
    if str(member.id) in wl.get("bot", []):
        return True
    if str(member.id) in wl.get(cmd, []):
        return True
    if guild_id and member_has_command_role(member, guild_id, cmd):
        return True
    return False
