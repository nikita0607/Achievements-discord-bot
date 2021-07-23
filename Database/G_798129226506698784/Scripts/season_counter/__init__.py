from classes import AchievementsListener, Database


def init(*args):
    pass


def check(client, guild, member, listener: AchievementsListener, database):
    achieves = [achieve[0] for achieve in database.get_achievements(guild, member.mention)]
    # print(member.display_name, achieves)
    loaded_achieves = listener.precreated_achievements.copy()
    seasons = loaded_achieves["seasons"]
    del loaded_achieves["seasons"]

    seasons_counter = {}

    for achieve in loaded_achieves:
        for _achieve_name in loaded_achieves[achieve]:
            _achieve = loaded_achieves[achieve][_achieve_name]
            # _achieve = _achieve[_achieve]
            # print("A:", _achieve)
            if f"season_{_achieve['season']}" not in seasons_counter:
                seasons_counter[f"season_{_achieve['season']}"] = 0
            if _achieve_name not in achieves:
                continue
            seasons_counter[f"season_{_achieve['season']}"] += 1

    # print(seasons_counter)
    for season in seasons:
        achieve = seasons[season]["achieve"]

        if achieve["name"] in achieves:
            continue

        if seasons_counter[season] >= seasons[season]["count"]:
            achieve = seasons[season]["achieve"]
            listener.add_achievement(guild, member,
                                     achieve["name"],
                                     achieve["description"],
                                     achieve["rare"])
