from discord.ext import commands


def init(client: commands.Bot):
    pass

async def on_message(ctx, listener):
    if ctx.author.bot:
        return

    database = listener.database

    field = database.get_field(ctx.guild, ctx.author.mention, "message_count")
    if field is None:
        field = 0
    field = int(field) + 1

    database.set_field(ctx.guild, ctx.author.mention, "message_count", field)
    # print("Message count:", field)

    guild = ctx.guild
    member = ctx.author

    av_achive = database.get_achievements(guild, member.mention)
    av_achive_name = [achive[0] for achive in av_achive]

    message_count = field

    for m_achieve in listener.precreated_achievements['messages_any_day']:
        # print(av_achive, av_achive_name)
        if m_achieve in av_achive_name:
            continue

        achive = listener.precreated_achievements['messages_any_day'][m_achieve]
        if message_count >= achive["message_count"]:
            listener.add_achievement(guild, member, m_achieve, achive["description"], achive["rare"])


##### CHECK #####


def voice_check(guild, member, listener, database):
    av_achive = database.get_achievements(guild, member.mention)
    av_achive_name = [achive[0] for achive in av_achive]

    voice_ch_time = database.get_field(guild, member.mention, "vc_time")

    # print(voice_ch_time, member.name)

    if voice_ch_time is None:
        voice_ch_time = 0

    voice_ch_time = float(voice_ch_time)

    for t_ahcieve in listener.precreated_achievements['voicechannels_timed_achievements']:
        # print(av_achive, av_achive_name)
        if t_ahcieve in av_achive_name:
            continue

        achive = listener.precreated_achievements['voicechannels_timed_achievements'][t_ahcieve]
        if voice_ch_time > achive["time"]:
            listener.add_achievement(guild, member, t_ahcieve, achive["description"], achive["rare"])


def check(client, guild, member, listener, database):
    voice_check(guild, member, listener, database)
