import asyncio
import importlib
import time
import sqlite3
import json
import os

import discord

from discord.ext import commands
from discord import Embed
from discord.message import Member, Guild
from discord.channel import VoiceChannel


client = None
add_achievement = lambda *x, **y: None
vc_chat_calc = None 


def init(_client, _add_achievement, _vc_chat_calc):
    global client
    global add_achievement
    global vc_chat_calc

    vc_chat_calc = _vc_chat_calc
    client = _client
    add_achievement = _add_achievement


class Log:

    def __init__(self, _from=None, log_path=""):
        if not os.path.isfile(f"{log_path}logs.log"):
            open(f"{log_path}logs.log", 'w', encoding="utf-8").close()
        self.log_path = log_path
        self._from = _from

    def log(self, text="", _from=""):
        text, _from = str(text), str(_from)

        if not len(_from) and self._from is not None:
            _from = self._from

        _s = f"{time.strftime('%d/%m/%y %T')}: {_from}: {text}\n"

        with open(f"{self.log_path}logs.log", encoding="utf-8") as file:
            lines = file.readlines()

            if len(lines) > 100:
                with open(f"{self.log_path}old_log_{time.strftime('%d_%m_%y %H_%M')}.log", 'w', encoding="utf-8") as new_file:
                    new_file.writelines(lines)

                file.close()

                with open(f"{self.log_path}logs.log", "w") as new_file:
                    new_file.write("")

                file = open(f"{self.log_path}logs.log", encoding="utf-8")

        with open(f"{self.log_path}logs.log", "a", encoding="utf-8") as file:
            file.write(_s)

    def error_handler(self, func):

        def dec(*args, **kwargs):
            # print("Handler!")
            try:
                func(*args, **kwargs)
            except Exception as ex:
                self.log(f"Error while running {func.__name__}: {ex}", f"{self._from} ErrorHandler")

        return dec


