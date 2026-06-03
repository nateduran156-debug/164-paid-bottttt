import aiohttp
from utils.storage import get_roblox_cookie
from config import TAG_MAP


async def get_csrf_token() -> str | None:
    cookie = get_roblox_cookie()
    headers = {}
    if cookie:
        headers["Cookie"] = f".ROBLOSECURITY={cookie}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://auth.roblox.com/v2/logout", headers=headers) as r:
                return r.headers.get("x-csrf-token")
    except Exception:
        return None


async def get_user_by_username(username: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            body = {"usernames": [username], "excludeBannedUsers": False}
            async with session.post("https://users.roblox.com/v1/usernames/users", json=body) as r:
                data = await r.json()
                return data.get("data", [None])[0]
    except Exception:
        return None


async def get_user_groups(user_id: int) -> list:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles") as r:
                data = await r.json()
                return data.get("data", [])
    except Exception:
        return []


async def get_group_info(group_id: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://groups.roblox.com/v1/groups/{group_id}") as r:
                if r.status != 200:
                    return None
                return await r.json()
    except Exception:
        return None


async def get_group_roles(group_id: str) -> list:
    cookie = get_roblox_cookie()
    headers = {}
    if cookie:
        headers["Cookie"] = f".ROBLOSECURITY={cookie}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://groups.roblox.com/v1/groups/{group_id}/roles", headers=headers) as r:
                data = await r.json()
                return data.get("roles", [])
    except Exception:
        return []


async def set_group_rank(group_id: str, user_id: int, role_id: int) -> dict:
    cookie = get_roblox_cookie()
    if not cookie:
        return {"ok": False, "reason": "no cookie set — use /cookie to set one"}
    csrf = await get_csrf_token()
    if not csrf:
        return {"ok": False, "reason": "could not get csrf token"}
    headers = {
        "Cookie": f".ROBLOSECURITY={cookie}",
        "x-csrf-token": csrf,
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"https://groups.roblox.com/v1/groups/{group_id}/users/{user_id}",
                json={"roleId": role_id},
                headers=headers,
            ) as r:
                if not r.ok:
                    data = await r.json()
                    msg = data.get("errors", [{}])[0].get("message", f"status {r.status}")
                    return {"ok": False, "reason": msg}
                return {"ok": True}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


async def accept_join_request(group_id: str, user_id: int) -> dict:
    cookie = get_roblox_cookie()
    if not cookie:
        return {"ok": False, "reason": "no cookie set"}
    csrf = await get_csrf_token()
    if not csrf:
        return {"ok": False, "reason": "could not get csrf token"}
    headers = {
        "Cookie": f".ROBLOSECURITY={cookie}",
        "x-csrf-token": csrf,
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://groups.roblox.com/v1/groups/{group_id}/join-requests/users/{user_id}",
                headers=headers,
            ) as r:
                if not r.ok:
                    data = await r.json()
                    msg = data.get("errors", [{}])[0].get("message", f"status {r.status}")
                    return {"ok": False, "reason": msg}
                return {"ok": True}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


async def get_pending_join_requests(group_id: str) -> list:
    cookie = get_roblox_cookie()
    if not cookie:
        return []
    headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://groups.roblox.com/v1/groups/{group_id}/join-requests?limit=100",
                headers=headers,
            ) as r:
                if not r.ok:
                    return []
                data = await r.json()
                return [
                    {"user_id": e["requester"]["userId"], "username": e["requester"]["username"]}
                    for e in data.get("data", [])
                ]
    except Exception:
        return []


async def get_user_avatar_url(user_id: int) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
            async with session.get(url) as r:
                data = await r.json()
                return data.get("data", [{}])[0].get("imageUrl")
    except Exception:
        return None


async def give_roblox_tag(roblox_username: str, tag_name: str) -> dict:
    tag_key = tag_name.lower()
    tag_info = TAG_MAP.get(tag_key)
    if not tag_info:
        return {"ok": False, "reason": f"unknown tag: {tag_name}"}

    group_id = tag_info["group_id"]
    role_name = tag_info["role_name"]

    user = await get_user_by_username(roblox_username)
    if not user:
        return {"ok": False, "reason": f"could not find roblox user: {roblox_username}"}

    user_id = user["id"]

    # try to accept their join request first in case they sent one
    await accept_join_request(group_id, user_id)

    import asyncio
    await asyncio.sleep(1)

    group_roles = await get_group_roles(group_id)
    matching_role = next(
        (r for r in group_roles if r["name"].lower() == role_name.lower()), None
    )
    if not matching_role:
        return {
            "ok": False,
            "reason": f'role "{role_name}" was not found in group {group_id} — make sure the role name matches exactly',
        }

    return await set_group_rank(group_id, user_id, matching_role["id"])


# presence stuff for the tracker

async def get_user_presence(user_id: int) -> dict | None:
    cookie = get_roblox_cookie()
    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = f".ROBLOSECURITY={cookie}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://presence.roblox.com/v1/presence/users",
                json={"userIds": [user_id]},
                headers=headers,
            ) as r:
                if not r.ok:
                    return None
                data = await r.json()
                presences = data.get("userPresences", [])
                return presences[0] if presences else None
    except Exception:
        return None


async def get_universe_name(universe_id: int) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://games.roblox.com/v1/games?universeIds={universe_id}") as r:
                data = await r.json()
                games = data.get("data", [])
                return games[0].get("name") if games else None
    except Exception:
        return None


async def get_game_name(place_id: int) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe") as r:
                data = await r.json()
                universe_id = data.get("universeId")
                if universe_id:
                    name = await get_universe_name(universe_id)
                    if name:
                        return name
    except Exception:
        pass
    return "Unknown Game"
