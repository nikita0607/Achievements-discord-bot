import re
import typing

import DiscordUtils

from Cybernator import Paginator
from functools import wraps
from classes import *

intents = discord.Intents.default()
intents.members = True

with open("config.json") as file:
    config = json.load(file)

use_gui = True

command_prefix = "|baldej| "

client = commands.Bot(intents=intents, command_prefix=command_prefix)
database = Database("Добро пожаловать на сервер!<Быть участником сервера><low>")
achievements_listener = AchievementsListener(database)

loaded_emojis = {}
achievements_colors = {}

for rare in achievements_listener.rares:
    try:
        achievements_colors[rare] = discord.Color(0).__getattribute__(achievements_listener.rares[rare].lower())()
    except:
        exec(f"achievements_colors[rare] = discord.Colour({achievements_listener.rares[rare]})")

work_chat = {}
admin_roles = []

for line in database.get_all_workchat_id():
    guild_id = line[0]
    channel_id = line[1]

    work_chat[guild_id] = channel_id
    print(f"Load work chat to {guild_id}: {channel_id}")

print(work_chat)

vc_chat_calc = {}
achievements_listeners = {}


def add_achievement(guild: Guild, member: Member, achieve_text, achieve_description, achieve_rare):
    database.add_achievement(guild, member.mention, achieve_text, achieve_rare, achieve_description)

    if work_chat[guild.id] is not None:
        emb = Embed(title="Ачивка!", colour=(
            achievements_colors[achieve_rare] if achieve_rare in achievements_colors else discord.Colour(0xffffff)
        ))

        emb.set_author(name=member.name, icon_url=member.avatar_url)
        emb.add_field(name=f"{achieve_text}.", value=f"Описание: {achieve_description}")

        send_message(client.get_channel(work_chat[guild.id]), embed=emb)


def get_all_members(guild: Guild):
    return [member for member in guild.members if not member.bot]


def get_member(guild, mention_or_name):
    for member in get_all_members(guild):
        if member.mention == mention_or_name.replace("!", "") or \
                member.display_name == mention_or_name or \
                member.name == mention_or_name:
            return member


def get_member_from_text(guild, user, text) -> tuple:
    if not len(text):
        return None, ""

    for member in get_all_members(guild):
        if member.mention == text.split()[0]:
            text = text.replace(member.mention, "")
            while text.startswith(" "):
                text = text.replace(" ", "", 1)
            return member, text

        elif member.name in text:
            text = text.replace(member.name, "")
            while text.startswith(" "):
                text = text.replace(" ", "", 1)
            return member, text

        elif member.display_name in text:
            text = text.replace(member.display_name
                                , "")
            while text.startswith(" "):
                text = text.replace(" ", "", 1)
            return member, text

    return user, text


def _has_admin_role(member: Member):
    roles = [role.name for role in member.roles]

    for role in roles:
        if role in database.get_admin_roles(member.guild):
            return True

    return False


def has_admin_role(*items):

    def dec(ctx: commands.context.Context):

        if _has_admin_role(ctx.author):
            return True
        else:
            send_message(ctx.channel, message=f"{ctx.author.mention}, у вас недостаточно прав!")
            return False

    return commands.check(dec)


def commands_error_handler(func):

    @wraps(wrapped=func)
    async def wraper(ctx: commands.context.Context):
        try:
            await func(ctx)
        except Exception as ex:
            bot_logger.log(f"Error: Guild:'{ctx.guild.name}', message:'{ctx.message.content}', error:'{ex}:{ex.__traceback__.tb_lineno}'")
            await send_error(ctx, "Неизвестная ошибка!")
    return wraper


def send_message(channel, message=None, embed=None):
    asyncio.run_coroutine_threadsafe(_send_message(channel, message, embed), client.loop)


async def _send_message(channel, message=None, embed=None):

    try:
        await channel.send(message, embed=embed)
    except Exception as ex:
        print(ex)


def get_chat(ctx):
    if work_chat[ctx.guild.id] is not None:
        return client.get_channel(work_chat[ctx.guild.id])
    return ctx


def normalize_content(content):
    _c = content.split()[:2]
    return content.replace(_c[0], "").replace(_c[1], "")[2:].strip()


