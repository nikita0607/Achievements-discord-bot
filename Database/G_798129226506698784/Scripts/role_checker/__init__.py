from discord import Member

from classes import *


def check(client, guild, member: Member, listener: AchievementsListener, database):

    roles = [role.name for role in member.roles]
    achieves = [achieve[0] for achieve in database.get_achievements(guild, member.mention)]

    loaded_roles = listener.precreated_achievements["has_role_achievements"]

    for achieve in loaded_roles:
        if achieve in achieves:
            continue

        _achieve = loaded_roles[achieve]

        for role in _achieve["role"].split(","):
            if role in roles:
                break

        else:
            continue

        listener.add_achievement(guild, member, achieve, _achieve["description"], _achieve["rare"])
