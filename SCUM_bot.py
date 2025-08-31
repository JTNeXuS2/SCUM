#Python 3.8 or higher is required.
#py -3 -m pip install -U disnake
#pip3 install python-a2s
#pip install aiofiles

import disnake
from disnake.ext import commands, tasks
from disnake import Intents
import json
import datetime
import requests
import configparser
import re
import unicodedata
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor
from battlemetrics import Battlemetrics
import glob
import aiofiles
import asyncio


shard_count = 2
#cant used
prefix = '/'

#Nothing change more

def read_cfg():
    config = configparser.ConfigParser(interpolation=None)
    try:
        with open('config.ini', 'r', encoding='utf-8') as file:
            config.read_file(file)
    except FileNotFoundError:
        print("Error: Config.ini not found.")
        return None
    return config
async def write_cfg(section, key, value):
    config = read_cfg()
    if f'{section}' not in config:
        config[f'{section}'] = {}
    config[f'{section}'][f'{key}'] = str(f'{value}')

    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def update_settings():
    global token, battlemetric_token, battlemetric_sid, channel_id, message_id, update_time, bot_name, bot_ava, address, command_prefex, webhook_url
    config = read_cfg()
    if config:
        try:
            bot_name = config['botconfig'].get('bot_name', None)
            token = config['botconfig'].get('token', None)
            battlemetric_token = config['botconfig'].get('battlemetric_token', None)
            address = (config['botconfig'].get('ip', '127.0.0.1'), int(config['botconfig'].get('port', 0)))
            battlemetric_sid = config['botconfig'].get('battlemetric_sid', None)
            channel_id = config['botconfig'].get('channel_id', None)
            message_id = config['botconfig'].get('message_id', None)
            bot_ava = config['botconfig'].get('bot_ava', None)
            update_time = config['botconfig'].get('update_time', None)
            command_prefex = config['botconfig'].get('command_prefex', None) and config['botconfig'].get('command_prefex').lower()
            webhook_url = config['botconfig'].get('webhook_url', None)

        except ValueError as e:
            print(f"Error: wrong value in config file {e}")
        except Exception as e:
            print(f"Error: {e}")

token = None
battlemetric_token = None
battlemetric_sid = None
channel_id = None
message_id = None
bot_name = None
bot_ava = None
update_time = 10
address = None
command_prefex = None
webhook_url = None
data_json = None
update_settings()


#bot idents
intents = disnake.Intents.default()
intents.messages = True
intents = disnake.Intents().all()
client = commands.Bot(command_prefix=prefix, intents=intents, case_insensitive=True)
bot = commands.AutoShardedBot(command_prefix=prefix, intents=intents, shard_count=shard_count ,case_insensitive=True)

async def update_avatar_if_needed(bot, bot_name, bot_ava):
    # Проверяем, совпадает ли ссылка на аватар
    current_avatar_url = bot.user.avatar.url if bot.user.avatar else None
    if current_avatar_url != bot_ava:
        try:
            response = requests.get(bot_ava)
            response.raise_for_status()  # Проверка на ошибки HTTP
            data = response.content
            print("Avatar data retrieved successfully.")
            await bot.user.edit(avatar=data)
        except requests.exceptions.RequestException as e:
            print(f"Error update avatar: {e}")

async def request_bm_api():
    try:
    	url_forse = f'https://api.battlemetrics.com/servers/{battlemetric_sid}/force-update'

    	url = f'https://api.battlemetrics.com/servers/{battlemetric_sid}'
    	headers = {
    		'Authorization': f'Bearer {battlemetric_token}',
    		'Accept': 'application/json'
    	}
    	requests.get(url_forse, headers=headers)
    	response = requests.get(url, headers=headers)
    	if response.status_code == 200:
    		server_info = response.json()
    		#print(json.dumps(server_info, indent=4, ensure_ascii=False))
    		return server_info
    	else:
    		print(f'Ошибка запроса: {response.status_code} - {response.text}')
    		return None
    except Exception as e:
        print(f'ERROR request_api >>: {e}')
        return None