class Database:
    logs = Log("Database")

    def __init__(self, welcome_achievement):
        for g_path in os.listdir("Database"):
            if ".py" in g_path:
                continue
            with sqlite3.connect(f"Database/{g_path}/database.db") as db:
                sql = db.cursor()

                sql.execute("CREATE TABLE IF NOT EXISTS members (mention, achieve, fields)")

        self.welcome_achievement = welcome_achievement

        self.logs = Log("Database")

        self.scripts = {}

    # @logs.error_handler
    def add_guild(self, guild):
        try:
            os.mkdir(f"Database/G_{guild.id}")
            os.mkdir(f"Database/G_{guild.id}/Scripts")
        except:
            pass

        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute("CREATE TABLE IF NOT EXISTS members (mention TEXT, achieve TEXT, vc_time TEXT)",)
            sql.execute("CREATE TABLE IF NOT EXISTS scripts (name)")

            self.logs.log(f"Add new guild {guild.name} <{guild.id}>")

        if not os.path.isfile(f"Database/G_{guild.id}/achievements.json"):
            ach = open("achievements.json").read()
            with open(f"Database/G_{guild.id}/achievements.json", 'w') as file:
                file.write(ach)

        if str(guild.id) not in self.scripts:
            self.scripts[f"{guild.id}"] = []



    @logs.error_handler
    def new_member(self, guild: Guild, mention):
        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM members WHERE mention=?", (mention,))

            if sql.fetchone() is not None:
                return False

            sql.execute("INSERT INTO members VALUES (?, ?, '')", (mention, self.welcome_achievement))

        return True

    def get_fields(self, guild: Guild, mention):
        self.new_member(guild, mention)

        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM members WHERE mention=?", (mention,))

            fields = sql.fetchone()[2]

            if not len(fields): return None

            return [[x.split("=")[0], x.split("=")[1]] for x in fields.split(",")]

    def get_field(self, guild: Guild, mention, name):
        self.new_member(guild, mention)

        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM members WHERE mention=?", (mention,))

            fields = sql.fetchone()[2]

            if not len(fields): return None
            # print(fields.split(",")[0].split("="))
            fields = [[x.split("=")[0], x.split("=")[1]] for x in fields.split(",") if len(x)]

            for i in fields:
                if i[0] == name:
                    return i[1]

            return None

    def set_field(self, guild: Guild, mention, name, value):
        self.new_member(guild, mention)

        field = self.get_field(guild, mention, name)

        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute("SELECT * FROM members WHERE mention=?", (mention,))

            if field is None:
                field = f"{name}={value},"
                fields = sql.fetchone()[2] + field

            else:
                fields = sql.fetchone()[2].replace(f"{name}={field},", f"{name}={str(value)},")

            # print(fields)
            sql.execute("UPDATE members SET fields=? WHERE mention=?", (fields, mention))

    @logs.error_handler
    def add_achievement(self, guild, mention, achieve_text, achieve_rare, achieve_description):
        self.new_member(guild, mention)

        av_achieve = [achieve[0] for achieve in self.get_achievements(guild, mention)]

        if achieve_text in av_achieve:
            return False

        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute(f"SELECT * FROM members WHERE mention=?", (mention,))

            achieve = sql.fetchone()[1]
            achieve += f" {achieve_text}<{achieve_description}><{achieve_rare}>"

            sql.execute(f"UPDATE members SET achieve=? WHERE mention=?", (achieve, mention))

        self.logs.log(f"Add achieve in {guild.name} to {mention}: {achieve_text}<{achieve_description}><{achieve_rare}>")

        return True

    @logs.error_handler
    def clear_workchats(self):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute("UPDATE guilds SET channel_id=''")

            self.logs.log("Clear all WorkChats")

    @logs.error_handler
    def delete_all_achievements(self, guild, mention):
        self.new_member(guild, mention)

        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute(f"UPDATE members SET achieve=?, vc_time=0 WHERE mention=?", (self.welcome_achievement, mention))

    def delete_achievement(self, guild, mention, achieve_name):
        self.new_member(guild, mention)
        achieves = self.get_achievements(guild, mention)
        cr_achieves = self.welcome_achievement

        ret_achieve = None

        if len(achieves):
            achieves = achieves[1:]

        for achieve in achieves:
            # print(achieve[0], achieve_name)
            if achieve[0] == achieve_name:
                ret_achieve = achieve
                continue

            cr_achieves += f" {achieve[0]}<{achieve[1]}><{achieve[2]}>"

        with sqlite3.connect(f"Database/G_{guild.id}/database.db") as db:
            sql = db.cursor()

            sql.execute(f"UPDATE members SET achieve=? WHERE mention=?", (cr_achieves, mention))

        return ret_achieve

    def add_guild_script(self, guild: Guild, name):
        pass

    def get_guild_scripts(self, guild: Guild):
        try:
            return self.scripts[f"G_{guild.id}"]
        except:
            return []

    @logs.error_handler
    def set_workchat_id(self, guild_id, chat_id):

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM guilds WHERE guild_id=?", (guild_id,))

            if sql.fetchone() is not None:
                sql.execute("UPDATE guilds SET channel_id=? WHERE guild_id=?", (chat_id, guild_id))
                return

            sql.execute("INSERT INTO guilds VALUES (?, ?, ?)", (guild_id, chat_id, "Администратор ачивок"))

    def get_admin_roles(self, guild):
        guild_id = guild.id

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM guilds WHERE guild_id=?", (guild_id,))

            roles = sql.fetchone()

            # print(roles[2])

            if roles is not None:
                return roles[2].split("   ")

            sql.execute("INSERT INTO guilds VALUES (?, ?, ?)", (guild_id, "", "Администратор ачивок"))
            return ["Администратор ачивок"]

    def add_admin_role(self, guild: Guild, role_name):
        guild_id = guild.id

        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM guilds WHERE guild_id=?", (guild_id,))

            if sql.fetchone() is not None:
                roles_str = "Администратор ачивок"

                roles = self.get_admin_roles(guild)
                if role_name not in roles:
                    roles.append(role_name)
                roles.remove("Администратор ачивок")

                for role in roles:
                    roles_str += "   "+role

                sql.execute("UPDATE guilds SET roles=? WHERE guild_id=?", (roles_str, guild_id))
                self.logs.log(f"Добавлена админ. роль на сервер {guild.name}: {role_name}")

                # sql.execute("SELECT * FROM guilds WHERE guild_id=?", (,))

                return

            sql.execute("INSERT INTO guilds VALUES (?, ?, ?)", (guild_id, "", f"   {role_name}"))

            self.logs.log(f"Добавлена админ. роль на сервер {guild.name}: {role_name}")

    def get_all_workchat_id(self):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()
            sql.execute("SELECT * FROM guilds")

            ret = sql.fetchall()

            return ret if ret is not None else []

    def get_achievements(self, guild, mention):
        self.new_member(guild, mention)

        db = sqlite3.connect(f"Database/G_{guild.id}/database.db")
        sql = db.cursor()

        sql.execute(f"SELECT * FROM members WHERE mention=?", (mention,))

        line = sql.fetchone()

        achieves = line[1].replace("> ", ">  ").split("  ")

        # print(achieves)

        return [[i[:i.index("<")], i[i.index("<")+1:i.index(">")], i[i.index(">")+2:-1]] for i in achieves]

    def execute(self, code):
        with sqlite3.connect("database.db") as db:
            sql = db.cursor()

            sql.execute(code)


