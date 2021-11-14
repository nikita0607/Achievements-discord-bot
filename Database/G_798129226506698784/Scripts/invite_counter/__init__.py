def check(client, guild, member, listener, database):
    invite_count = database.get_field(guild, member.mention, "invite_count")

    if invite_count is None:
        return
    invite_count = int(invite_count)

    invites = listener.precreated_achievements["invites"]

    member_achieves = [x[0] for x in database.get_achievements(guild, member.mention)]

    for achieve_name in invites:
        if achieve_name in member_achieves:
            continue

        achieve = invites[achieve_name]

        if invite_count >= achieve["invite_count"]:
            listener.add_achievement(guild, member, achieve_name, achieve["description"], achieve["rare"])