def get_args_from_content(content: str, normolized=False):
    if not normolized:
        content = normalize_content(content)

    kwargs = {}
    args = []

    str_kwargs: typing.List[str] = re.findall(" [^\s]*=\".*?\"", content)
    for _id, arg in enumerate(str_kwargs):
        content = content.replace(arg, "", 1)
        str_kwargs[_id] = arg[1:]

    simple_kwargs: typing.List[str] = re.findall("[^\s]*=[^\s]*", content)

    for _id, arg in enumerate(simple_kwargs):
        content = content.replace(arg, "", 1)
        simple_kwargs[_id] = simple_kwargs[_id].strip()

    # print(str_kwargs, simple_kwargs, sep="\n")

    args = content.strip().split()

    for arg in str_kwargs:
        _arg = arg.split("=")
        kwargs[_arg[0]] = _arg[1]

    for arg in simple_kwargs:
        _arg = arg.split("=")
        kwargs[_arg[0]] = _arg[1]

    return args, kwargs


async def send_error(ctx, error_msg):
    emb = Embed(colour=discord.Color.red())
    emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    emb.add_field(name="Ошибка", value=error_msg)

    await ctx.send(f"{ctx.author.mention}", embed=emb)


async def send_succes(ctx, succes_msg):
    emb = Embed(colour=discord.Color.green())
    emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    emb.add_field(name="Успешно", value=succes_msg)

    await ctx.send(f"{ctx.author.mention}", embed=emb)

init(client, add_achievement, _vc_chat_calc=vc_chat_calc)


######################  DISCORD COMMANDS ######################


bot_logger = Log("discordBot")
tracker = DiscordUtils.InviteTracker(client)


def disable():
    bot_logger.log("Disabling bot")

    for guild in client.guilds:
        for channel in guild.channels:
            if isinstance(channel, VoiceChannel):
                for member in channel.members:
                    g_time = database.get_field(member.guild, member.mention, "vc_time")
                    g_time = (float(g_time) if g_time is not None else 0)

                    database.set_field(member.guild, member.mention, "vc_time",
                                       g_time + time.time() - vc_chat_calc[guild.id][member.mention])
                    achievements_listeners[guild.id].check()
                    del vc_chat_calc[guild.id][member.mention]


###### Invite Checker ######

@client.event
async def on_invite_create(invite):
    await tracker.update_invite_cache(invite)

@client.event
async def on_guild_join(guild):
    await tracker.update_guild_cache(guild)

@client.event
async def on_invite_delete(invite):
    await tracker.remove_invite_cache(invite)

@client.event
async def on_guild_remove(guild):
    await tracker.remove_guild_cache(guild)

@client.event
async def on_member_join(member):
    inviter = await tracker.fetch_inviter(member)
    invite_count = database.get_field(member.guild, inviter.mention, "invite_count")
    if invite_count is None:
        invite_count = 0
    else:
        invite_count = int(invite_count)

    # print(f"{inviter.name} has {invite_count+1} invites!")

    add_achievement(member.guild, member, "Добро пожаловать на сервер", "Быть участником сервера", "low")
    database.new_member(member.guild, member.mention)
    database.set_field(member.guild, inviter.mention, "invite_count", invite_count+1)

is_ready = False


@client.event
async def on_ready():
    global is_ready

    if is_ready:
        return
    is_ready = True

    await tracker.cache_invites()

    bot_logger.log("\nStart bot")

    for emoji in client.emojis:
        loaded_emojis[emoji.name[5:]] = emoji

    for guild in client.guilds:
        database.add_guild(guild)
        vc_chat_calc[guild.id] = {}

        achievements_listeners[guild.id] = AchievementsListener(database, f"Database/G_{guild.id}/", guild=guild)
        asyncio.run_coroutine_threadsafe(achievements_listeners[guild.id].run(guild), client.loop)

        if guild.id in work_chat:
            continue
        work_chat[guild.id] = None

    print("Ready!")
    bot_logger.log("Bot is ready!")

