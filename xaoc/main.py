import os
import sys
import json
import random
import requests
import asyncio
import string
import time
import datetime
import platform
import itertools
import io
import re
import html
import logging

try:
    import discord
    from discord.ext import commands
    from discord.gateway import DiscordWebSocket
    import websockets
    import qrcode
    import pyfiglet
    from colorama import Fore, init
    from gtts import gTTS
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"\n[!] Missing required library: {e.name}")
    print("[!] Please run: python -m pip install -r requirements.txt")
    sys.exit(1)

init(autoreset=True)

logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.getLogger("discord.gateway").setLevel(logging.CRITICAL)
logging.getLogger("discord.client").setLevel(logging.CRITICAL)
logging.getLogger("discord.http").setLevel(logging.CRITICAL)
logging.getLogger("discord.state").setLevel(logging.CRITICAL)

print("""
                                                                   ▄█ ▀▄▄
        ▄▄▄▄░░█▄    ▄▄██▄▄      ▄▄▀ ▄▄          ▄▄     ▄▄██▄▄    ▄███  ▐▒░▄
      ▄▒▒▒▀ ▀▒▒█ ▄█░░░░░░░░░▄▄█░░░ ▄░░░░▄  ▄▒▌  ███▄▄█░░░░░░░░░▄▀░░▒░  ░▒▓░▀
     ▐▓▓▓▌   ▀▓   ▓▓▓▓ ▀▓▓▓▓▀ ▓▓▓▓ ▀▓▓▓▓▓ ░▓▓▌  ░▒░░ ▓▓▓▓ ▀▓▓▓▀▀ ▒▒▒▒▄▒▓▒▀
     ████         ████ ▄█▀▀   ████  █████▐███▌  ▒▒▒▒ ████▄▀▀     ▓▓▓▓▓▓▓▓▓▄
     ░░░░▌        ░░░░        ░░░░  ▐░░░░▐░░░▌  ░░░░ ░░░░  ▄▄▄▄  █████ ████▌
      ▒▒▒▒▄  ▐▄▄  ▒▒▒▒       ▐▒▒▒▒▄ ▐▒▒▒▒ ▓▒▒▒  ▓▒▒▒ ▒▒▒▒▒▄▒▒▒▒▒ ░░░░▌ ▐░░░▌
       ▀▓▓▓▓▓█▓▓▌▀▓▓▓█       ▀▓▓▓▓▓▓▄▓▓▓▌  ▀▀██▄▀▒▓█▀▓▓▓█▓▓█▓▓▓▀▀▒▒▒▒▀ ▒▒▒▒▌
          ▀▀▀▐█▀    ▀█▀        ▀▀▀▀▀▀▀▀▀  ■     ▐▓▓▌   ▀▀██▀▀     ▀▀  ▐▓▓▓▓
                                           ▀█▄▄███▀                  ▄███▀
                                              ▀▀                   ▄█▀▀
""")

# --- FIXED TOKEN LOADING FOR RENDER ---
system = os.environ.get("TOKEN")
if not system:
    print("[!] No token provided. Exiting.")
    sys.exit(1)

token = system
__version__ = "0.8"
start_time = datetime.datetime.now(datetime.timezone.utc)

CONFIG_PATH = "config.json"
DATA_PATH = "data.json"

DEFAULT_CONFIG = {
    "prefix": ".",
    "output": "embed",
    "platform": "desktop",
    "autoreply": {"users": [], "channels": [], "messages": ["hi", "hello", "hey"]},
    "afk": {"enabled": False, "message": "afk"},
    "copycat": {"users": []},
    "remote-users": [],
}

DEFAULT_DATA = {
    "aliases": {}, "ignored": [], "saved": [], "reminders": [], "schedules": [],
    "watches": [], "watchwords": [], "giveaway_sniper": False, "giveaway_entries": [],
    "usernames": {}, "displays": {}, "avatars": {}, "banners": {}, "guildnames": {},
    "ghostfriends": [], "lastpings": {}, "message_history": {}, "snipes": {}, "editsnipes": {},
}

def load_json(path, default_data):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    try:
        with open(path, "r") as f:
            data = json.load(f)
            for k, v in default_data.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return default_data

config = load_json(CONFIG_PATH, DEFAULT_CONFIG)
data = load_json(DATA_PATH, DEFAULT_DATA)

prefix = config.get("prefix", ".")
message_generator = itertools.cycle(config["autoreply"]["messages"])