class AchievementsListener:

    def __init__(self, database: Database, achievements_path="", guild=None):
        self.database = database
        self.achievement_path = achievements_path
        self.guild = guild

        self.logger = Log("Listener", achievements_path)

        self.open_achievements()

        self.scripts = []

        if guild is None:
            return

        for module in os.listdir(f"Database/G_{guild.id}/Scripts"):
            if not os.path.isfile(f"Database/G_{guild.id}/Scripts/{module}/__init__.py"):
                self.logger.log("Ignore path {module}")
                continue

            self.scripts.append(importlib.import_module(f"Database.G_{guild.id}.Scripts.{module}"))
            try:
                self.scripts[-1].init(client)
            except Exception as ex:
                self.logger.log("Exception while init script: ", ex)

    def open_achievements(self):
        self.precreated_achievements = json.load(open(f"{self.achievement_path}achievements.json", encoding="utf-8"))

        self.rares = self.precreated_achievements['rares']
        del self.precreated_achievements['rares']

        self.welcome_achievement = self.precreated_achievements['welcome_achievement']
        del self.precreated_achievements['welcome_achievement']

        self.database.welcome_achievement = self.welcome_achievement

    async def run(self, guild: Guild):
        self.logger.log("Run")
        await asyncio.sleep(2)

        while True:
            members = [member for member in guild.members if not member.bot]

            for channel in guild.channels:
                if isinstance(channel, VoiceChannel):
                    for member in channel.members:
                        # print(member.mention)
                        if member.mention not in vc_chat_calc[guild.id]:
                            vc_chat_calc[guild.id][member.mention] = time.time()
                            self.logger.log(f"Member {member.display_name} connected to voice chat on {guild.name}!")

            await self.check_all(guild, members)

            await asyncio.sleep(0.5)

    async def on_message(self, ctx):
        # print(f"Message from {ctx.author.name}")
        if self.guild is None:
            return
        for script in self.database.scripts[f"{self.guild.id}"]:
            try:
                await script.on_message(ctx, self)
            except AttributeError:
                pass
            except Exception as ex:
                print(ex)

    async def check_all(self, guild, members):
        for member in members:
            await self.check(guild, member)

    async def check(self, guild: Guild, member: Member):
        for script in self.database.scripts[f"{guild.id}"]:
            try:
                await script.check(client, guild, member, self, self.database)
            except:
                try:
                    script.check(client, guild, member, self, self.database)
                except Exception as ex:
                    self.logger.log(f"Exception in {script.__name__}: {ex.__traceback__}, {ex}")

        await asyncio.sleep(0.2)

    def add_achievement(self, guild, member, name, description, rare):
        self.logger.log(f"{member.display_name} has got achievement: {name}")
        add_achievement(guild, member, name, description, rare)