import time
import classes


c_time = time.time()


def init(*args):
    pass


async def on_message(ctx, listener: classes.AchievementsListener):
    if ctx.author.bot:
        return

    # print(ctx.author.name, "wrote message")

    database = listener.database

    today_message_count = database.get_field(ctx.guild, ctx.author.mention, "today_message_count")

    if today_message_count is None:
        today_message_count = 0
    today_message_count = int(today_message_count)

    today_message_count += 1

    database.set_field(ctx.guild, ctx.author.mention, "today_message_count", today_message_count)

    acievements = listener.precreated_achievements["messages_days"]

    for achieve in acievements:
        updated = database.get_field(ctx.guild, ctx.author.mention, f"{achieve}_any_days_updated")

        if updated == "True":
            continue

        updated = False

        any_days = database.get_field(ctx.guild, ctx.author.mention, f"{achieve}_any_days")

        if any_days is None:
            any_days = 0
        any_days = int(any_days)

        if today_message_count >= acievements[achieve]["messages"]:
            any_days += 1

        database.set_field(ctx.guild, ctx.author.mention, f"{achieve}_any_days", any_days)

        if any_days >= acievements[achieve]["days"]:
            listener.add_achievement(ctx.guild, ctx.author,
                                     achieve,
                                     acievements[achieve]["description"],
                                     acievements[achieve]["rare"])

            database.set_field(ctx.guild, ctx.author.mention, f"{achieve}_any_days_updated", True)


def check(client, guild, member, listener, database):
    if (time.time()-c_time)/100/60/60 > 24:
        acievements = listener.precreated_achievements["messages_days"]

        for achieve in acievements:
            updated = database.get_field(guild, member, f"{acievements[achieve]}_any_days_updated")

            if updated is True:
                database.set_field(guild, member, f"{acievements[achieve]}_any_days_updated", False)
                continue

            database.set_field(guild, member, f"{acievements[achieve]}_any_days", 0)