@client.event
async def on_voice_state_update(member: Member, before: discord.VoiceState, after: discord.VoiceState):

    if before.channel is None and after.channel is not None:
        vc_chat_calc[member.guild.id][member.mention] = time.time()
        bot_logger.log(f"Member {member.display_name} connected to voice chat on {member.guild.name}!")

    if before.channel is not None and after.channel is None:
        g_time = database.get_field(member.guild, member.mention, "vc_time")
        g_time = (float(g_time) if g_time is not None else 0)

        database.set_field(member.guild, member.mention, "vc_time", g_time + time.time() - vc_chat_calc[member.guild.id][member.mention])

        bot_logger.log(f"Member {member.display_name} disconnected from voice chat on {member.guild.name}!")
        del vc_chat_calc[member.guild.id][member.mention]


@client.command()
@has_admin_role()
async def clear_workchats(ctx: commands.context.Context):
    if ctx.author.name != "Nikita0607":
        return

    bot_logger.log("WorkChats cleared!")
    database.clear_workchats()


@client.command(aliases=['чат'])
@has_admin_role()
async def workchat(ctx: commands.context.Context):
    await ctx.send("Рабочий чат установлен!")

    database.set_workchat_id(ctx.guild.id, ctx.channel.id)
    work_chat[ctx.guild.id] = ctx.channel.id

    bot_logger.log(f"Set WorkChat to {ctx.guild.name}")


@client.command(pass_context=True)
async def delete_all(ctx: commands.context.Context):
    database.delete_all_achievements(ctx.guild, ctx.author.mention)

    emb = Embed(title=f"У пользователя `{ctx.author.name}` были удалены все ачивки!")
    emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

    await ctx.send(embed=emb)


@client.command(aliases=["дать"])
@has_admin_role()
async def give(ctx: commands.context.Context):
    print(get_args_from_content(ctx.message.content))
    msg = ctx.message.content.replace("\n", "")

    msg = msg.replace(" ", "", 1)
    msg = msg.replace(msg.split()[0]+" ", "")

    mention = ctx.author.mention
    achive = msg

    try:
        if msg[0] == "<":
            mention = msg.split()[0]
            achive = msg.replace(msg.split()[0]+" ", "")
        print(achive)
        achive = [
            achive[:achive.index("<")],
             achive[achive.index("<") + 1:achive.index(">")],
             achive[achive.index(">") + 2:-1]
        ]
    except:
        await get_chat(ctx).send("Проверьте правильность введенных данных!")
        return

    if achive[2] not in achievements_colors:
        await get_chat(ctx).send(f"Не существует уровня достижения `{achive[2]}`")
        return
    member = [i for i in client.get_all_members() if i.mention == mention][0]

    add_achievement(ctx.guild, member, achive[0], achive[1], achive[2])


@client.command()
@has_admin_role()
async def get_field(ctx: commands.context.Context):
    content = normalize_content(ctx.message.content)
    member, field_name = get_member_from_text(ctx.guild, ctx.author, content)
    field = database.get_field(ctx.guild, member.mention, field_name)

    if field is None:
        await send_error(ctx, f"Поле `{field_name}` не найдено!")
        return

    await send_succes(ctx, f"{field_name} = {field}")


@client.command()
@has_admin_role()
@commands_error_handler
async def set_field(ctx: commands.context.Context):
    content = normalize_content(ctx.message.content)

    member, field_values = get_member_from_text(ctx.guild, ctx.author, content)
    _, field_values = get_args_from_content(content, True)

    if member is None:
        member = ctx.author

    if not len(field_values):
        await send_error(ctx, f"{command_prefix} set_field ARG1=VAL1 ARG2=VAL2")
        return

    msg = ""
    for arg in field_values:
        database.set_field(ctx.guild, member.mention, arg, field_values[arg])
        msg += f"{arg} = {field_values[arg]}\n"

    await send_succes(ctx, msg)


@client.command(aliases=["роль"])
@has_admin_role()
async def add_role(ctx: commands.context.Context):
    content = ctx.message.content.split()
    if len(content) < 3:
        await send_error(ctx, f"{ctx.author.mention}, вы вообще хоть что-нибудь написали?")
        return

    role = content[2]

    database.add_admin_role(ctx.guild, role)

    await ctx.send(f"Роль {role} успешно сохранена!")


