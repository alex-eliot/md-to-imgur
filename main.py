import requests
import json
import os

from sendToImgur import *
from getObjectInfo import *
from githubCommit import *

mdlink = "https://api.mangadex.org"
imgurlink = "https://api.imgur.com"
imgUploadLink = "https://imgur-apiv3.p.rapidapi.com/3/image"
albumCreateLink = "https://imgur-apiv3.p.rapidapi.com/3/album"

with open("./settings.json", 'r') as f:
    data = json.load(f)

headers = {
    "content-type": "application/x-www-form-urlencoded",
    "authorization": "Bearer " + data["imgurToken"],
    "x-rapidapi-key": data["x-rapidapi-key"],
    "x-rapidapi-host": "imgur-apiv3.p.rapidapi.com"
}

query = input("Search for a manga: ")
searchResults = requests.get(mdlink + "/manga", params = {"title": query, "limit": data["searchResultsLimit"]})

if searchResults.status_code == 200:

    mangaQuery = searchResults.json()
    print("\n(#) Found " + str(len(mangaQuery["results"])) + " manga.\n")

    manga_list = []

    for index, item in enumerate(mangaQuery["results"]):
        print("[" + str(index + 1), end=']: ')
        print(item["data"]["attributes"]["title"]["en"])
    mangaSelection = input("\nSelect one: ")

    mangaID = mangaQuery["results"][int(mangaSelection) - 1]["data"]["id"]
    mangaName = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["title"]
    mangaMU = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["links"]["mu"]

    saveOption = input("\n[1]: Save locally\n[2]: Save to imgur album\n\nSelect one: ")
    saveOption = (""
            + "local" * (saveOption == "1")
            + "imgur" * (saveOption == "2")
    )

    if saveOption == "local":
        try:
            os.makedirs("manga/")
        except FileExistsError:
            pass
        os.chdir("./manga")

    elif saveOption == "imgur":
        customCover = input("Would you like to use a custom cover? (y/n): ").replace(' ', '')
        if customCover == "y":
            fileOrLink = input("\n[1]: Local path\n[2]: Image link\n\nChoose one: ").replace(' ', '')
            success = False
            while not success:
                if fileOrLink == "1":
                    coverPath = input("\nInput path for the image: ")
                    try:
                        with open(coverPath, 'rb') as f:
                            coverSend = requests.post(imgurlink + "/3/image", data={"image": f.read()}, headers={"Authorization": "Client-ID {}".format(data["clientID"])})
                            if coverSend.status_code == 200:
                                success = True
                                print("(#) Cover successfully uploaded.")
                            else:
                                print("(!) Unable to send cover to imgur, error code: {}".format(coverSend.status_code))
                    except OSError:
                        print("(!) Unable to access/locate file.")
                elif fileOrLink == "2":
                    coverPath = input("\nInput link for the image: ")
                    coverSend = requests.post(imgurlink + "/3/image", data={"image": coverPath}, headers={"Authorization": "Client-ID {}".format(data["clientID"])})
                    if coverSend.status_code == 200:
                        success = True
                        print("(#) Cover successfully uploaded.")
                    else:
                        print("(!) Unable to send cover to imgur, error code: {}".format(coverSend.status_code))
                else:
                    print("(!) Invalid input.")
                    fileOrLink = input("\n[1]: Local path\n[2]: Image link\n\nChoose one: ").replace(' ', '')
            coverId = coverSend.json()["data"]["id"]

        mdDescription = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["description"]["en"]
        mdDescriptionFiltered = mdDescription[0:mdDescription.index("\r")]

        cubariJson = {}
        artistIds = []
        authorsIds = []
        for relationship in mangaQuery["results"][int(mangaSelection) - 1]["relationships"]:
            if relationship["type"] == "artist":
                artistIds.append(relationship["id"])
            elif relationship["type"] == "author":
                authorsIds.append(relationship["id"])
        artists = getNameByID(artistIds, "author")
        authors = getNameByID(authorsIds, "author")
        artistString = ""
        for artistIndex, artist in enumerate(artists):
            artistString += artist
            if artistIndex < len(artists) - 1:
                artistString += " & "
        authorString = ""
        for authorIndex, artist in enumerate(authors):
            authorString += artist
            if artistIndex < len(artists) - 1:
                authorString += " & "

        cubariJson["title"] = mangaName["en"]
        cubariJson["description"] = mdDescriptionFiltered
        cubariJson["artist"] = artistString
        cubariJson["author"] = authorString
        if customCover == "y":
            cubariJson["cover"] = "https://i.imgur.com/{}.png".format(coverId)
        cubariJson["chapters"] = {}

    payload = {
        "limit":            data["chapterResultsLimit"],
        "locales[]":        data["languageFilter"],
        "order[chapter]":   "asc"
    }
    getChapterList = requests.get(mdlink + "/manga/" + mangaID + "/feed", params=payload)

    if getChapterList.status_code == 200:
        chapterList = getChapterList.json()

        print("(#) Found " + str(len(chapterList["results"])) + " chapters.\n")

        for index, chapter in enumerate(chapterList["results"]):

            groups = getChapterGroups(chapter)

            print("[" + str(index + 1), end=']: ')
            print("("
                    + chapter["data"]["attributes"]["translatedLanguage"]
                    + ") Chapter "
                    + chapter["data"]["attributes"]["chapter"]
                    + " - ", end = '')
            print(groups)
        chapterSelection = input("\nSelect one or more (separated by comma): ").replace(' ', '')

        print("\nSelect the quality to save.\n")
        print("[1]: Original Quality\n[2]: Data Saver\n")
        qualitySelect = input("Select one: ")
        print()

        if saveOption == "local":
            try:
                os.makedirs(mangaMU + "-" + mangaName["en"])
            except FileExistsError:
                pass
            os.chdir(mangaMU + "-" + mangaName["en"])

        for selectedChapter in chapterSelection.split(","):
            chapterNumber = chapterList["results"][int(selectedChapter) - 1]["data"]["attributes"]["chapter"]
            if saveOption == "local":
                try:
                    os.makedirs(zeropad(2, chapterNumber))
                except FileExistsError:
                    pass
                os.chdir(zeropad(2, chapterNumber))

            groups = getChapterGroups(chapterList["results"][int(selectedChapter) - 1])
            pageIDs, contents = sendChapter(chapterList["results"][int(selectedChapter) - 1], qualitySelect, saveOption, data, headers)

            attempts = 1
            while pageIDs is None and contents is None and attempts <= 10:
                attempts += 1
                print("(#) Resetting connection...")
                pageIDs, contents = sendChapter(chapterList["results"][int(selectedChapter) - 1], qualitySelect, saveOption, data, headers)

            if saveOption == "imgur":
                albumTitle = mangaName["en"] + " - Chapter " + list(contents.keys())[0]

                payload = {"title": albumTitle, "cover": pageIDs[0], "privacy": "hidden", "ids[]": pageIDs}
                albumCreate = requests.post(albumCreateLink, data=payload, headers=headers)
                if albumCreate.status_code == 200:
                    albumID = albumCreate.json()["data"]["id"]
                    contents[list(contents.keys())[0]]["groups"][groups] = "/proxy/api/imgur/chapter/{}/".format(albumID)
                    print("(#) Chapter {} album successfully created, id = {}".format(list(contents.keys())[0], albumID))

            if saveOption == "local":
                os.chdir("../")
            elif saveOption == "imgur":
                cubariJson["chapters"][list(contents.keys())[0]] = contents[list(contents.keys())[0]]

        if saveOption == "local":
            os.chdir("../")

    if saveOption == "local":
        os.chdir("../")

    elif saveOption == "imgur":
        if customCover != "y":
            firstChapter = cubariJson["chapters"][list(cubariJson["chapters"].keys())[0]]["groups"][list(cubariJson["chapters"][list(cubariJson["chapters"].keys())[0]]["groups"].keys())[0]]
            firstChapterID = firstChapter.split("/")[-2]

            imgurHeaders = {"Authorization": "Bearer {}".format(data["imgurToken"])}
            r1 = requests.get("https://api.imgur.com/3/album/{}/images".format(firstChapterID), headers=imgurHeaders)
            cover = "https://i.imgur.com/{}.png".format(r1.json()["data"][0]["id"])
            cubariJson["cover"] = cover

        if input("Would you like to create a file in GitHub? (y/n): ") == "y":
            friendlyName = input("Input a friendly name for the json file on GitHub (without the extention): ").replace(' ', '') + ".json"
            createGitIo = input("Would you like to create git.io link? (y/n): ")
            cubariPage = makeFileAndGetGist(json.dumps(cubariJson, indent=2), friendlyName, createGitIo)
            if createGitIo == "y":
                print("\nCubari page: {}".format(cubariPage))

print("\n\n(#) Operation finished with no errors.")
