from discord.ext import commands


def init(client: commands.Bot, event):
    print("HellO")

async def on_message(ctx):
    pass


def check(client, guild, member, listener, database):
    av_achive = database.get_achievements(guild, member.mention)
    av_achive_name = [achive[0] for achive in av_achive]

    voice_ch_time = database.get_field(guild, member.mention, "vc_time")

    if voice_ch_time is None:
        voice_ch_time = 0

    voice_ch_time = float(voice_ch_time)

    for t_ahcieve in listener.precreated_achievements['voicechannels_timed_achievements']:
        # print(av_achive, av_achive_name)
        if t_ahcieve in av_achive_name:
            continue

        achive = listener.precreated_achievements['voicechannels_timed_achievements'][t_ahcieve]
        if voice_ch_time > achive["time"]:
            listener.add_achievement(guild, member, t_ahcieve, achive["decription"], achive["rare"])