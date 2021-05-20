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
    for ID in ids:
        r = requests.get(mdlink + "/" + type, params={"ids[]": ID})
        names.append(r.json()["results"][0]["data"]["attributes"]["name"])
    return names