@tasks.loop(seconds=int(update_time))
async def update_status():
    global data_json
    update_settings()

    try:
        data_json = await request_bm_api()
        if data_json is None:
            print("ERROR: data_json is None")
            return
        attributes = data_json.get('data', {}).get('attributes', {})

        name = attributes.get('name', 'N/A')
        ip = attributes.get('ip', 'N/A')
        port = attributes.get('port', 'N/A')
        players = attributes.get('players', 'N/A')
        maxPlayers = attributes.get('maxPlayers', 'N/A')
        status = attributes.get('status', 'N/A')
        time = attributes.get('details', {}).get('time', 'N/A')
        '''
        print(f"Название сервера: {name}")
        print(f"IP: {ip}")
        print(f"Порт: {port}")
        print(f"Игроки: {players} / {maxPlayers}")
        print(f"Статус: {status}")
        print(f"Время: {time}")
        '''
        activity = disnake.Game(name=f"{status}: {players}/{maxPlayers}")
        await bot.change_presence(status=disnake.Status.online, activity=activity)

        if bot.user.name != bot_name:
            await bot.user.edit(username=bot_name)

        async def upd_msg():
            uptime_seconds = metrics["uptime"]
            hours = f"{uptime_seconds // 3600:02}"
            minutes = f"{(uptime_seconds % 3600) // 60:02}"
            message = (
                f":earth_africa:Direct Link: **{settings['PublicIP']}:{settings['PublicPort']}**\n"
                f":map: Guid: **{info['worldguid']}**\n"
                f":green_circle: Online: **{player_count}/{max_players}**\n"
                f":film_frames: FPS: **{metrics['serverfps']}**\n"
                f":asterisk: Day: **{metrics['days']}**\n"
                f":timer: UpTime: **{hours}:{minutes}**\n"
                f":newspaper: Ver: **{info['version']}**\n"
                f"============ Server Settings ============\n"
                f"PVP:      **{settings['bIsPvP']}**\n"
                f"HardCore: **{settings['bHardcore']}**\n"
                f"Exp Rate: **{settings['ExpRate']}**\n"
                f"Drop Loot: **{settings['DeathPenalty']}**\n"
                f"Lost Pal: **{settings['bPalLost']}**\n"
                f"Decay Camps: **{settings['AutoResetGuildTimeNoOnlinePlayers']}h**\n"
                f"Base Camps: **{settings['BaseCampMaxNumInGuild']}**\n"
                f"Invaders: **{settings['bEnableInvaderEnemy']}**\n"
            )
            addition_embed = disnake.Embed(
                title=f"**{info['servername']}**",
                colour=disnake.Colour.green(),
                description=f"{message}",
            )
            try:
                channel = await bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id)

                if message:
                    await message.edit(content=f'Last update: {datetime.datetime.now().strftime("%H:%M")}', embed=addition_embed)
            except Exception as e:
                print(f'Failed to fetch channel, message or server data. Maybe try /{command_prefex}_sendhere\n {e}')
        #await upd_msg()
    except Exception as e:
        print(f'ERROR >>: {e}')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}\nBot Shards: {bot.shard_count}')
    print('Invite bot link to discord (open in browser):\nhttps://discord.com/api/oauth2/authorize?client_id='+ str(bot.user.id) +'&permissions=8&scope=bot\n')
    try:
        await update_avatar_if_needed(bot, bot_name, bot_ava)
    except Exception as e:
        print(f'update_avatar ERROR >>: {e}')
    try:
        update_status.start()
    except Exception as e:
        print(f'ERROR update_status >>: {e}')

#events
@bot.event
async def on_message(message):
    if message.author == client.user:		#отсеим свои сообщения
        return;
    if message.author.bot:
        return;
    if message.content.startswith(''):
        return

#template admin commands
'''
@bot.slash_command(description="Add SteamID to Whitelist")
async def admin_cmd(ctx: disnake.ApplicationCommandInteraction, steamid: str):
    if ctx.author.guild_permissions.administrator:
        print(f'it admin command')
        try:
            await ctx.send(f'admin command try', ephemeral=True)
        except Exception as e:
            await ctx.send(f'ERROR Adding SteamID', ephemeral=True)
    else:
        await ctx.response.send_message("❌ You do not have permission to run this command.", ephemeral=True)
'''
#template users command
'''
@bot.slash_command(description="Show commands list")
async def help(ctx):
    await ctx.send('**==Support commands==**\n'
    f' Show commands list```{prefix}help```'
    f' Show server status```{prefix}moestatus```'
    f'\n **Need admin rights**\n'
    f' Auto send server status here```{prefix}sendhere```'
    f' Add server to listing```{prefix}serveradd adress:port name```',
    ephemeral=True
    )
'''

try:
    bot.run(token)
except disnake.errors.LoginFailure:
    print(' Improper token has been passed.\n Get valid app token https://discord.com/developers/applications/ \nscreenshot https://junger.zzux.com/webhook/guide/4.png')
except disnake.HTTPException:
    print(' HTTPException Discord API')
except disnake.ConnectionClosed:
    print(' ConnectionClosed Discord API')
except disnake.errors.PrivilegedIntentsRequired:
    print(' Privileged Intents Required\n See Privileged Gateway Intents https://discord.com/developers/applications/ \nscreenshot http://junger.zzux.com/webhook/guide/3.png')
