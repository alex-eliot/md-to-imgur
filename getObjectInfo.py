import requests

def getChapterGroups(chapter):
    groupIDs = []
    for relationship in chapter["relationships"]:
        if relationship["type"] == "scanlation_group":
            groupIDs.append(relationship["id"])
    groups = getNameByID(groupIDs, "group")
    groupsString = ""
    for groupIndex, group in enumerate(groups):
        groupsString += group
        if groupIndex < len(groups) - 1:
            groupsString += " & "

    return groupsString

def getNameByID(ids, type):
    mdlink = "https://api.mangadex.org"
    names = []
    for id in ids:
        r = requests.get(mdlink + "/" + type, params={"ids[]": id})
        names.append(r.json()["results"][0]["data"]["attributes"]["name"])
    return names