@client.command(aliases=["удалить"])
async def delete(ctx: commands.context.Context):
    content = ctx.message.content.split()[1:]
    if len(content) < 2:
        await ctx.send(f"{ctx.author.mention}, вы вообще хоть что-нибудь написали?")

    content = content[1:]

    achieve_name = ""

    for part in content:
        achieve_name += part + " "
    achieve_name = achieve_name[:-1]

    member, achieve_name = get_member_from_text(ctx.guild, ctx.author, achieve_name)

    if not len(achieve_name):
        await send_error(ctx, "Напишите название ачивки!")
        return

    if member is None:
        member = ctx.author
    elif not _has_admin_role(ctx.author):
        await send_error(ctx, "У вас недостаточно прав!")
        return

    emb = Embed(title="Удаление ачивок", colour=discord.colour.Colour.red())
    emb.set_author(name=member.name, icon_url=member.avatar_url)
    r_achieve = database.delete_achievement(ctx.guild, member.mention, achieve_name)

    if r_achieve is not None:
        emb.add_field(name=r_achieve[0]+".", value=f"Описание: {r_achieve[1]}")

    if len(emb.fields) < 1:
        emb.add_field(name="Ошибочка", value="Не было удалено ни одной ачивки!")

    await ctx.send(f"{ctx.author.mention}", embed=emb)


@client.command(aliases=["ачивки"])
async def achievements(ctx: commands.context.Context):
    chat = ctx.channel
    if work_chat[ctx.guild.id] is not None:
        chat = client.get_channel(work_chat[ctx.guild.id])

    content = ctx.message.content.split()
    if len(content) > 2:
        content = content[2:]
    else:
        content = []

    msg = ""

    for part in content:
        msg += part + " "
    msg = msg[:-1]

    if not len(msg):
        member = ctx.author
    else:
        member, _ = get_member_from_text(ctx.guild, ctx.author, msg)

        if member is None:
            await send_error(ctx, f"Пользователь '{msg}' не найден!")
            return

    embeds = {}
    for rare in achievements_colors:

        embeds[rare] = [Embed(title=f"Ачивки пользователя {member.name}:", colour=achievements_colors[rare]), 0]
        embeds[rare][0].set_author(name=member.name, icon_url=member.avatar_url)

    for num, achieve in enumerate(database.get_achievements(ctx.guild, member.mention)):
        embeds[achieve[2]][0].add_field(name=f"{achieve[0]}. ", value=f"Описание: {achieve[1]}\n", inline=True)
        embeds[achieve[2]][1] += 1

    for emb in embeds:
        embeds[emb][0].add_field(name="_______ _______ _______ _______ _______ _______ _______ _______",
                                 value=f"Количество {emb.upper()} ачивок: {embeds[emb][1]}")

    embeds = [embeds[i][0] for i in embeds]

    msg = await chat.send(embed=embeds[0])
    page = Paginator(client, msg, embeds, only=ctx.author)

    await page.start()


@client.command(aliases=["база"])
@has_admin_role()
async def load_base(ctx: commands.context.Context):
    await ctx.author.send(f"Database from {ctx.guild.name}",
            file=discord.File(f"Database/G_{ctx.guild.id}/database.db"))

@client.command(aliases=["помощь"])
async def helper(ctx):
    emb = Embed(title="Помощь")
    emb.add_field(name="achievements, ачивки", value="Показать свои/чужие ачивки")
    emb.add_field(name="workchat, чат", value="Установить рабочий чат")
    emb.add_field(name="give, дать", value=f"Выдать ачивку. Пример: {command_prefix}@God#0000 Имя<Описание><rare>")
    emb.add_field(name="role, роль", value=f"Добавить роль для администрации. Пример: {command_prefix}Админ")

    await ctx.send(embed=emb)


@client.event
async def on_message(ctx):
    if ctx.author == client.user:
        return
    await client.process_commands(ctx)
    await achievements_listeners[ctx.guild.id].on_message(ctx)


#################################################################

try:
    client.run(config["token"])
except Exception as _:
    disable()