PLATFORMS = {
    "mobile": {
        "os": "Android", "browser": "Discord Android", "device": "emu64x",
        "system_locale": "en-US", "has_client_mods": False,
        "client_version": "267.0 - rn", "release_channel": "stable",
        "browser_version": "", "os_version": "33",
        "referrer": "", "referring_domain": "",
        "referrer_current": "", "referring_domain_current": "",
        "client_build_number": 267200, "client_event_source": None,
        "browser_user_agent": "Discord-Android/267020;RNA",
    },
    "desktop": {
        "os": "Windows", "browser": "Discord Client", "device": "",
        "system_locale": "en-US", "has_client_mods": False,
        "client_version": "0.0.305", "release_channel": "stable",
        "browser_version": "22.0.0", "os_version": "10",
        "referrer": "", "referring_domain": "",
        "referrer_current": "", "referring_domain_current": "",
        "client_build_number": 289011, "client_event_source": None,
        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/120.0.0.0 Electron/28.0.0 Safari/537.36",
    },
    "web": {
        "os": "Windows", "browser": "Chrome", "device": "",
        "system_locale": "en-US", "has_client_mods": False,
        "client_version": "0.0.305", "release_channel": "stable",
        "browser_version": "120.0.0.0", "os_version": "10",
        "referrer": "", "referring_domain": "",
        "referrer_current": "", "referring_domain_current": "",
        "client_build_number": 289011, "client_event_source": None,
        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
}

spoofplat = config.get("platform", "desktop")
realidentify = None

async def spoofident(self):
    global realidentify
    if realidentify is None:
        realidentify = DiscordWebSocket.identify
    props = PLATFORMS.get(spoofplat, PLATFORMS["desktop"])
    self._super_properties = dict(props)
    return await realidentify(self)

def installpatch():
    global realidentify
    if DiscordWebSocket.identify is spoofident:
        return
    realidentify = DiscordWebSocket.identify
    DiscordWebSocket.identify = spoofident

installpatch()

def save_config():
    with open(CONFIG_PATH, "w") as file:
        json.dump(config, file, indent=4)

def save_data():
    with open(DATA_PATH, "w") as file:
        json.dump(data, file, indent=4)

def apihdrs():
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

def ago(ts):
    d = int(time.time() - ts)
    if d < 60:
        return f"{d}s ago"
    if d < 3600:
        return f"{d // 60}m ago"
    if d < 86400:
        return f"{d // 3600}h ago"
    return f"{d // 86400}d ago"

def savemsg(uid, entry, cap=500):
    uid = str(uid)
    if uid not in data["message_history"]:
        data["message_history"][uid] = []
    data["message_history"][uid].append(entry)
    if len(data["message_history"][uid]) > cap:
        data["message_history"][uid] = data["message_history"][uid][-cap:]

def savesnipe(channel_id, entry, cap=5):
    cid = str(channel_id)
    if cid not in data["snipes"]:
        data["snipes"][cid] = []
    data["snipes"][cid].append(entry)
    if len(data["snipes"][cid]) > cap:
        data["snipes"][cid] = data["snipes"][cid][-cap:]

def saveedit(channel_id, entry, cap=5):
    cid = str(channel_id)
    if cid not in data["editsnipes"]:
        data["editsnipes"][cid] = []
    data["editsnipes"][cid].append(entry)
    if len(data["editsnipes"][cid]) > cap:
        data["editsnipes"][cid] = data["editsnipes"][cid][-cap:]

mimictargets = {}
reactchannels = {}
reactemojis = {}
nickjobs = {}
gclocks = {}
deletetimers = {}
followers = {}
spinjobs = {}
calltrapids = set()
rpcstate = {"name": "", "type": "playing"}
RPC_CLIENT_ID = "1081629665543209020"
rpctask = None
remindtask = None
ghosttask = None
snipestate = {"nitro": {"enabled": config.get("sniper_nitro", True), "ignore_invalid": False}}
snipehook = config.get("sniper_webhook", "")
snipehistory = []
seencodes = set()
NITRO_RE = re.compile(r"(?:discord\.gift/|discord\.com/gifts/)([a-zA-Z0-9]{16,24})")

SOCIAL_GIFS = {
    "hug": ["https://media.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif"],
    "kiss": ["https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif"],
    "kill": ["https://media.giphy.com/media/3o7aD2d7hy9ktXNDP2/giphy.gif"],
    "slap": ["https://media.giphy.com/media/Gf3AUz3eBNbTW/giphy.gif"],
    "pat": ["https://media.giphy.com/media/ARSp9T7wwxNcs/giphy.gif"],
    "bonk": ["https://media.giphy.com/media/W0FdFcNJb9l8A/giphy.gif"],
    "cuddle": ["https://media.giphy.com/media/3bqtLDeiDtwhq/giphy.gif"],
}

def selfbot_menu(bot):
    print(f"\n{Fore.RESET}Xaoc\n")
    print(f"""
    https://discord.gg/v2QwrUPUzk
 Linked: \x1b[38;5;127m {bot.user} \x1b[38;5;255m
 Prefix: \x1b[38;5;127m {prefix} \x1b[38;5;255m
 Platform: \x1b[38;5;127m {spoofplat} \x1b[38;5;255m
 Version: \x1b[38;5;48m {__version__} \x1b[38;5;255m
 """)

# --- FIXED: ADDED INTENTS ---
bot = commands.Bot(command_prefix=prefix, self_bot=True, help_command=None, intents=discord.Intents.all())

async def remindloop():
    while True:
        try:
            now = time.time()
            changed = False
            for r in list(data["reminders"]):
                if r["fire_at"] <= now:
                    try:
                        u = await bot.fetch_user(r["user_id"])
                        await u.send(f"reminder: {r['note']}")
                    except Exception:
                        pass
                    data["reminders"].remove(r)
                    changed = True
            for s in list(data["schedules"]):
                if s["fire_at"] <= now and not s.get("fired"):
                    try:
                        ch = bot.get_channel(int(s["channel_id"]))
                        if ch:
                            await ch.send(s["message"])
                    except Exception:
                        pass
                    s["fired"] = True
                    changed = True
            data["schedules"] = [x for x in data["schedules"] if not x.get("fired")]
            if changed:
                save_data()
            await asyncio.sleep(20)
        except Exception:
            await asyncio.sleep(30)

async def ghostloop():
    known = {}
    while True:
        try:
            r = requests.get("https://discord.com/api/v10/users/@me/relationships", headers=apihdrs(), timeout=10)
            rels = r.json()
            current = {rel["id"]: rel for rel in rels if rel.get("type") == 3}
            for uid, rel in known.items():
                if uid not in current:
                    still_friend = any(x["id"] == uid and x.get("type") == 1 for x in rels)
                    if not still_friend:
                        u = rel.get("user", {})
                        data["ghostfriends"].append({"id": uid, "username": u.get("username", "unknown"), "display": u.get("global_name"), "time": time.time()})
                        data["ghostfriends"] = data["ghostfriends"][-200:]
                        save_data()
            known = current
            await asyncio.sleep(60)
        except Exception:
            await asyncio.sleep(120)

async def rpcpush():
    if not rpcstate.get("name"):
        return False
    type_map = {"playing": 0, "streaming": 1, "listening": 2, "watching": 3, "competing": 5}
    typ = rpcstate.get("type", "playing")
    payload = {"name": rpcstate["name"], "type": type_map.get(typ, 0), "application_id": RPC_CLIENT_ID}
    if typ == "streaming":
        payload["url"] = "https://twitch.tv/discord"
    try:
        await bot.ws.send_as_json({"op": 3, "d": {"since": 0, "activities": [payload], "status": "online", "afk": False}})
        return True
    except Exception:
        return False

async def rpcloop():
    while True:
        await asyncio.sleep(120)
        if rpcstate.get("name"):
            await rpcpush()

@bot.event
async def on_ready():
    global remindtask, ghosttask, rpctask
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(f"Xaoc v{__version__}")
        except Exception:
            pass
    selfbot_menu(bot)
    if remindtask is None or remindtask.done(): remindtask = bot.loop.create_task(remindloop())
    if ghosttask is None or ghosttask.done(): ghosttask = bot.loop.create_task(ghostloop())
    if rpctask is None or rpctask.done(): rpctask = bot.loop.create_task(rpcloop())

@bot.event
async def on_message(message):
    if str(message.author.id) in data["ignored"]: return
    if message.author != bot.user and message.content:
        savemsg(message.author.id, {"content": message.content[:500], "channel": str(message.channel), "guild": message.guild.name if message.guild else "DM", "message_id": str(message.id), "time": time.time()})
    
    if message.content.startswith(config["prefix"]):
        rest = message.content[len(config["prefix"]):]
        parts = rest.split(maxsplit=1)
        if parts and parts[0].lower() in data["aliases"]:
            target = data["aliases"][parts[0].lower()]
            new_content = config["prefix"] + target
            if len(parts) > 1: new_content += " " + parts[1]
            try: message.content = new_content
            except Exception: pass

    if data["giveaway_sniper"] and message.author != bot.user:
        low = message.content.lower()
        if "giveaway" in low or "🎉" in message.content:
            try:
                await message.add_reaction("🎉")
                data["giveaway_entries"].append({"message_id": str(message.id), "channel": str(message.channel), "author": str(message.author), "content": message.content[:120], "time": time.time()})
                data["giveaway_entries"] = data["giveaway_entries"][-100:]
                save_data()
            except Exception: pass

    if data["watchwords"] and message.author != bot.user and message.content:
        for w in list(data["watchwords"]):
            if w["word"].lower() in message.content.lower():
                try:
                    u = await bot.fetch_user(w["user_id"])
                    gid = message.guild.id if message.guild else "@me"
                    await u.send(f"watchword `{w['word']}` from {message.author} in {message.channel}\nhttps://discord.com/channels/{gid}/{message.channel.id}/{message.id}")
                except Exception: pass

    if message.author.id in config["copycat"]["users"]:
        if message.content.startswith(config["prefix"]): await message.reply(message.content[len(config["prefix"]):])
        else: await message.reply(message.content)

    if config["afk"]["enabled"]:
        if bot.user in message.mentions and message.author != bot.user:
            await message.reply(config["afk"]["message"])
            return
        elif isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
            await message.reply(config["afk"]["message"])
            return

    if message.author != bot.user:
        if str(message.author.id) in config["autoreply"]["users"]:
            await message.reply(next(message_generator))
            return
        elif str(message.channel.id) in config["autoreply"]["channels"]:
            await message.reply(next(message_generator))
            return

    if bot.user in message.mentions and message.author != bot.user:
        data["lastpings"][str(message.author.id)] = {"content": message.content[:200], "time": time.time(), "channel": str(message.channel), "message_id": str(message.id), "guild": message.guild.name if message.guild else "DM"}
        save_data()

    if (message.guild and message.guild.id == 1469040923538227407 and message.content.startswith(config["prefix"])):
        await message.delete()
        await message.channel.send("SB commands are not allowed here.", delete_after=5)
        return

    if message.author != bot.user and str(message.author.id) not in config["remote-users"]: return
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    savesnipe(message.channel.id, {"author": str(message.author), "author_id": str(message.author.id), "content": message.content or "*[no text content]*", "message_id": str(message.id), "time": time.time()})
    save_data()

@bot.event
async def on_message_edit(before, after):
    if before.content != after.content:
        saveedit(before.channel.id, {"author": str(before.author), "author_id": str(before.author.id), "before": before.content, "after": after.content, "message_id": str(before.id), "time": time.time()})
        save_data()

@bot.event
async def on_user_update(before, after):
    try:
        uid = str(after.id)
        if before.name != after.name:
            data["usernames"].setdefault(uid, []).append({"old": before.name, "new": after.name, "time": time.time()})
            data["usernames"][uid] = data["usernames"][uid][-50:]
        if getattr(before, "global_name", None) != getattr(after, "global_name", None):
            data["displays"].setdefault(uid, []).append({"old": getattr(before, "global_name", None), "new": getattr(after, "global_name", None), "time": time.time()})
            data["displays"][uid] = data["displays"][uid][-50:]
        save_data()
    except Exception: pass

@bot.event
async def on_guild_update(before, after):
    try:
        if before.name != after.name:
            gid = str(after.id)
            data["guildnames"].setdefault(gid, []).append({"old": before.name, "new": after.name, "time": time.time()})
            data["guildnames"][gid] = data["guildnames"][gid][-50:]
            save_data()
    except Exception: pass

@bot.event
async def on_presence_update(before, after):
    for w in data["watches"]:
        if str(after.id) == str(w["target_id"]) and str(before.status) == "offline" and str(after.status) != "offline":
            try:
                u = await bot.fetch_user(w["user_id"])
                await u.send(f"watch: {after.name} is now {after.status}")
            except Exception: pass

@bot.event
async def on_voice_state_update(member, before, after):
    for user_id, target_id in list(followers.items()):
        if member.id == target_id and before.channel != after.channel and after.channel:
            try:
                me = member.guild.get_member(bot.user.id)
                if me and me.voice and me.voice.channel:
                    await me.move_to(after.channel)
            except Exception: pass

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return

@bot.listen("on_message")
async def mimicwatch(message):
    if message.author.id in mimictargets:
        if time.time() > mimictargets[message.author.id]:
            del mimictargets[message.author.id]
            return
        if message.content:
            try: await message.channel.send(message.content)
            except Exception: pass

@bot.listen("on_message")
async def reactwatch(message):
    if message.channel.id in reactchannels and message.author != bot.user:
        emoji = reactemojis.get(message.channel.id)
        if emoji:
            try: await message.add_reaction(emoji)
            except Exception: pass

@bot.listen("on_message")
async def deletewatch(message):
    if message.channel.id in deletetimers and message.author == bot.user:
        try:
            await asyncio.sleep(deletetimers[message.channel.id])
            await message.delete()
        except Exception: pass

@bot.listen("on_message")
async def snipewatch(message):
    if message.author == bot.user or str(message.author.id) in data["ignored"] or not snipestate["nitro"]["enabled"]: return
    m = NITRO_RE.search(message.content)
    if not m: return
    code = m.group(1)
    if code in seencodes: return
    seencodes.add(code)
    try:
        r = requests.post(f"https://discord.com/api/v10/entitlements/gift-codes/{code}/redeem", headers=apihdrs(), json={}, timeout=15)
        status = r.status_code
    except Exception: status = None
    snipehistory.append({"type": "nitro", "code": code, "author": str(message.author), "channel": str(message.channel), "status": status, "time": time.time()})
    snipehistory[:] = snipehistory[-100:]
    if snipehook and (status == 200 or not snipestate["nitro"]["ignore_invalid"]):
        try: requests.post(snipehook, json={"embeds": [{"title": f"nitro {'sniped' if status == 200 else 'failed'}", "description": f"code: `{code}`\nfrom: {message.author}\nstatus: `{status}`\n{message.jump_url}", "color": 0x00FF00 if status == 200 else 0xFF0000}]}, timeout=10)
        except Exception: pass

@bot.listen("on_socket_response")
async def callwatch(payload):
    try:
        if payload.get("t") != "VOICE_STATE_UPDATE": return
        d = payload.get("d") or {}
        if str(d.get("user_id")) != str(bot.user.id) or not d.get("channel_id"): return
        channel = bot.get_channel(int(d["channel_id"]))
        if not channel or not isinstance(channel, discord.DMChannel) or bot.user.id not in calltrapids: return
        await bot.ws.voice_state(None, d["channel_id"], self_mute=False, self_deaf=False)
        await asyncio.sleep(1.0)
        await bot.ws.voice_state(None, None, self_mute=False, self_deaf=False)
    except Exception: pass

HELP_DATA = {
    "admin": [
        ("prefix", "<prefix>", "change the bot prefix"), ("remoteuser", "ADD|REMOVE <@user>", "authorize a user"),
        ("whitelist", "<@user>", "let another user run your commands"), ("unwhitelist", "<@user>", "remove from whitelist"),
        ("autoreply", "ON|OFF [@user]", "toggle automatic replies"), ("afk", "ON|OFF [message]", "toggle afk auto-message"),
        ("copycat", "ON|OFF <@user>", "mirror a user's messages"), ("customstatus", "<text>", "change your custom status"),
        ("autodelete", "[seconds]", "auto-delete your messages here"), ("ignore", "<@user>", "ignore a user completely"),
        ("unignore", "<@user>", "stop ignoring a user"), ("ignorelist", "", "show ignored users"),
        ("alias", "<name> <command>", "create a shortcut"), ("unalias", "<name>", "remove a shortcut"),
        ("aliases", "", "list all aliases"), ("status", "online|idle|dnd|invisible", "change your status"),
        ("rotation", "[seconds] online|idle or rpc a|b or custom a|b", "rotate presence"), ("platform", "mobile|desktop|web|ios|xbox", "spoof client platform"),
        ("rpc", "<name> or <type> <name>", "set your activity"), ("clone", "<source_id> <home_id>", "clone a server into another"),
        ("stopall", "", "stop every running task"), ("config", "", "view current bot configuration"),
        ("uptime", "", "how long the bot has been running"), ("ping", "", "bot latency"), ("shutdown", "", "stop the selfbot"),
    ],
    "animated": [
        ("airplane", "", "animated sequence"), ("faketype", "[seconds]", "appear as typing for n seconds"),
        ("nickcycle", "<name|name|name>", "cycle your nickname through a list"), ("timer", "<duration>", "visible countdown in channel"),
    ],
    "text": [
        ("ascii", "<text>", "convert text to ascii art"), ("leetspeak", "<text>", "convert text to l33t"), ("reverse", "<text>", "reverse a message"),
        ("edit", "<message>", "move the (edited) tag"), ("hidemention", "<message>", "hide text behind a mention"), ("zalgo", "<text>", "corrupted text"),
        ("aesthetic", "<text>", "fullwidth aesthetic text"), ("bubble", "<text>", "bubble text"), ("morse", "<text>", "encode to morse"),
        ("binary", "<text>", "encode to binary"), ("spoiler", "<text>", "every char in a spoiler"), ("shrug", "", "shrug emoji"),
        ("tableflip", "", "flip a table"), ("unflip", "", "put the table back"), ("blank", "", "send a blank message"),
        ("chatbypass", "<text>", "bold unicode text"), ("regional", "<text>", "emoji letter text"), ("randomcase", "<text>", "random CaSe"),
        ("animate", "<text>", "type text out char by char"), ("lmgtfy", "<query>", "let me google that for you"), ("json", "<code>", "json codeblock"),
        ("python", "<code>", "python codeblock"), ("js", "<code>", "javascript codeblock"), ("html", "<code>", "html codeblock"),
        ("css", "<code>", "css codeblock"), ("java", "<code>", "java codeblock"), ("c", "<code>", "c codeblock"),
        ("cpp", "<code>", "cpp codeblock"), ("php", "<code>", "php codeblock"), ("lua", "<code>", "lua codeblock"),
    ],
    "image": [
        ("avatar", "[@user]", "user profile picture"), ("userbanner", "[@user]", "user banner"), ("servericon", "[guild_id]", "server icon"),
        ("serverbanner", "[guild_id]", "server banner"), ("usericon", "<@user>", "user pfp (link)"), ("guildicon", "", "server icon (link)"),
        ("guildbanner", "", "server banner (link)"), ("qr", "[text]", "generate a qr code"), ("pfpglitch", "<@user>", "glitch filter on a pfp"),
        ("pfppixelate", "<@user> [size]", "pixelate a pfp"), ("lovecalc", "<@a> <@b>", "compatibility calculator"), ("cat", "", "random cat"),
        ("dog", "", "random dog"), ("bird", "", "random bird"), ("fox", "", "random fox"), ("raccoon", "", "random raccoon"),
        ("achievement", "<text>", "minecraft achievement"), ("challenge", "<text>", "minecraft challenge"), ("fakechat", "<@user> <msg>", "fake discord message"),
    ],
    "social": [
        ("hug", "[@user]", "hug a user"), ("kiss", "[@user]", "kiss a user"), ("kill", "[@user]", "kill a user"),
        ("slap", "[@user]", "slap a user"), ("pat", "[@user]", "pat a user"), ("bonk", "[@user]", "bonk a user"), ("cuddle", "[@user]", "cuddle a user"),
    ],
    "troll": [
        ("ghostping", "<@user> [count]", "ping then delete"), ("mimic", "<@user> [minutes]", "copy a user"), ("autoreact", "[emoji]", "auto-react to every message"),
        ("msgspam", "[count] <message>", "spam current channel"), ("dmspam", "<@user> [count] <message>", "spam a user's dms"), ("reactspam", "[emoji...] [msg_id]", "react with many emojis"),
        ("trap", "<@user>", "keep a user in a group dm"), ("callspam", "<@user> [count]", "ring a user then hang up repeatedly"), ("callflood", "<@user> [count]", "fast ring/hangup loop"),
        ("calltrap", "", "auto-answer incoming calls then hang up"), ("tokenflood", "[count]", "spam fake tokens"), ("nitroflood", "[count]", "spam fake nitro links"),
        ("dick", "[@user]", "size calculator"), ("gcname", "<name>", "change group chat name"), ("antigc", "", "leave all group chats"),
    ],
    "fun": [
        ("minesweeper", "[size]", "text minesweeper"), ("8ball", "<question>", "magic 8ball"), ("coinflip", "", "flip a coin"),
        ("dice", "[sides]", "roll dice"), ("rps", "<rock|paper|scissors>", "rock paper scissors"),
    ],
    "tools": [
        ("geoip", "<ip>", "geolocate an ip"), ("pingweb", "<url>", "check a website's status"), ("tts", "<message>", "text to speech audio"),
        ("tokeninfo", "<token>", "scrape info from a token"), ("gentoken", "[user]", "generate a fake token"), ("nitro", "", "generate a fake nitro link"),
        ("whremove", "<webhook>", "delete a webhook"), ("hypesquad", "<house>", "change hypesquad house"), ("info", "", "show your account info"),
        ("serverinfo", "", "server information"), ("fetchmembers", "", "export a server's member list"), ("firstmessage", "", "link to the first message"),
        ("lastmessage", "", "link to the newest message"), ("massreact", "<emoji> [count]", "react to newest n messages"), ("react", "<emoji> [msg_id]", "react to a message"),
        ("unreact", "<emoji> [msg_id]", "remove a reaction"), ("nickall", "<name>", "change nickname across every server"), ("purgeuser", "<@user> [count]", "delete messages from a user"),
        ("check", "<@user>", "check a user's account"), ("count", "[#channel]", "count messages in a channel"), ("define", "<word>", "define a word"),
        ("languages", "", "list language codes"), ("joinvc", "", "join your voice channel"), ("leavevc", "", "leave voice channel"),
        ("joinserver", "<invite>", "join a server from an invite"), ("weather", "<city>", "get the weather"), ("translate", "<lang> <text>", "translate text"),
        ("price", "<symbol>", "crypto price"), ("news", "[topic]", "top news headlines"), ("ytsearch", "<query>", "top youtube result"),
        ("github", "<username>", "github user info"), ("remind", "<duration> <note>", "dm reminder"), ("reminders", "", "list pending reminders"),
        ("schedule", "<HH:MM> <#channel> <msg>", "schedule a message"), ("schedules", "", "list scheduled messages"), ("watch", "<@user>", "dm you when they come online"),
        ("unwatch", "<@user>", "stop watching"), ("watchlist", "", "list watched users"), ("watchword", "<word>", "ping when anyone says it"),
        ("unwatchword", "<word>", "remove a watchword"), ("watchwords", "", "list watchwords"), ("backupdms", "<@user>", "dump dm history with someone"),
        ("saved", "add|list|search|random", "bookmark messages"), ("vcecho", "<@user>", "follow a user between voice channels"), ("export", "[#channel]", "export channel to html"),
        ("specs", "", "your computer specs"), ("clearcache", "", "clear the cache folder"), ("inviteinfo", "<invite>", "info about an invite"),
        ("hiddenchannels", "", "list channels you can't see"), ("tickets", "", "list ticket channels"), ("dmpurge", "<amount> <user_id>", "purge a dm by user id"),
    ],
    "tracking": [
        ("avatars", "[@user]", "avatar change history"), ("banners", "[@user]", "banner change history"), ("displays", "[@user]", "display name change history"),
        ("usernames", "[@user]", "username change history"), ("editsnipe", "[index]", "recent edited messages"), ("snipe", "[index]", "recent deleted messages"),
        ("ghostfriends", "", "cancelled friend requests"), ("guildnames", "[guild_id]", "guild name change history"), ("guilds", "[@user]", "your guilds or mutual servers"),
        ("history", "<@user> [page]", "message history of a user"), ("lastping", "[@user]", "recent mentions of you"),
    ],
    "sniper": [
        ("snipers", "", "list all snipers"), ("sniperstatus", "<name>", "check a sniper's status"), ("nitrosniper", "[on|off]", "toggle nitro sniper"),
        ("ignoreinvalidcodes", "<name>", "toggle ignore invalid codes"), ("sniperlog", "", "recent snipes"), ("sniperwebhook", "<url|clear>", "set notification webhook"),
        ("giveawaysniper", "on|off", "auto-enter giveaways"), ("giveawaylist", "", "show recent giveaway entries"),
    ],
    "abuse": [
        ("spam", "<amount> <message>", "spam a message n times"), ("quickdelete", "<message>", "send then delete after 2s"), ("dmall", "<message>", "dm every member in the server"),
        ("sendall", "<message>", "send a message to every channel"), ("clear", "", "clear the channel view"), ("purge", "<amount>", "delete n messages"),
        ("cleardm", "<amount>", "delete n of your messages in a dm"), ("massdm", "<message>", "message all your friends"), ("massdm_server", "<message>", "dm every member in this server"),
        ("massdm_guild", "<guild_id> <message>", "dm every member in a server by id"), ("massmention", "<message>", "mention every member"), ("invitespam", "[count]", "create n invites to the server"),
        ("friendspam", "<@user> [count]", "spam friend requests"), ("leaveguilds", "[whitelist_ids...]", "leave every server except whitelisted"), ("leave", "<guild_id>", "leave a server by id"),
        ("closedms", "", "close all your dms"), ("muteall", "", "mute all servers"),
    ],
    "nuke": [
        ("terminate", "[name]", "delete all channels, roles, emojis, then rename"), ("nukechannel", "", "delete and recreate current channel"),
        ("guildrename", "<name>", "rename the server"), ("channelspam", "[count] [name]", "create n channels"), ("channeldelete", "", "delete every channel"),
        ("channelrename", "[name]", "rename every channel"), ("channelwebhook", "[count] [name]", "create n webhooks"), ("rolecreate", "[count] [name]", "create n roles"),
        ("roledelete", "", "delete every role below yours"), ("roleadmin", "<@user>", "give admin to a user"), ("emojidelete", "", "delete every emoji"),
        ("serverrename", "[name]", "rename the server"), ("banall", "[reason]", "ban every member you can"), ("massban", "[reason]", "ban every member you can"),
        ("unbanall", "", "unban every banned user"), ("kickall", "[reason]", "kick every member you can"), ("everyone", "[message]", "ping @everyone in every channel"),
        ("here", "[message]", "ping @here in every channel"), ("autoapprove", "ON|OFF", "auto-approve pending members"),
    ],
}

CATEGORY_BLURB = {
    "admin": "Administration", "animated": "Animated messages", "text": "Text messages", "image": "Image commands",
    "social": "Social interactions", "troll": "Trolling options", "fun": "Funny commands", "tools": "General tools",
    "tracking": "Tracking", "sniper": "Snipers", "abuse": "Abusive commands", "nuke": "Server nuking",
}

def cmdline(name, args, desc):
    if args: return f"`[ .{name} {args} ]` {desc}"
    return f"`[ .{name} ]` {desc}"

async def sendcat(ctx, category):
    category = category.lower()
    cmds = HELP_DATA.get(category)
    if not cmds:
        await ctx.send(f"`[ x ]` unknown category `{category}`", delete_after=5)
        return
    header = f"`[ {category} ]`\n\n<> = required, [] = optional\n\n"
    lines = [cmdline(name, args, desc) for name, args, desc in cmds]
    chunks = []
    current = header
    for line in lines:
        if len(current) + len(line) + 1 > 1900:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current.strip(): chunks.append(current)
    for chunk in chunks:
        try:
            await ctx.send(chunk)
            await asyncio.sleep(0.4)
        except Exception: pass

@bot.command(aliases=["h"])
async def help(ctx, category: str = None):
    await ctx.message.delete()
    if category:
        await sendcat(ctx, category)
        return
    lines = ["`[ Xaoc ]`", "", "<> = required, [] = optional", "", "`[ .help ]` Shows this menu"]
    for cat in HELP_DATA.keys():
        lines.append(f"`[ .{cat} ]` {CATEGORY_BLURB[cat]}")
    await ctx.send("\n".join(lines))

CATEGORY_SHORTCUTS = ["admin", "animated", "text", "image", "social", "troll", "fun", "tools", "tracking", "abuse", "nuke"]

def makecatcmd(cat_name):
    async def run(ctx):
        await ctx.message.delete()
        await sendcat(ctx, cat_name)
    run.__name__ = cat_name
    return run

for c in CATEGORY_SHORTCUTS:
    bot.command(name=c)(makecatcmd(c))

@bot.command()
async def ignore(ctx, target: discord.User = None):
    await ctx.message.delete()
    if target and str(target.id) not in data["ignored"]:
        data["ignored"].append(str(target.id))
        save_data()

@bot.command()
async def unignore(ctx, target: discord.User = None):
    await ctx.message.delete()
    if target and str(target.id) in data["ignored"]:
        data["ignored"].remove(str(target.id))
        save_data()

@bot.command()
async def ignorelist(ctx):
    await ctx.message.delete()
    if not data["ignored"]:
        await ctx.send("`[ ignorelist ]` empty", delete_after=5)
        return
    lines = [f"`[ ignorelist ]` ({len(data['ignored'])})"]
    for uid in data["ignored"]:
        try:
            u = await bot.fetch_user(int(uid))
            lines.append(f"> `{u.name}` ({uid})")
        except Exception:
            lines.append(f"> `{uid}`")
    await ctx.send("\n".join(lines), delete_after=20)

@bot.command()
async def alias(ctx, name: str = None, *, target: str = None):
    await ctx.message.delete()
    if name and target:
        data["aliases"][name.lower()] = target
        save_data()

@bot.command()
async def unalias(ctx, name: str = None):
    await ctx.message.delete()
    if name:
        data["aliases"].pop(name.lower(), None)
        save_data()

@bot.command()
async def aliases(ctx):
    await ctx.message.delete()
    if not data["aliases"]:
        await ctx.send("`[ aliases ]` empty", delete_after=5)
        return
    lines = [f"`[ aliases ]` ({len(data['aliases'])})"]
    for k, v in data["aliases"].items():
        lines.append(f"> `.{k}` to `.{v}`")
    await ctx.send("\n".join(lines), delete_after=20)

@bot.command(aliases=["rotate"])
async def rotation(ctx, *, args: str = None):
    await ctx.message.delete()
    key = f"rot_{ctx.author.id}"
    if not args:
        running = spinjobs.get(key)
        if running:
            await ctx.send(f"`[ rotation ]` running `{running['type']}` every {running['interval']}s:\n> {' | '.join(running['items'])}")
        else:
            await ctx.send("`[ rotation ]` nothing running\n> `.rotation online|idle|dnd`\n> `.rotation rpc test1|test2`\n> `.rotation custom brb|afk`\n> `.rotation 5 online|idle` (with seconds)\n> `.rotation off`", delete_after=25)
        return
    if args.strip().lower() == "off":
        old = spinjobs.pop(key, None)
        if old: old["task"].cancel()
        await ctx.send("`[ rotation ]` stopped", delete_after=5)
        return
    raw = args.strip()
    type_ = None
    low = raw.lower()
    if low.startswith("rpc "):
        type_ = "rpc"
        raw = raw[4:].strip()
    elif low.startswith("custom "):
        type_ = "custom"
        raw = raw[7:].strip()
    interval = 30
    tokens = raw.split(maxsplit=1)
    if tokens and tokens[0].isdigit():
        interval = max(2, int(tokens[0]))
        raw = tokens[1] if len(tokens) > 1 else ""
    parts = [x.strip() for x in raw.split("|") if x.strip()]
    if not parts: return
    status_set = {"online", "idle", "dnd", "invisible"}
    if type_ is None:
        if all(p.lower() in status_set for p in parts): type_ = "status"
        else: type_ = "rpc"
    if type_ == "status":
        values = [p.lower() for p in parts if p.lower() in status_set]
        if not values: return
    elif type_ == "rpc":
        values = []
        for it in parts:
            if ":" in it:
                t, n = it.split(":", 1)
                t = t.lower().strip()
                if t in ("playing", "streaming", "listening", "watching", "competing"): values.append((t, n.strip()))
            else: values.append(("playing", it))
        if not values: return
    else: values = parts
    old = spinjobs.pop(key, None)
    if old: old["task"].cancel()
    type_map = {"playing": 0, "streaming": 1, "listening": 2, "watching": 3, "competing": 5}

    async def loop():
        i = 0
        try:
            while True:
                v = values[i % len(values)]
                try:
                    if type_ == "status": await bot.change_presence(status=getattr(discord.Status, v))
                    elif type_ == "rpc":
                        t, n = v
                        payload = {"name": n, "type": type_map.get(t, 0), "application_id": RPC_CLIENT_ID}
                        if t == "streaming": payload["url"] = "https://twitch.tv/discord"
                        await bot.ws.send_as_json({"op": 3, "d": {"since": 0, "activities": [payload], "status": "online", "afk": False}})
                    elif type_ == "custom": await bot.change_presence(activity=discord.CustomActivity(name=v))
                except Exception: pass
                i += 1
                await asyncio.sleep(interval)
        except asyncio.CancelledError: pass

    spinjobs[key] = {"type": type_, "items": parts, "interval": interval, "task": bot.loop.create_task(loop())}
    await ctx.send(f"`[ rotation ]` {type_} every {interval}s ({len(values)} item(s))", delete_after=5)

@bot.command(name="platform")
async def platform_cmd(ctx, which: str = None):
    await ctx.message.delete()
    global spoofplat
    if not which:
        valid = " | ".join(sorted(PLATFORMS.keys()))
        await ctx.send(f"`[ platform ]`\n`[ .platform {valid} ]`", delete_after=15)
        return
    which = which.lower()
    if which not in PLATFORMS:
        await ctx.send(f"`[ x ]` invalid `{which}`", delete_after=5)
        return
    spoofplat = which
    config["platform"] = which
    save_config()
    await ctx.send(f"`[ platform ]` set to `{which}`, reconnecting...", delete_after=3)
    await asyncio.sleep(1)
    try: await bot.close()
    except Exception: pass

@bot.command()
async def rpc(ctx, *, args: str = None):
    await ctx.message.delete()
    if not args:
        if rpcstate.get("name"): await ctx.send(f"`[ rpc ]` {rpcstate['name']}\n> type: `{rpcstate.get('type', 'playing')}`")
        else: await ctx.send("`[ rpc ]` usage:\n> `.rpc <name>` (playing)\n> `.rpc listening <name>`\n> `.rpc watching <name>`\n> `.rpc competing <name>`\n> `.rpc off`", delete_after=15)
        return
    if args.strip().lower() == "off":
        rpcstate["name"] = ""
        rpcstate["type"] = "playing"
        try: await bot.ws.send_as_json({"op": 3, "d": {"since": 0, "activities": [], "status": "online", "afk": False}})
        except Exception: pass
        await ctx.send("`[ rpc ]` cleared", delete_after=5)
        return
    tokens = args.split(maxsplit=1)
    valid_types = ("playing", "listening", "watching", "competing", "streaming")
    if len(tokens) == 2 and tokens[0].lower() in valid_types:
        typ = tokens[0].lower()
        name = tokens[1]
    else:
        typ = "playing"
        name = args
    rpcstate["name"] = name
    rpcstate["type"] = typ
    if await rpcpush(): await ctx.send(f"`[ rpc ]` {typ} `{name}`", delete_after=5)
    else: await ctx.send("`[ x ]` failed to push rpc", delete_after=5)

@bot.command()
async def snipers(ctx):
    await ctx.message.delete()
    lines = ["`[ snipers ]`"]
    for name, state in snipestate.items(): lines.append(f"> `{name}`: {'enabled' if state['enabled'] else 'disabled'}")
    lines.append(f"> `giveawaysniper`: {'enabled' if data['giveaway_sniper'] else 'disabled'}")
    await ctx.send("\n".join(lines))

@bot.command()
async def sniperstatus(ctx, name: str = None):
    await ctx.message.delete()
    if not name: return
    name = name.lower()
    if name == "giveaway":
        await ctx.send(f"`[ sniperstatus ]` giveaway: {'enabled' if data['giveaway_sniper'] else 'disabled'}")
        return
    if name in snipestate:
        s = snipestate[name]
        await ctx.send(f"`[ sniperstatus ]` {name}: {'enabled' if s['enabled'] else 'disabled'}")

@bot.command(aliases=["nsniper"])
async def nitrosniper(ctx, state: str = None):
    await ctx.message.delete()
    s = snipestate["nitro"]
    if state and state.lower() not in ("on", "off"): return
    if state: s["enabled"] = state.lower() == "on"
    else: s["enabled"] = not s["enabled"]
    config["sniper_nitro"] = s["enabled"]
    save_config()
    await ctx.send(f"> nitro sniper `{'on' if s['enabled'] else 'off'}`")

@bot.command(aliases=["sniperignore", "ignoreinvalid"])
async def ignoreinvalidcodes(ctx, name: str = None):
    await ctx.message.delete()
    if name and name.lower() in snipestate:
        s = snipestate[name.lower()]
        s["ignore_invalid"] = not s["ignore_invalid"]
        await ctx.send(f"> `{name.lower()}` will now {'ignore' if s['ignore_invalid'] else 'report'} invalid codes")

@bot.command()
async def sniperlog(ctx):
    await ctx.message.delete()
    if not snipehistory:
        await ctx.send("`[ sniperlog ]` no snipes yet", delete_after=5)
        return
    lines = [f"`[ sniperlog ]` ({len(snipehistory)})", ""]
    for entry in snipehistory[-10:]:
        lines.append(f"> `{entry['code']}` from {entry['author']} ({ago(entry['time'])}) status: `{entry['status']}`")
    await ctx.send("\n".join(lines), delete_after=30)

@bot.command(aliases=["setupwebhooks"])
async def sniperwebhook(ctx, *, url: str = None):
    await ctx.message.delete()
    global snipehook
    if not url: return
    if url.lower() == "clear":
        snipehook = ""
        config["sniper_webhook"] = ""
        save_config()
        await ctx.send("`[ sniperwebhook ]` cleared")
        return
    snipehook = url
    config["sniper_webhook"] = url
    save_config()
    await ctx.send("`[ sniperwebhook ]` set", delete_after=5)

@bot.command()
async def giveawaysniper(ctx, mode: str = None):
    await ctx.message.delete()
    if not mode: return
    if mode.lower() == "on": data["giveaway_sniper"] = True
    elif mode.lower() == "off": data["giveaway_sniper"] = False
    save_data()
    await ctx.send(f"> giveaway sniper `{mode.lower()}`")

@bot.command()
async def giveawaylist(ctx):
    await ctx.message.delete()
    if not data["giveaway_entries"]:
        await ctx.send("`[ giveawaylist ]` empty", delete_after=5)
        return
    lines = [f"`[ giveawaylist ]` ({len(data['giveaway_entries'])})"]
    for e in data["giveaway_entries"][-10:]: lines.append(f"> {e['author']} in {e['channel']}: {e['content'][:60]}")
    await ctx.send("\n".join(lines), delete_after=20)

async def cloneget(url):
    try:
        r = await bot.loop.run_in_executor(None, lambda: requests.get(url, headers=apihdrs(), timeout=15))
        if r.status_code == 200: return r.json()
    except Exception: pass
    return None

async def clonepost(url, payload):
    try:
        r = await bot.loop.run_in_executor(None, lambda: requests.post(url, headers=apihdrs(), json=payload, timeout=15))
        if r.status_code in (200, 201): return r.json()
        if r.status_code == 429:
            await asyncio.sleep(r.json().get("retry_after", 2) + 0.5)
            return await clonepost(url, payload)
    except Exception: pass
    return None

async def clonepatch(url, payload):
    try:
        r = await bot.loop.run_in_executor(None, lambda: requests.patch(url, headers=apihdrs(), json=payload, timeout=15))
        if r.status_code in (200, 204): return True
        if r.status_code == 429:
            await asyncio.sleep(r.json().get("retry_after", 2) + 0.5)
            return await clonepatch(url, payload)
    except Exception: pass
    return False

@bot.command()
async def clone(ctx, source_id: int = None, home_id: int = None):
    await ctx.message.delete()
    if not source_id or not home_id:
        await ctx.send("`[ x ]` .clone <source_id> <home_id>", delete_after=8)
        return
    src = bot.get_guild(source_id)
    home = bot.get_guild(home_id)
    if not src or not home:
        await ctx.send("`[ x ]` not in source or home server", delete_after=5)
        return
    me = home.get_member(bot.user.id)
    if not me or not me.guild_permissions.manage_channels or not me.guild_permissions.manage_roles:
        await ctx.send("`[ x ]` need manage channels + manage roles on home", delete_after=5)
        return
    status = await ctx.send(f"> `[ clone ]` reading {src.name}...")
    base = "https://discord.com/api/v10"
    channels = await cloneget(f"{base}/guilds/{source_id}/channels") or []
    roles = await cloneget(f"{base}/guilds/{source_id}/roles") or []
    for r_ in roles:
        r_.pop("id", None)
        r_.pop("guild_id", None)
    for c in channels:
        old_id = c.pop("id", None)
        c["old_id"] = old_id
        c.pop("guild_id", None)
        if "parent_id" in c: c["old_parent_id"] = c.pop("parent_id")
        if "permission_overwrites" in c:
            for ov in c["permission_overwrites"]: ov.pop("id", None)
    await status.edit(content=f"> `[ clone ]` read {len(channels)} ch + {len(roles)} roles...")
    role_count = 0
    for role in sorted(roles, key=lambda r_: r_.get("position", 0)):
        if role.get("name") == "@everyone": continue
        if await clonepost(f"{base}/guilds/{home_id}/roles", {"name": role.get("name", "role"), "permissions": str(role.get("permissions", "0")), "color": role.get("color", 0), "hoist": role.get("hoist", False), "mentionable": role.get("mentionable", False)}):
            role_count += 1
        await asyncio.sleep(1.1)
    cat_map = {}
    for ch in channels:
        if ch.get("type") != 4: continue
        res = await clonepost(f"{base}/guilds/{home_id}/channels", {"name": ch.get("name", "category"), "type": 4, "position": ch.get("position", 0)})
        if res: cat_map[ch.get("old_id")] = res["id"]
        await asyncio.sleep(1.1)
    ch_count = 0
    for ch in channels:
        if ch.get("type") == 4: continue
        ch_type = ch.get("type", 0)
        if ch_type not in (0, 2, 5, 13, 15): continue
        payload = {"name": ch.get("name", "channel"), "type": ch_type, "position": ch.get("position", 0), "topic": ch.get("topic") or None, "nsfw": ch.get("nsfw", False), "rate_limit_per_user": ch.get("rate_limit_per_user", 0) or 0}
        if ch_type == 2:
            payload["bitrate"] = ch.get("bitrate")
            payload["user_limit"] = ch.get("user_limit")
        old_parent = ch.get("old_parent_id")
        if old_parent and old_parent in cat_map: payload["parent_id"] = cat_map[old_parent]
        payload = {k: v for k, v in payload.items() if v is not None}
        if await clonepost(f"{base}/guilds/{home_id}/channels", payload): ch_count += 1
        await asyncio.sleep(1.1)
    await clonepatch(f"{base}/guilds/{home_id}", {"name": src.name})
    await status.edit(content=f"> `[ clone ]` done\n> roles: `{role_count}` | channels: `{ch_count}`\n> home renamed to {src.name}")

def ringup(channel_id):
    try: return requests.post(f"https://discord.com/api/v9/channels/{channel_id}/call/ring", headers=apihdrs(), timeout=10).status_code in (200, 204)
    except Exception: return False

def ringstop(channel_id):
    try: requests.post(f"https://discord.com/api/v9/channels/{channel_id}/call/stop-ringing", headers=apihdrs(), timeout=10)
    except Exception: pass

@bot.command()
async def callspam(ctx, target: discord.User = None, count: int = 5):
    await ctx.message.delete()
    if not target:
        await ctx.send("`[ x ]` .callspam <@user> [count]", delete_after=5)
        return
    count = max(1, min(count, 30))
    try: dm = await target.create_dm()
    except Exception: return
    for i in range(count):
        ringup(dm.id)
        await asyncio.sleep(1.0)
        ringstop(dm.id)
        await asyncio.sleep(random.uniform(0.8, 1.5))

@bot.command(aliases=["missedcallflood"])
async def callflood(ctx, target: discord.User = None, count: int = 10):
    await ctx.message.delete()
    if not target:
        await ctx.send("`[ x ]` .callflood <@user> [count]", delete_after=5)
        return
    count = max(1, min(count, 30))
    try: dm = await target.create_dm()
    except Exception: return
    for i in range(count):
        ringup(dm.id)
        await asyncio.sleep(0.5)
        ringstop(dm.id)
        await asyncio.sleep(random.uniform(0.4, 0.7))

@bot.command()
async def calltrap(ctx):
    await ctx.message.delete()
    if ctx.author.id in calltrapids:
        calltrapids.discard(ctx.author.id)
        await ctx.send("`[ calltrap ]` off", delete_after=5)
        return
    calltrapids.add(ctx.author.id)
    await ctx.send("`[ calltrap ]` on", delete_after=5)

@bot.command(aliases=["pfp"])
async def avatar(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    try:
        r = requests.get(target.display_avatar.with_size(1024).url, timeout=10)
        await ctx.send(file=discord.File(io.BytesIO(r.content), f"{target.name}-pfp.png"))
    except Exception: pass

@bot.command(aliases=["ubanner"])
async def userbanner(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    banner = getattr(target, "banner", None)
    if not banner: return
    try:
        r = requests.get(banner.with_size(1024).url, timeout=10)
        await ctx.send(file=discord.File(io.BytesIO(r.content), f"{target.name}-banner.png"))
    except Exception: pass

@bot.command()
async def usernames(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    hist = data["usernames"].get(str(target.id), [])
    if not hist:
        await ctx.send("> `[ usernames ]` no history", delete_after=8)
        return
    lines = [f"`[ usernames ]` {target.name} ({len(hist)})", ""]
    for h in hist[-15:]: lines.append(f"> `{h['old']}` to `{h['new']}` ({ago(h['time'])})")
    await ctx.send("\n".join(lines), delete_after=30)

@bot.command()
async def displays(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    hist = data["displays"].get(str(target.id), [])
    if not hist:
        await ctx.send("> `[ displays ]` no history", delete_after=8)
        return
    lines = [f"`[ displays ]` {target.name} ({len(hist)})", ""]
    for h in hist[-15:]: lines.append(f"> `{h['old'] or '-'}` to `{h['new'] or '-'}` ({ago(h['time'])})")
    await ctx.send("\n".join(lines), delete_after=30)

@bot.command()
async def avatars(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    hist = data["avatars"].get(str(target.id), [])
    if not hist:
        await ctx.send("> `[ avatars ]` no history", delete_after=8)
        return
    urls = [h["url"] for h in hist if h["url"]][-3:]
    await ctx.send(f"`[ avatars ]` {target.name} ({len(hist)} changes)\n" + "\n".join(f"> <{u}>" for u in urls), delete_after=30)

@bot.command()
async def banners(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    hist = data["banners"].get(str(target.id), [])
    if not hist:
        await ctx.send("> `[ banners ]` no history", delete_after=8)
        return
    urls = [h["url"] for h in hist if h["url"]][-3:]
    await ctx.send(f"`[ banners ]` {target.name} ({len(hist)} changes)\n" + "\n".join(f"> <{u}>" for u in urls), delete_after=30)

@bot.command()
async def guildnames(ctx, guild_id: int = None):
    await ctx.message.delete()
    gid = str(guild_id) if guild_id else (str(ctx.guild.id) if ctx.guild else None)
    if not gid: return
    hist = data["guildnames"].get(gid, [])
    if not hist:
        await ctx.send("> `[ guildnames ]` no history", delete_after=8)
        return
    lines = [f"`[ guildnames ]` ({len(hist)})", ""]
    for h in hist[-15:]: lines.append(f"> `{h['old']}` to `{h['new']}` ({ago(h['time'])})")
    await ctx.send("\n".join(lines), delete_after=30)

@bot.command()
async def ghostfriends(ctx):
    await ctx.message.delete()
    hist = data["ghostfriends"]
    if not hist:
        await ctx.send("`[ ghostfriends ]` none recorded", delete_after=8)
        return
    lines = [f"`[ ghostfriends ]` ({len(hist)})", ""]
    for g in hist[-15:]: lines.append(f"> `{g.get('display') or g['username']}` cancelled ({ago(g['time'])})")
    await ctx.send("\n".join(lines), delete_after=30)

@bot.command()
async def snipe(ctx, index: int = 1):
    await ctx.message.delete()
    hist = data["snipes"].get(str(ctx.channel.id), [])
    if not hist:
        await ctx.send("`[ snipe ]` nothing to snipe", delete_after=5)
        return
    index = max(1, min(index, len(hist)))
    entry = hist[-index]
    await ctx.send(f"> `[ snipe #{index} ]` {entry['author']} ({ago(entry['time'])})\n{entry['content']}")

@bot.command()
async def editsnipe(ctx, index: int = 1):
    await ctx.message.delete()
    hist = data["editsnipes"].get(str(ctx.channel.id), [])
    if not hist:
        await ctx.send("`[ editsnipe ]` nothing to snipe", delete_after=5)
        return
    index = max(1, min(index, len(hist)))
    entry = hist[-index]
    await ctx.send(f"> `[ editsnipe #{index} ]` {entry['author']} ({ago(entry['time'])})\n> before: {entry['before']}\n> after: {entry['after']}")

@bot.command()
async def history(ctx, target: discord.User = None, page: int = 1):
    await ctx.message.delete()
    target = target or ctx.author
    hist = data["message_history"].get(str(target.id), [])
    if not hist:
        await ctx.send(f"> `[ history ]` no messages for {target.name}", delete_after=8)
        return
    per = 10
    total = max(1, (len(hist) + per - 1) // per)
    page = max(1, min(page, total))
    start = len(hist) - (page * per)
    chunk = hist[max(0, start):max(0, start + per)]
    lines = [f"`[ history ]` {target.name} page {page}/{total} ({len(hist)} msgs)", ""]
    for m in chunk: lines.append(f"> `{m['guild']}`/{m['channel']} ({ago(m['time'])}): {m['content'][:80]}")
    await ctx.send("\n".join(lines), delete_after=45)

@bot.command()
async def lastping(ctx, target: discord.User = None):
    await ctx.message.delete()
    if not data["lastpings"]:
        await ctx.send("`[ lastping ]` no recent mentions", delete_after=5)
        return
    if target:
        info = data["lastpings"].get(str(target.id))
        if info: await ctx.send(f"> `[ lastping ]` {target.name} in {info['channel']} ({ago(info['time'])})\n{info['content']}")
        return
    lines = ["`[ lastping ]`"]
    items = sorted(data["lastpings"].items(), key=lambda x: x[1]["time"], reverse=True)[:5]
    for uid, info in items:
        try:
            u = await bot.fetch_user(int(uid))
            name = u.name
        except Exception: name = uid
        lines.append(f"> {name} in {info['channel']} ({ago(info['time'])}): {info['content'][:80]}")
    await ctx.send("\n".join(lines), delete_after=30)

@bot.command()
async def guilds(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    if target.id == bot.user.id:
        lines = [f"`[ guilds ]` you are in {len(bot.guilds)}", ""]
        for g in bot.guilds[:20]: lines.append(f"> `{g.name}` ({g.id}) {len(g.members)} members")
        await ctx.send("\n".join(lines), delete_after=30)
        return
    mutual = [g for g in bot.guilds if g.get_member(target.id)]
    if not mutual:
        await ctx.send(f"> `[ guilds ]` no mutual with {target.name}", delete_after=8)
        return
    lines = [f"`[ guilds ]` mutual with {target.name} ({len(mutual)})", ""]
    for g in mutual[:20]: lines.append(f"> `{g.name}` ({g.id})")
    await ctx.send("\n".join(lines), delete_after=30)

@bot.command()
async def export(ctx, channel: discord.TextChannel = None):
    await ctx.message.delete()
    ch = channel or ctx.channel
    rows = []
    try:
        async for msg in ch.history(limit=1000):
            rows.append({"author": str(msg.author), "avatar": str(msg.author.display_avatar.url), "content": msg.content, "time": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")})
        rows.reverse()
        parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'>", f"<title>#{html.escape(ch.name)} export</title>", "<style>body{background:#313338;color:#dbdee1;font-family:Arial,sans-serif;padding:20px;margin:0;}", ".msg{display:flex;padding:8px 0;border-bottom:1px solid #3f4147;}", ".avatar{width:40px;height:40px;border-radius:50%;margin-right:12px;flex-shrink:0;}", ".body{flex:1;}.meta{font-size:13px;color:#949ba4;margin-bottom:2px;}", ".author{color:#f2f3f5;font-weight:600;margin-right:6px;}", ".content{font-size:15px;line-height:1.4;white-space:pre-wrap;word-wrap:break-word;}", "h1{color:#f2f3f5;font-size:18px;border-bottom:1px solid #3f4147;padding-bottom:8px;}", "</style></head><body>", f"<h1>#{html.escape(ch.name)} {len(rows)} messages</h1>"]
        for r in rows:
            parts.append(f"<div class='msg'><img class='avatar' src='{html.escape(r['avatar'])}'><div class='body'><div class='meta'><span class='author'>{html.escape(r['author'])}</span>{html.escape(r['time'])}</div><div class='content'>{html.escape(r['content'])}</div></div></div>")
        parts.append("</body></html>")
        buf = io.BytesIO("".join(parts).encode("utf-8"))
        await ctx.send(file=discord.File(buf, f"{ch.name}-export.html"))
    except Exception as e: await ctx.send(f"`[ x ]` `{e}`", delete_after=5)

@bot.command()
async def uptime(ctx):
    await ctx.message.delete()
    delta = datetime.datetime.now(datetime.timezone.utc) - start_time
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    d, h = divmod(h, 24)
    if d: await ctx.send(f"{d}d {h}h {m}m {s}s")
    else: await ctx.send(f"{h}h {m}m {s}s")

@bot.command()
async def ping(ctx):
    await ctx.message.delete()
    before = time.monotonic()
    msg = await ctx.send("...")
    await msg.edit(content=f"`{int((time.monotonic() - before) * 1000)} ms`")

@bot.command()
async def geoip(ctx, ip: str = None):
    await ctx.message.delete()
    if not ip: return
    try:
        geo = requests.get(f"http://ip-api.com/json/{ip}", timeout=10).json()
        await ctx.send(f"**IP** `{geo['query']}`\n**Location** `{geo['country']} / {geo['regionName']} / {geo['city']}`\n**Coords** `{geo['lat']}, {geo['lon']}`\n**ISP** `{geo['isp']}`\n**Org** `{geo['org']}`\n**Timezone** `{geo['timezone']}`")
    except Exception: pass

@bot.command()
async def tts(ctx, *, content: str = None):
    await ctx.message.delete()
    if not content: return
    t = gTTS(text=content.strip(), lang="en")
    f = io.BytesIO()
    t.write_to_fp(f)
    f.seek(0)
    await ctx.send(file=discord.File(f, "tts.mp3"))

@bot.command(aliases=["qrcode"])
async def qr(ctx, *, text: str = "xaoc"):
    await ctx.message.delete()
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    await ctx.send(file=discord.File(buf, "qr_code.png"))

@bot.command()
async def pingweb(ctx, url: str = None):
    await ctx.message.delete()
    if not url: return
    try:
        r = requests.get(url, timeout=10).status_code
        await ctx.send(f"`[ pingweb ]` {'down' if r == 404 else 'operational'} `({r})`")
    except Exception: pass

@bot.command()
async def gentoken(ctx, user: str = None):
    await ctx.message.delete()
    code = ("ODA" + random.choice(string.ascii_letters) + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(20)) + "." + random.choice(string.ascii_letters).upper() + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(5)) + "." + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(27)))
    if not user: await ctx.send(code)
    else: await ctx.send(f"> {user}'s token: ||{code}||")

@bot.command()
async def quickdelete(ctx, *, message: str = None):
    await ctx.message.delete()
    if message: await ctx.send(message, delete_after=2)

@bot.command(aliases=["uicon"])
async def usericon(ctx, user: discord.User = None):
    await ctx.message.delete()
    if user: await ctx.send(f"> {user.mention}: {user.display_avatar.url}")

@bot.command(aliases=["tinfo"])
async def tokeninfo(ctx, usertoken: str = None):
    await ctx.message.delete()
    if not usertoken: return
    try:
        res = requests.get("https://discord.com/api/v10/users/@me", headers={"Authorization": usertoken, "Content-Type": "application/json"}, timeout=10)
        res.raise_for_status()
    except Exception: return
    d = res.json()
    uid = d["id"]
    created = datetime.datetime.fromtimestamp(((int(uid) >> 22) + 1420070400000) / 1000).strftime("%d-%m-%Y %H:%M UTC")
    await ctx.send(f"**Username** `{d['username']}`\n**ID** `{uid}`\n**Created** `{created}`\n**Email** `{d.get('email') or 'None'}`\n**Phone** `{d.get('phone') or 'None'}`\n**MFA** `{d.get('mfa_enabled')}`\n**Locale** `{d.get('locale')}`")

@bot.command()
async def cleardm(ctx, amount: str = "1"):
    await ctx.message.delete()
    if not amount.isdigit() or not isinstance(ctx.channel, discord.DMChannel): return
    amount = int(amount)
    if not 1 <= amount <= 100: return
    async for m in ctx.channel.history(limit=amount):
        if m.author == bot.user:
            try: await m.delete()
            except Exception: pass

@bot.command(aliases=["hs"])
async def hypesquad(ctx, house: str = None):
    await ctx.message.delete()
    if not house: return
    payload = {"bravery": 1, "brilliance": 2, "balance": 3}.get(house.lower())
    if payload:
        try: requests.post("https://discord.com/api/v9/hypesquad/online", headers=apihdrs(), json={"house_id": payload}, timeout=10)
        except Exception: pass

@bot.command(aliases=["serverinfo"])
async def guildinfo(ctx):
    await ctx.message.delete()
    if not ctx.guild: return
    g = ctx.guild
    await ctx.send(f"**Name** `{g.name}`\n**ID** `{g.id}`\n**Created** `{g.created_at.strftime('%a, %d %b %Y %I:%M %p')}`\n**Icon** `{g.icon.url if g.icon else 'None'}`\n**Owner** `{g.owner}`\n**Members** `{len(g.members)}`\n**Roles** `{len(g.roles)}`\n**Channels** `{len(g.text_channels)} text / {len(g.voice_channels)} voice`")

@bot.command(aliases=["me", "account"])
async def info(ctx):
    await ctx.message.delete()
    try: d = requests.get("https://discord.com/api/v10/users/@me", headers=apihdrs(), timeout=10).json()
    except Exception: return
    uid = d["id"]
    created = datetime.datetime.fromtimestamp(((int(uid) >> 22) + 1420070400000) / 1000).strftime("%d-%m-%Y %H:%M UTC")
    await ctx.send(f"**Username** `{d['username']}`\n**Display** `{d.get('global_name') or 'None'}`\n**ID** `{uid}`\n**Created** `{created}`\n**Email** `{d.get('email') or 'None'}`\n**Phone** `{d.get('phone') or 'None'}`\n**MFA** `{d.get('mfa_enabled')}`\n**Locale** `{d.get('locale')}`")

@bot.command()
async def nitro(ctx):
    await ctx.message.delete()
    await ctx.send(f"https://discord.gift/{''.join(random.choices(string.ascii_letters + string.digits, k=16))}")

@bot.command()
async def whremove(ctx, webhook: str = None):
    await ctx.message.delete()
    if webhook:
        try: requests.delete(webhook.rstrip(), timeout=10)
        except Exception: pass

@bot.command(aliases=["hide"])
async def hidemention(ctx, *, content: str = None):
    await ctx.message.delete()
    if content: await ctx.send(content + "\n" + "||\u200b||\n" * 100 + "@everyone")

@bot.command()
async def edit(ctx, *, content: str = None):
    await ctx.message.delete()
    if content:
        text = await ctx.send(content)
        await text.edit(content=f"\u202b{content}")

@bot.command(aliases=["911"])
async def airplane(ctx):
    await ctx.message.delete()
    frames = [":man_wearing_turban::airplane:\t\t\t\t:office:", ":man_wearing_turban:\t:airplane:\t\t\t:office:", ":man_wearing_turban:\t\t::airplane:\t\t:office:", ":man_wearing_turban:\t\t\t:airplane:\t:office:", ":man_wearing_turban:\t\t\t\t:airplane::office:", ":boom::boom::boom:"]
    msg = await ctx.send(frames[0])
    for f in frames[1:]:
        await asyncio.sleep(0.5)
        await msg.edit(content=f)

@bot.command(aliases=["mine"])
async def minesweeper(ctx, size: int = 5):
    await ctx.message.delete()
    size = max(min(size, 8), 2)
    bombs = [[random.randint(0, size - 1), random.randint(0, size - 1)] for _ in range(size - 1)]
    inb = lambda x, y: 0 <= x < size and 0 <= y < size
    hb = lambda x, y: [i for i in bombs if i[0] == x and i[1] == y]
    nums = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:"]
    offs = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    out = "**Click to play**:\n"
    for yy in range(size):
        for xx in range(size):
            tile = "||{}||".format(chr(11036))
            if hb(xx, yy): tile = "||{}||".format(chr(128163))
            else:
                c = 0
                for xo, yo in offs:
                    if inb(xx + xo, yy + yo) and hb(xx + xo, yy + yo): c += 1
                if c: tile = "||{}||".format(nums[c - 1])
            out += tile
        out += "\n"
    await ctx.send(out)

@bot.command(aliases=["leet"])
async def leetspeak(ctx, *, content: str = None):
    await ctx.message.delete()
    if content:
        for a_, b_ in [("a", "4"), ("e", "3"), ("i", "1"), ("o", "0"), ("t", "7"), ("b", "8")]:
            content = content.replace(a_, b_).replace(a_.upper(), b_)
        await ctx.send(content)

@bot.command()
async def dick(ctx, user: str = None):
    await ctx.message.delete()
    if not user: user = ctx.author.display_name
    await ctx.send(f"> {user}'s size:\n8{'=' * random.randint(1, 15)}D")

@bot.command()
async def reverse(ctx, *, content: str = None):
    await ctx.message.delete()
    if content: await ctx.send(content[::-1])

@bot.command(aliases=["fetch"])
async def fetchmembers(ctx):
    await ctx.message.delete()
    if not ctx.guild: return
    rows = [{"name": m.name, "id": str(m.id), "avatar_url": str(m.avatar.url) if m.avatar else str(m.default_avatar.url), "status": str(m.status), "joined_at": str(m.joined_at)} for m in ctx.guild.members]
    buf = io.BytesIO(json.dumps(rows, indent=4).encode())
    await ctx.send(file=discord.File(buf, "members.json"))

@bot.command()
async def spam(ctx, amount: int = 1, *, message_to_send: str = "spam"):
    await ctx.message.delete()
    if amount <= 0 or amount > 9: return
    for i in range(amount):
        try: await ctx.send(message_to_send)
        except Exception: pass

@bot.command(aliases=["gicon"])
async def guildicon(ctx):
    await ctx.message.delete()
    if ctx.guild: await ctx.send(f"> {ctx.guild.name}\n{ctx.guild.icon.url if ctx.guild.icon else '*NO ICON*'}")

@bot.command(aliases=["gbanner"])
async def guildbanner(ctx):
    await ctx.message.delete()
    if ctx.guild: await ctx.send(f"> {ctx.guild.name}\n{ctx.guild.banner.url if ctx.guild.banner else '*NO BANNER*'}")

@bot.command(aliases=["grename"])
async def guildrename(ctx, *, name: str = None):
    await ctx.message.delete()
    if not name or not ctx.guild or not ctx.guild.me.guild_permissions.manage_guild: return
    try: await ctx.guild.edit(name=name)
    except Exception: pass

@bot.command()
async def purge(ctx, num_messages: int = 1):
    await ctx.message.delete()
    if not ctx.guild or not ctx.author.guild_permissions.manage_messages: return
    if 1 <= num_messages <= 100:
        try: await ctx.channel.purge(limit=num_messages)
        except Exception: pass

@bot.command(aliases=["autor"])
async def autoreply(ctx, command: str, user: discord.User = None):
    await ctx.message.delete()
    if command.upper() not in ("ON", "OFF"): return
    if command.upper() == "ON":
        if user:
            if str(user.id) not in config["autoreply"]["users"]: config["autoreply"]["users"].append(str(user.id))
        else:
            if str(ctx.channel.id) not in config["autoreply"]["channels"]: config["autoreply"]["channels"].append(str(ctx.channel.id))
    else:
        if user:
            if str(user.id) in config["autoreply"]["users"]: config["autoreply"]["users"].remove(str(user.id))
        else:
            if str(ctx.channel.id) in config["autoreply"]["channels"]: config["autoreply"]["channels"].remove(str(ctx.channel.id))
    save_config()

@bot.command(aliases=["remote"])
async def remoteuser(ctx, action: str, *users: discord.User):
    await ctx.message.delete()
    if not users or action.upper() not in ("ADD", "REMOVE"): return
    if action.upper() == "ADD":
        for u in users:
            if str(u.id) not in config["remote-users"]: config["remote-users"].append(str(u.id))
    else:
        for u in users:
            if str(u.id) in config["remote-users"]: config["remote-users"].remove(str(u.id))
    save_config()

@bot.command(aliases=["addwhitelist"])
async def whitelist(ctx, user: discord.User = None):
    await ctx.message.delete()
    if user and str(user.id) not in config["remote-users"]:
        config["remote-users"].append(str(user.id))
        save_config()

@bot.command(aliases=["removewhitelist"])
async def unwhitelist(ctx, user: discord.User = None):
    await ctx.message.delete()
    if user and str(user.id) in config["remote-users"]:
        config["remote-users"].remove(str(user.id))
        save_config()

@bot.command()
async def list_whitelist(ctx):
    await ctx.message.delete()
    users = config["remote-users"]
    if not users:
        await ctx.send("`[ whitelist ]` empty", delete_after=5)
        return
    lines = [f"`[ whitelist ]` ({len(users)})"]
    for uid in users:
        try:
            u = await bot.fetch_user(int(uid))
            lines.append(f"> `{u.name}` ({uid})")
        except Exception: lines.append(f"> `{uid}`")
    await ctx.send("\n".join(lines), delete_after=20)

@bot.command()
async def afk(ctx, status: str = None, *, message: str = None):
    await ctx.message.delete()
    if status not in ("ON", "OFF"): return
    if status.upper() == "ON":
        config["afk"]["enabled"] = True
        if message: config["afk"]["message"] = message
    else: config["afk"]["enabled"] = False
    save_config()

@bot.command(aliases=["prefix", "changeprefix"])
async def set_prefix(ctx, *, new_prefix: str = None):
    await ctx.message.delete()
    if new_prefix:
        config["prefix"] = new_prefix
        save_config()
        bot.command_prefix = new_prefix

@bot.command(aliases=["logout"])
async def shutdown(ctx):
    await ctx.message.delete()
    await bot.close()

@bot.command()
async def clear(ctx):
    await ctx.message.delete()
    await ctx.send("\u200b\n" * 200)

@bot.command()
async def sendall(ctx, *, message="spam"):
    await ctx.message.delete()
    if not ctx.guild: return
    for ch in ctx.guild.text_channels:
        try:
            await ch.send(message)
            await asyncio.sleep(random.uniform(1.2, 2.5))
        except Exception: pass

@bot.command(aliases=["copycatuser", "copyuser"])
async def copycat(ctx, action: str = None, user: discord.User = None):
    await ctx.message.delete()
    if action not in ("ON", "OFF") or not user: return
    if action == "ON":
        if user.id not in config["copycat"]["users"]: config["copycat"]["users"].append(user.id)
    else:
        if user.id in config["copycat"]["users"]: config["copycat"]["users"].remove(user.id)
    save_config()

@bot.command()
async def firstmessage(ctx):
    await ctx.message.delete()
    if not ctx.guild: return
    try:
        async for m in ctx.channel.history(limit=1, oldest_first=True):
            await ctx.send(f"> https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{m.id}", delete_after=5)
            break
    except Exception: pass

@bot.command()
async def lastmessage(ctx):
    await ctx.message.delete()
    if not ctx.guild: return
    try:
        async for m in ctx.channel.history(limit=1):
            await ctx.send(f"> https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{m.id}", delete_after=10)
            return
    except Exception: pass

@bot.command()
async def ascii(ctx, *, message=None):
    await ctx.message.delete()
    if message:
        try: await ctx.send(f"```\n{pyfiglet.figlet_format(message)}\n```")
        except Exception: pass

@bot.command()
async def status(ctx, mode: str = None):
    await ctx.message.delete()
    mapping = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible, "offline": discord.Status.invisible}
    if mode and mode.lower() in mapping:
        try: await bot.change_presence(status=mapping[mode.lower()])
        except Exception: pass

@bot.command()
async def customstatus(ctx, *, text: str = None):
    await ctx.message.delete()
    if text:
        try: await bot.change_presence(activity=discord.CustomActivity(name=text))
        except Exception: pass

@bot.command()
async def autodelete(ctx, seconds: str = None):
    await ctx.message.delete()
    if not seconds:
        deletetimers.pop(ctx.channel.id, None)
        return
    try: n = int(seconds)
    except ValueError: return
    deletetimers[ctx.channel.id] = max(1, min(n, 3600))

@bot.command()
async def stopall(ctx):
    await ctx.message.delete()
    for task in list(nickjobs.values()): task.cancel()
    for trap in list(gclocks.values()): trap["task"].cancel()
    for rot in list(spinjobs.values()): rot["task"].cancel()
    mimictargets.clear()
    reactchannels.clear()
    reactemojis.clear()
    deletetimers.clear()
    nickjobs.clear()
    gclocks.clear()
    followers.clear()
    spinjobs.clear()
    calltrapids.clear()

@bot.command(aliases=["config"])
async def settings(ctx):
    await ctx.message.delete()
    await ctx.send(f"`[ config ]`\n> prefix: `{config.get('prefix')}`\n> afk: `{config['afk']['enabled']}`\n> platform: `{spoofplat}`\n> remote users: `{len(config['remote-users'])}`\n> history entries: `{sum(len(v) for v in data['message_history'].values())}`", delete_after=20)

@bot.command(aliases=["sicon"])
async def servericon(ctx, guild_id: int = None):
    await ctx.message.delete()
    guild = bot.get_guild(guild_id) if guild_id else ctx.guild
    if not guild or not guild.icon: return
    try:
        r = requests.get(guild.icon.with_size(1024).url, timeout=10)
        await ctx.send(file=discord.File(io.BytesIO(r.content), f"{guild.name}-icon.png"))
    except Exception: pass

@bot.command(aliases=["sbanner"])
async def serverbanner(ctx, guild_id: int = None):
    await ctx.message.delete()
    guild = bot.get_guild(guild_id) if guild_id else ctx.guild
    if not guild or not guild.banner: return
    try:
        r = requests.get(guild.banner.with_size(1024).url, timeout=10)
        await ctx.send(file=discord.File(io.BytesIO(r.content), f"{guild.name}-banner.png"))
    except Exception: pass

@bot.command()
async def check(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    await ctx.send(f"> `[ check ]` {target.name} id `{target.id}` created `{target.created_at.strftime('%d-%m-%Y')}`")

@bot.command()
async def count(ctx, channel: discord.TextChannel = None):
    await ctx.message.delete()
    ch = channel or ctx.channel
    n = 0
    try:
        async for i in ch.history(limit=1000): n += 1
    except Exception: pass
    await ctx.send(f"> `[ count ]` counted `{n}` in {ch.mention}", delete_after=10)

@bot.command()
async def define(ctx, *, word: str = None):
    await ctx.message.delete()
    if not word: return
    try:
        d = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10).json()
        await ctx.send(f"> `[ define ]` {word}: {d[0]['meanings'][0]['definitions'][0]['definition']}")
    except Exception: pass

@bot.command()
async def languages(ctx):
    await ctx.message.delete()
    await ctx.send("> `[ languages ]` " + ", ".join(["en-US", "en-GB", "es-ES", "fr", "de", "it", "pt-BR", "ru", "ja", "ko", "zh-CN"]), delete_after=15)

@bot.command()
async def joinvc(ctx):
    await ctx.message.delete()
    if ctx.author.voice and ctx.author.voice.channel:
        try: await ctx.author.voice.channel.connect()
        except Exception: pass

@bot.command()
async def leavevc(ctx):
    await ctx.message.delete()
    for vc in bot.voice_clients:
        try: await vc.disconnect()
        except Exception: pass

@bot.command()
async def joinserver(ctx, invite: str = None):
    await ctx.message.delete()
    if invite:
        try: requests.post(f"https://discord.com/api/v10/invites/{invite.split('/')[-1].split('?')[0]}", headers=apihdrs(), timeout=10)
        except Exception: pass

@bot.command(aliases=["mreact"])
async def massreact(ctx, emoji: str = None, count: int = 5):
    await ctx.message.delete()
    if not emoji: return
    count = max(1, min(count, 25))
    reacted = 0
    async for m in ctx.channel.history(limit=count * 3):
        if reacted >= count: break
        if m.author == bot.user: continue
        try:
            await m.add_reaction(emoji)
            reacted += 1
            await asyncio.sleep(random.uniform(0.3, 0.7))
        except Exception: continue

@bot.command(aliases=["manualreact"])
async def react(ctx, emoji: str = None, message_id: int = None):
    await ctx.message.delete()
    if not emoji: return
    target = None
    if message_id:
        try: target = await ctx.channel.fetch_message(message_id)
        except Exception: return
    else:
        async for m in ctx.channel.history(limit=5):
            if m.author != bot.user:
                target = m
                break
    if target:
        try: await target.add_reaction(emoji)
        except Exception: pass

@bot.command()
async def unreact(ctx, emoji: str = None, message_id: int = None):
    await ctx.message.delete()
    if not emoji: return
    target = None
    if message_id:
        try: target = await ctx.channel.fetch_message(message_id)
        except Exception: return
    else:
        async for m in ctx.channel.history(limit=5):
            if m.author != bot.user:
                target = m
                break
    if target:
        try: await target.remove_reaction(emoji, bot.user)
        except Exception: pass

@bot.command(aliases=["nick"])
async def nickall(ctx, *, name: str = None):
    await ctx.message.delete()
    if not name: return
    for guild in bot.guilds:
        member = guild.get_member(bot.user.id)
        if member:
            try:
                await member.edit(nick=name)
                await asyncio.sleep(1.2)
            except Exception: continue

@bot.command()
async def purgeuser(ctx, target: discord.User = None, count: int = 20):
    await ctx.message.delete()
    if not target or not ctx.guild or not ctx.author.guild_permissions.manage_messages: return
    count = max(1, min(count, 100))
    deleted = 0
    async for m in ctx.channel.history(limit=count * 3):
        if deleted >= count: break
        if m.author.id == target.id:
            try:
                await m.delete()
                deleted += 1
                await asyncio.sleep(0.4)
            except Exception: continue

async def socialize(ctx, action, target):
    await ctx.message.delete()
    if target is None: target = ctx.message.mentions[0] if ctx.message.mentions else ctx.author
    if target.id == ctx.author.id: line = f"> {ctx.author.display_name} {action}s themselves."
    else: line = f"> {ctx.author.display_name} {action}s {target.display_name}"
    await ctx.send(f"{line}\n{random.choice(SOCIAL_GIFS.get(action, SOCIAL_GIFS['hug']))}")

@bot.command()
async def hug(ctx, target: discord.User = None): await socialize(ctx, "hug", target)
@bot.command()
async def kiss(ctx, target: discord.User = None): await socialize(ctx, "kiss", target)
@bot.command()
async def kill(ctx, target: discord.User = None): await socialize(ctx, "kill", target)
@bot.command()
async def slap(ctx, target: discord.User = None): await socialize(ctx, "slap", target)
@bot.command()
async def pat(ctx, target: discord.User = None): await socialize(ctx, "pat", target)
@bot.command()
async def bonk(ctx, target: discord.User = None): await socialize(ctx, "bonk", target)
@bot.command()
async def cuddle(ctx, target: discord.User = None): await socialize(ctx, "cuddle", target)

@bot.command(aliases=["gp"])
async def ghostping(ctx, target: discord.User = None, count: int = 1):
    await ctx.message.delete()
    if not target: return
    count = max(1, min(count, 15))
    for i in range(count):
        try:
            m = await ctx.send(target.mention)
            await m.delete()
        except Exception: pass
        await asyncio.sleep(random.uniform(0.6, 1.2))

@bot.command()
async def mimic(ctx, target: discord.User = None, minutes: int = 5):
    await ctx.message.delete()
    if target: mimictargets[target.id] = time.time() + minutes * 60

@bot.command()
async def autoreact(ctx, emoji: str = None):
    await ctx.message.delete()
    if not emoji:
        reactchannels.pop(ctx.channel.id, None)
        reactemojis.pop(ctx.channel.id, None)
        return
    reactchannels[ctx.channel.id] = True
    reactemojis[ctx.channel.id] = emoji

@bot.command()
async def msgspam(ctx, count: int = 5, *, message: str = "spam"):
    await ctx.message.delete()
    count = max(1, min(count, 50))
    for i in range(count):
        try: await ctx.send(message)
        except Exception: pass
        await asyncio.sleep(random.uniform(0.4, 0.9))

@bot.command()
async def dmspam(ctx, target: discord.User = None, count: int = 5, *, message: str = "spam"):
    await ctx.message.delete()
    if not target: return
    count = max(1, min(count, 30))
    for i in range(count):
        try: await target.send(message)
        except Exception: pass
        await asyncio.sleep(random.uniform(1.0, 2.0))

@bot.command()
async def reactspam(ctx, *, args: str = None):
    await ctx.message.delete()
    parts = args.split() if args else []
    message_id = None
    if parts and parts[-1].isdigit():
        message_id = int(parts[-1])
        parts = parts[:-1]
    emojis = parts if parts else random.sample(["👍", "🔥", "😂", "❤️", "🎉", "💯", "👀", "✨", "😳", "🙏"], 3)
    target = None
    if message_id:
        try: target = await ctx.channel.fetch_message(message_id)
        except Exception: return
    else:
        if ctx.message.reference and ctx.message.reference.message_id:
            try: target = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except Exception: pass
        if not target:
            async for m in ctx.channel.history(limit=5):
                if m.author != bot.user:
                    target = m
                    break
    if target:
        for e in emojis:
            try:
                await target.add_reaction(e)
                await asyncio.sleep(random.uniform(0.3, 0.6))
            except Exception: continue

@bot.command()
async def trap(ctx, target: discord.User = None):
    if not target:
        await ctx.message.delete()
        return
    channel = ctx.channel
    if not isinstance(channel, discord.GroupChannel):
        await ctx.message.delete()
        return
    await ctx.message.delete()
    key = channel.id
    if key in gclocks and gclocks[key]["user_id"] == target.id:
        gclocks[key]["task"].cancel()
        del gclocks[key]
        return
    if key in gclocks: gclocks[key]["task"].cancel()

    async def keeper():
        while True:
            try:
                ch = await bot.fetch_channel(channel.id)
                if not isinstance(ch, discord.GroupChannel): break
                ids = [u.id for u in ch.recipients]
                if target.id not in ids:
                    requests.put(f"https://discord.com/api/v10/channels/{ch.id}/recipients/{target.id}", headers=apihdrs(), json={})
                await asyncio.sleep(3)
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(5)
    gclocks[key] = {"user_id": target.id, "task": bot.loop.create_task(keeper())}

@bot.command()
async def tokenflood(ctx, count: int = 5):
    await ctx.message.delete()
    count = max(1, min(count, 25))
    for i in range(count):
        code = ("ODA" + random.choice(string.ascii_letters) + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(20)) + "." + random.choice(string.ascii_letters).upper() + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(5)) + "." + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(27)))
        await ctx.send(f"||{code}||")
        await asyncio.sleep(random.uniform(0.5, 1.0))

@bot.command()
async def nitroflood(ctx, count: int = 5):
    await ctx.message.delete()
    count = max(1, min(count, 25))
    for i in range(count):
        await ctx.send(f"https://discord.gift/{''.join(random.choices(string.ascii_letters + string.digits, k=16))}")
        await asyncio.sleep(random.uniform(0.5, 1.0))

@bot.command()
async def gcname(ctx, *, name: str = None):
    await ctx.message.delete()
    if name:
        try: await ctx.channel.edit(name=name)
        except Exception: pass

@bot.command()
async def antigc(ctx):
    await ctx.message.delete()
    for ch in list(bot.private_channels):
        if isinstance(ch, discord.GroupChannel):
            try: await ch.leave()
            except Exception: pass

@bot.command(name="8ball")
async def eightball(ctx, *, question: str = None):
    await ctx.message.delete()
    if question:
        answers = ["yes.", "no.", "maybe.", "ask again later.", "definitely.", "definitely not.", "unclear.", "i wouldn't bet on it.", "for sure.", "not a chance."]
        await ctx.send(f"> `[ 8ball ]` Q: {question}\n> A: {random.choice(answers)}")

@bot.command()
async def coinflip(ctx):
    await ctx.message.delete()
    await ctx.send(f"> `[ coinflip ]` {random.choice(['heads', 'tails'])}")

@bot.command()
async def dice(ctx, sides: int = 6):
    await ctx.message.delete()
    await ctx.send(f"> `[ dice ]` `{random.randint(1, max(2, sides))}`")

@bot.command()
async def rps(ctx, choice: str = None):
    await ctx.message.delete()
    if choice not in ("rock", "paper", "scissors"): return
    bc = random.choice(["rock", "paper", "scissors"])
    beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
    result = "tie" if choice == bc else ("you win" if beats[choice] == bc else "you lose")
    await ctx.send(f"> `[ rps ]` you: `{choice}` | me: `{bc}` {result}")

@bot.command()
async def faketype(ctx, seconds: int = 10):
    await ctx.message.delete()
    seconds = max(1, min(seconds, 120))
    async with ctx.typing(): await asyncio.sleep(seconds)

@bot.command()
async def nickcycle(ctx, *, names: str = None):
    await ctx.message.delete()
    if not ctx.guild or not names: return
    name_list = [n.strip() for n in names.split("|") if n.strip()]
    key = ctx.guild.id
    if key in nickjobs: nickjobs[key].cancel()

    async def loop():
        i = 0
        while True:
            try:
                m = ctx.guild.get_member(bot.user.id)
                if m: await m.edit(nick=name_list[i % len(name_list)])
                i += 1
                await asyncio.sleep(3)
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(5)
    nickjobs[key] = bot.loop.create_task(loop())

@bot.command()
async def timer(ctx, duration: str = None):
    await ctx.message.delete()
    if not duration: return
    m = re.match(r"^(\d+)([smhd])$", duration)
    if not m: return
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2).lower()]
    secs = int(m.group(1)) * mult
    if secs > 300: return
    msg = await ctx.send(f"`[ timer ]` {secs}s")
    for remaining in range(secs - 1, -1, -1):
        await asyncio.sleep(1)
        try: await msg.edit(content=f"`[ timer ]` {remaining}s")
        except Exception: break

@bot.command()
async def shrug(ctx):
    await ctx.message.delete()
    await ctx.send("¯\\_(ツ)_/¯")

@bot.command()
async def tableflip(ctx):
    await ctx.message.delete()
    await ctx.send("(╯°□°）╯︵ ┻━┻")

@bot.command()
async def unflip(ctx):
    await ctx.message.delete()
    await ctx.send("┬─┬ ノ( ゜-゜ノ)")

@bot.command(aliases=["empty"])
async def blank(ctx):
    await ctx.message.delete()
    await ctx.send("** **")

@bot.command(aliases=["bypass"])
async def chatbypass(ctx, *, text: str = None):
    await ctx.message.delete()
    if text:
        table = str.maketrans("abcdefghijklmnopqrstuvwxyz", "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣")
        await ctx.send(text.lower().translate(table))

@bot.command()
async def regional(ctx, *, text: str = None):
    await ctx.message.delete()
    if text:
        base = ord("🇦") - ord("a")
        await ctx.send("".join(chr(ord(c) + base) if c.isalpha() else c for c in text.lower()))

@bot.command()
async def randomcase(ctx, *, text: str = None):
    await ctx.message.delete()
    if text: await ctx.send("".join(random.choice([c.upper(), c.lower()]) for c in text))

@bot.command()
async def animate(ctx, *, text: str = None):
    await ctx.message.delete()
    if not text: return
    msg = await ctx.send(text[0])
    out = text[0]
    for c in text[1:]:
        out += c
        await asyncio.sleep(0.5)
        try: await msg.edit(content=out)
        except Exception: break

@bot.command(aliases=["letmegooglethatforyou"])
async def lmgtfy(ctx, *, query: str = None):
    await ctx.message.delete()
    if query: await ctx.send(f"https://lmgtfy.app/?q={query.replace(' ', '+')}")

async def codeblock(ctx, lang, code):
    await ctx.message.delete()
    if code: await ctx.send(f"```{lang}\n{code}\n```")

@bot.command(name="json")
async def jsonblock(ctx, *, code: str = None): await codeblock(ctx, "json", code)
@bot.command(name="python", aliases=["py"])
async def pythonblock(ctx, *, code: str = None): await codeblock(ctx, "python", code)
@bot.command(name="js", aliases=["javascript"])
async def jsblock(ctx, *, code: str = None): await codeblock(ctx, "javascript", code)
@bot.command(name="html")
async def htmlblock(ctx, *, code: str = None): await codeblock(ctx, "html", code)
@bot.command(name="css")
async def cssblock(ctx, *, code: str = None): await codeblock(ctx, "css", code)
@bot.command(name="java")
async def javablock(ctx, *, code: str = None): await codeblock(ctx, "java", code)
@bot.command(name="c")
async def cblock(ctx, *, code: str = None): await codeblock(ctx, "c", code)
@bot.command(name="cpp")
async def cppblock(ctx, *, code: str = None): await codeblock(ctx, "cpp", code)
@bot.command(name="php")
async def phpblock(ctx, *, code: str = None): await codeblock(ctx, "php", code)
@bot.command(name="lua")
async def luablock(ctx, *, code: str = None): await codeblock(ctx, "lua", code)

@bot.command()
async def zalgo(ctx, *, text: str = None):
    await ctx.message.delete()
    if not text: return
    comb = ["\u0300", "\u0301", "\u0302", "\u0303", "\u0308", "\u030a", "\u0327"]
    out = ""
    for ch in text:
        out += ch
        for i in range(random.randint(1, 4)): out += random.choice(comb)
    await ctx.send(out[:1900])

@bot.command()
async def aesthetic(ctx, *, text: str = None):
    await ctx.message.delete()
    if not text: return
    out = ""
    for ch in text:
        o = ord(ch)
        if 33 <= o <= 126: out += chr(o + 0xFEE0)
        elif ch == " ": out += "　"
        else: out += ch
    await ctx.send(out)

@bot.command()
async def bubble(ctx, *, text: str = None):
    await ctx.message.delete()
    if not text: return
    alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    bubbled = "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"
    await ctx.send("".join(bubbled[alpha.index(c)] if c in alpha else c for c in text))

@bot.command()
async def morse(ctx, *, text: str = None):
    await ctx.message.delete()
    if not text: return
    m = {"a": ".-", "b": "-...", "c": "-.-.", "d": "-..", "e": ".", "f": "..-.", "g": "--.", "h": "....", "i": "..", "j": ".---", "k": "-.-", "l": ".-..", "m": "--", "n": "-.", "o": "---", "p": ".--.", "q": "--.-", "r": ".-.", "s": "...", "t": "-", "u": "..-", "v": "...-", "w": ".--", "x": "-..-", "y": "-.--", "z": "--.."}
    await ctx.send(" ".join(m.get(c.lower(), c) for c in text)[:1900])

@bot.command()
async def binary(ctx, *, text: str = None):
    await ctx.message.delete()
    if text: await ctx.send(" ".join(format(ord(c), "08b") for c in text)[:1900])

@bot.command()
async def spoiler(ctx, *, text: str = None):
    await ctx.message.delete()
    if text: await ctx.send("".join(f"||{c}||" for c in text)[:1900])

async def getavatar(target):
    r = requests.get(target.display_avatar.with_size(512).url, timeout=10)
    return Image.open(io.BytesIO(r.content)).convert("RGBA")

@bot.command()
async def pfpglitch(ctx, target: discord.User = None):
    await ctx.message.delete()
    target = target or ctx.author
    try:
        img = await getavatar(target)
        w_, h_ = img.size
        r, g, b_, a = img.split()
        r = r.transform((w_, h_), Image.AFFINE, (1, 0.05, 0, 0, 1, 0))
        b_ = b_.transform((w_, h_), Image.AFFINE, (1, -0.05, 0, 0, 1, 0))
        out = Image.merge("RGBA", (r, g, b_, a))
        buf = io.BytesIO()
        out.save(buf, "PNG")
        buf.seek(0)
        await ctx.send(file=discord.File(buf, "glitch.png"))
    except Exception: pass

@bot.command()
async def pfppixelate(ctx, target: discord.User = None, size: int = 16):
    await ctx.message.delete()
    target = target or ctx.author
    size = max(4, min(size, 128))
    try:
        img = await getavatar(target)
        img = img.resize((size, size), Image.NEAREST).resize((512, 512), Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        await ctx.send(file=discord.File(buf, "pixelate.png"))
    except Exception: pass

@bot.command()
async def lovecalc(ctx, a: discord.User = None, b: discord.User = None):
    await ctx.message.delete()
    if not a or not b: return
    percent = (a.id + b.id) % 100
    percent = percent if percent > 20 else percent + 40
    await ctx.send(f"> `[ lovecalc ]` {a.display_name} + {b.display_name}\n> {'█' * int(percent / 5)}{'░' * (20 - int(percent / 5))} {percent}%")

@bot.command()
async def cat(ctx):
    await ctx.message.delete()
    try: await ctx.send(requests.get("https://api.alexflipnote.dev/cats", timeout=10).json()["file"])
    except Exception: pass

@bot.command()
async def dog(ctx):
    await ctx.message.delete()
    try: await ctx.send(requests.get("https://api.alexflipnote.dev/dogs", timeout=10).json()["file"])
    except Exception: pass

@bot.command(aliases=["birb"])
async def bird(ctx):
    await ctx.message.delete()
    try: await ctx.send(requests.get("https://api.alexflipnote.dev/birb", timeout=10).json()["file"])
    except Exception: pass

@bot.command()
async def fox(ctx):
    await ctx.message.delete()
    try: await ctx.send(requests.get("https://randomfox.ca/floof/", timeout=10).json()["image"])
    except Exception: pass

@bot.command()
async def raccoon(ctx):
    await ctx.message.delete()
    try:
        r = requests.get("https://api.racc.lol/raccoon", timeout=15)
        await ctx.send(file=discord.File(io.BytesIO(r.content), "raccoon.jpg"))
    except Exception: pass

@bot.command()
async def achievement(ctx, *, text: str = None):
    await ctx.message.delete()
    if not text: return
    try:
        r = requests.get("https://api.alexflipnote.dev/achievement", params={"text": text, "icon": 1}, timeout=15)
        if r.status_code == 200: await ctx.send(file=discord.File(io.BytesIO(r.content), "achievement.png"))
    except Exception: pass

@bot.command()
async def challenge(ctx, *, text: str = None):
    await ctx.message.delete()
    if not text: return
    try:
        r = requests.get("https://api.alexflipnote.dev/challenge", params={"text": text, "icon": 1}, timeout=15)
        if r.status_code == 200: await ctx.send(file=discord.File(io.BytesIO(r.content), "challenge.png"))
    except Exception: pass

def fcfont(size):
    for p in ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        try: return ImageFont.truetype(p, size)
        except Exception: continue
    return ImageFont.load_default()

def fccircle(url, size=40):
    r = requests.get(url, timeout=10)
    img = Image.open(io.BytesIO(r.content)).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out

def fcwrap(text, font, max_width, draw):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        words, cur = para.split(" "), ""
        for w in words:
            test = (cur + " " + w).strip()
            if draw.textlength(test, font=font) <= max_width: cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
    return lines

def fcrender(username, avatar_url, content, timestamp, channel_name=None):
    padding, avatar_size, gap, line_height, width = 16, 40, 16, 22, 720
    header_h = 40 if channel_name else 0
    font = fcfont(16)
    font_header = fcfont(15)
    tmp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(tmp)
    lines = fcwrap(content, font, width - padding * 2 - avatar_size - gap, d)
    body_h = padding * 2 + max(avatar_size, 20 + len(lines) * line_height)
    total_h = header_h + body_h
    img = Image.new("RGBA", (width, total_h), (49, 51, 56, 255))
    draw = ImageDraw.Draw(img)
    y_offset = 0
    if channel_name:
        draw.line([(0, header_h - 1), (width, header_h - 1)], fill=(30, 31, 34, 255))
        draw.text((padding + 4, header_h // 2 - 8), f"#  {channel_name}", font=font_header, fill=(242, 243, 245))
        y_offset = header_h
    try:
        av = fccircle(avatar_url, avatar_size)
        img.paste(av, (padding, y_offset + padding), av)
    except Exception: pass
    x = padding + avatar_size + gap
    name_y = y_offset + padding
    draw.text((x, name_y), username, font=font, fill=(242, 243, 245))
    name_w = d.textlength(username, font=font)
    draw.text((x + name_w + 8, name_y), timestamp, font=font, fill=(148, 155, 164))
    y = name_y + 20
    for line in lines:
        draw.text((x, y), line, font=font, fill=(219, 222, 225))
        y += line_height
    return img

@bot.command(aliases=["fc"])
async def fakechat(ctx, target: discord.User = None, *, message: str = None):
    await ctx.message.delete()
    if not target or not message:
        await ctx.send("`[ x ]` .fakechat <@user> <message>", delete_after=5)
        return
    now = datetime.datetime.now()
    ts = f"Today at {now.strftime('%I').lstrip('0') or '12'}:{now.strftime('%M %p')}"
    try:
        img = fcrender(target.display_name, str(target.display_avatar.url), message, ts, ctx.channel.name if ctx.guild else None)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        await ctx.send(file=discord.File(buf, "fakechat.png"))
    except Exception: pass

@bot.command()
async def specs(ctx):
    await ctx.message.delete()
    try: import psutil
    except ImportError:
        await ctx.send("`[ x ]` pip install psutil", delete_after=5)
        return
    try:
        up = int(time.time() - psutil.boot_time())
        await ctx.send(f"**OS** `{platform.system()} {platform.release()}`\n**Host** `{platform.node()}`\n**CPU** `{platform.processor() or 'unknown'}`\n**RAM** `{psutil.virtual_memory().used // 1_000_000_000}/{psutil.virtual_memory().total // 1_000_000_000} GB`\n**Disk** `{psutil.disk_usage('/').total // 1_000_000_000} GB`\n**Python** `{platform.python_version()}`\n**Uptime** `{up // 3600}h {(up % 3600) // 60}m`")
    except Exception: pass

@bot.command()
async def clearcache(ctx):
    await ctx.message.delete()
    import shutil
    n = 0
    for path in ("data/cache", "cache"):
        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=True)
                os.makedirs(path, exist_ok=True)
                n += 1
            except Exception: pass
    await ctx.send(f"`[ clearcache ]` {n} folder(s) cleared", delete_after=5)

@bot.command()
async def inviteinfo(ctx, invite: str = None):
    await ctx.message.delete()
    if not invite: return
    try:
        r = requests.get(f"https://discord.com/api/v10/invites/{invite.split('/')[-1].split('?')[0]}?with_counts=true&with_expiration=true", headers=apihdrs(), timeout=10)
        if r.status_code != 200: return
        d = r.json()
        g, ch, inv = d.get("guild") or {}, d.get("channel") or {}, d.get("inviter") or {}
        await ctx.send(f"**Server** `{g.get('name', '?')}`\n**ID** `{g.get('id', '?')}`\n**Members** `{d.get('approximate_member_count', '?')}`\n**Online** `{d.get('approximate_presence_count', '?')}`\n**Channel** `{ch.get('name', '?')}`\n**Inviter** `{inv.get('username', 'unknown')}`")
    except Exception: pass

@bot.command()
async def hiddenchannels(ctx):
    await ctx.message.delete()
    if not ctx.guild: return
    hidden = [f"#{c.name}" for c in ctx.guild.channels if not c.permissions_for(ctx.author).view_channel]
    if not hidden: await ctx.send("`[ hiddenchannels ]` none", delete_after=5)
    else: await ctx.send(f"`[ hiddenchannels ]` ({len(hidden)})\n" + "\n".join(f"> {h}" for h in hidden[:30]))

@bot.command()
async def tickets(ctx):
    await ctx.message.delete()
    if not ctx.guild: return
    t = [f"#{c.name}" for c in ctx.guild.channels if "ticket" in c.name.lower()]
    if not t: await ctx.send("`[ tickets ]` none", delete_after=5)
    else: await ctx.send(f"`[ tickets ]` ({len(t)})\n" + "\n".join(f"> {x}" for x in t))

@bot.command()
async def dmpurge(ctx, amount: int = 10, user_id: int = None):
    await ctx.message.delete()
    if not user_id: return
    try:
        user = await bot.fetch_user(user_id)
        dm = await user.create_dm()
    except Exception: return
    n = 0
    async for m in dm.history(limit=amount):
        if m.author == bot.user:
            try:
                await m.delete()
                n += 1
                await asyncio.sleep(0.75)
            except Exception: pass
    await ctx.send(f"`[ dmpurge ]` deleted {n} message(s)", delete_after=5)

@bot.command()
async def weather(ctx, *, city: str = None):
    await ctx.message.delete()
    if not city: return
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1", timeout=10).json()
        if not geo.get("results"): return
        lat, lon, name = geo["results"][0]["latitude"], geo["results"][0]["longitude"], geo["results"][0]["name"]
        cur = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code", timeout=10).json()["current"]
        await ctx.send(f"> `[ weather ]` {name}\n> temp: {cur['temperature_2m']}C\n> humidity: {cur['relative_humidity_2m']}%\n> wind: {cur['wind_speed_10m']} km/h")
    except Exception: pass

@bot.command()
async def translate(ctx, lang: str = None, *, text: str = None):
    await ctx.message.delete()
    if not lang or not text: return
    try: await ctx.send(f"> `[ translate {lang} ]` {requests.get('https://api.mymemory.translated.net/get', params={'q': text, 'langpair': f'auto|{lang}'}, timeout=10).json()['responseData']['translatedText']}")
    except Exception: pass

@bot.command(aliases=["p"])
async def price(ctx, symbol: str = None, currency: str = "usd"):
    await ctx.message.delete()
    if not symbol: return
    cur = currency.lower()
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": symbol.lower(), "vs_currencies": cur, "include_24hr_change": "true"}, timeout=10).json()
        if symbol.lower() not in r:
            hits = requests.get("https://api.coingecko.com/api/v3/search", params={"query": symbol}, timeout=10).json()
            if not hits.get("coins"): return
            symbol = hits["coins"][0]["id"]
            r = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": symbol, "vs_currencies": cur, "include_24hr_change": "true"}, timeout=10).json()
        d = r[symbol.lower()]
        await ctx.send(f"> `[ price ]` {symbol.upper()}: ${d.get(cur, '?')} {cur.upper()}\n> 24h: {d.get(cur + '_24h_change', 0):.2f}%")
    except Exception: pass

@bot.command()
async def news(ctx, *, topic: str = None):
    await ctx.message.delete()
    try:
        r = requests.get(f"https://news.google.com/rss/search?q={topic}" if topic else "https://news.google.com/rss", timeout=10)
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", r.text)[:5] or re.findall(r"<title>(.*?)</title>", r.text)[1:6]
        await ctx.send("`[ news ]`\n" + "\n".join(f"> {t}" for t in titles))
    except Exception: pass

@bot.command()
async def ytsearch(ctx, *, query: str = None):
    await ctx.message.delete()
    if not query: return
    try:
        ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', requests.get("https://www.youtube.com/results", params={"search_query": query}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text)
        if ids: await ctx.send(f"> `[ ytsearch ]` https://youtu.be/{ids[0]}")
    except Exception: pass

@bot.command()
async def github(ctx, username: str = None):
    await ctx.message.delete()
    if not username: return
    try:
        u = requests.get(f"https://api.github.com/users/{username}", timeout=10).json()
        if "login" in u: await ctx.send(f"> `[ github ]` {u['login']}\n> repos: {u.get('public_repos')} | followers: {u.get('followers')}\n> {u.get('html_url')}")
    except Exception: pass

def parsedur(s):
    if not s: return None
    m = re.match(r"^(\d+)([smhd])$", s.strip(), re.IGNORECASE)
    if not m: return None
    return int(m.group(1)) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2).lower()]

@bot.command()
async def remind(ctx, duration: str = None, *, note: str = None):
    await ctx.message.delete()
    secs = parsedur(duration)
    if secs and note:
        data["reminders"].append({"user_id": ctx.author.id, "note": note, "fire_at": time.time() + secs})
        save_data()

@bot.command()
async def reminders(ctx):
    await ctx.message.delete()
    if not data["reminders"]: await ctx.send
