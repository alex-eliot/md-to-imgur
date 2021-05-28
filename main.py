import requests
import json
import os
import sys
import traceback

import sendToImgur
import globals

from datetime import datetime

from getObjectInfo import *
from githubCommit import *
from stringManipulation import *

globals.init()

try:
    os.makedirs("{}/logs/jsons".format(globals.rootDir))
except FileExistsError:
    pass
try:
    os.makedirs("{}/cubari".format(globals.rootDir))
except FileExistsError:
    pass

def main():

    # LOADING SETTINGS

    with open("./settings.json", 'r') as f:
        globals.log += "{} (#) Loading settings\n".format(datetime.now().isoformat().split(".")[0])
        data = json.load(f)
        globals.log += "{} (#) Settings loaded\n".format(datetime.now().isoformat().split(".")[0])
        settingsStatus = {
          "imgurToken": "no_entry",
          "clientID": "no_entry",
          "clientSecret": "no_entry",
          "refreshToken": "no_entry",
          "x-rapidapi-key": "no_entry",
          "githubToken": "no_entry",
          "repoDirectory": "no_entry",
        }

        if len(data["imgurToken"]) == 40:
            settingsStatus["imgurToken"] = "ok"
            globals.log += "{} (#) imgurToken ok\n".format(datetime.now().isoformat().split(".")[0])
        if len(data["clientID"]) == 15:
            settingsStatus["clientID"] = "ok"
            globals.log += "{} (#) clientID ok\n".format(datetime.now().isoformat().split(".")[0])
        if len(data["clientSecret"]) == 40:
            settingsStatus["clientSecret"] = "ok"
            globals.log += "{} (#) clientSecret ok\n".format(datetime.now().isoformat().split(".")[0])
        if len(data["refreshToken"]) == 40:
            settingsStatus["refreshToken"] = "ok"
            globals.log += "{} (#) refreshToken ok\n".format(datetime.now().isoformat().split(".")[0])
        if len(data["x-rapidapi-key"]) == 50:
            settingsStatus["x-rapidapi-key"] = "ok"
            globals.log += "{} (#) x-rapidapi-key ok\n".format(datetime.now().isoformat().split(".")[0])
        if len(data["githubToken"]) == 40:
            settingsStatus["githubToken"] = "ok"
            globals.log += "{} (#) githubToken ok\n".format(datetime.now().isoformat().split(".")[0])
        if "" not in data["repoDirectory"].split("/"):
            settingsStatus["repoDirectory"] = "ok"
            globals.log += "{} (#) repoDirectory ok\n".format(datetime.now().isoformat().split(".")[0])


    cubariPage = None

    globals.headers = {
        "content-type": "application/x-www-form-urlencoded",
        "authorization": "Bearer " + data["imgurToken"],
        "x-rapidapi-key": data["x-rapidapi-key"],
        "x-rapidapi-host": "imgur-apiv3.p.rapidapi.com"
    }

    # SEARCHING MANGA
    query = input("Search for a manga: ")
    globals.log += "{} (#) Searching for [{}]\n".format(datetime.now().isoformat().split(".")[0], query)

    searchResults = requests.get("{}/manga".format(globals.mdlink), params = {"title": query, "limit": data["searchResultsLimit"]})

    with open("{}/logs/jsons/{}".format(globals.rootDir, "searchResults.json"), "w") as f:
        json.dump(searchResults.json(), f, indent=2)

    globals.log += "{} (#) Search returned status code {}\n".format(datetime.now().isoformat().split(".")[0], searchResults.status_code)

    if searchResults.status_code == 200:

        # PRINTING FOUND MANGA
        mangaQuery = searchResults.json()
        print("\n(#) Found " + str(len(mangaQuery["results"])) + " manga.\n")

        manga_list = []

        for index, item in enumerate(mangaQuery["results"]):
            print("[" + str(index + 1), end=']: ')
            print(item["data"]["attributes"]["title"]["en"])

        # SELECTING MANGA
        mangaSelection = input("\nSelect one: ")

        while int(mangaSelection) not in range(1, len(mangaQuery["results"]) + 1):
            print("(!) Invalid input, try again")
            mangaSelection = input("\nSelect one: ")

        # ASSIGNING USEFUL VALUES
        mangaID = mangaQuery["results"][int(mangaSelection) - 1]["data"]["id"]
        mangaName = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["title"]["en"]

        globals.log += "{} (#) Selected {}, mangaID: {}\n".format(datetime.now().isoformat().split(".")[0], mangaName, mangaID)


        # SELECTING SAVE OPTION
        saveOption = input("\n[1]: Save locally\n[2]: Save to imgur album\n\nSelect one: ")
        while saveOption not in ["1", "2"]:
            print("(!) Invalid input, try again")
            saveOption = input("\n[1]: Save locally\n[2]: Save to imgur album\n\nSelect one: ")

        saveOption = (""
                + "local" * (saveOption == "1")
                + "imgur" * (saveOption == "2")
        )

        globals.log += "{} (#) Save option: {}\n".format(datetime.now().isoformat().split(".")[0], saveOption)

        if saveOption == "imgur":

            saveInGithub = input("Would you like to create a file in Github? (y/n): ")
            if saveInGithub == "y":
                friendlyName = input("Input a friendly name for the json file on GitHub: ").replace(' ', '').replace(".json", "") + ".json"
                makeGist = input("Would you like to create a gist? (y/n): ")
                if makeGist == "y":
                    customURL = input("Input custom name (leave empty if you want a random one): ")

            customOrMangadexCover = input("\nWould you like to use a custom cover or use a cover from Mangadex?\n\n[1]: Mangadex cover\n[2]: Custom cover\n\nSelect one: ")
            while customOrMangadexCover not in ["1", "2"]:
                print("(!) Invalid input, try again")
                customOrMangadexCover = input("Would you like to use a custom cover or use a cover from Mangadex?\n [1]: Mangadex cover\n[2]: Custom cover\nSelect one: ")

            customOrMangadexCover = (""
                                    + "mangadex"    * (customOrMangadexCover == "1")
                                    + "custom"      * (customOrMangadexCover == "2")
            )

            mdDescription = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["description"]["en"]
            if "\r" in mdDescription:
                mdDescriptionFiltered = mdDescription[0:mdDescription.index("\r")]
            else:
                mdDescriptionFiltered = mdDescription

            cubariJson = {}
            artistIds = []
            authorsIds = []
            globals.log += "{} (#) Getting author and artist names from ID\n".format(datetime.now().isoformat().split(".")[0])
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

            cubariJson["title"] = mangaName
            cubariJson["description"] = mdDescriptionFiltered
            cubariJson["artist"] = artistString
            cubariJson["author"] = authorString
            cubariJson["chapters"] = {}

        payload = {
            "limit":                    data["chapterResultsLimit"],
            "translatedLanguage[]":     data["languageFilter"],
            "order[chapter]":           "asc"
        }
        getChapterList = requests.get(globals.mdlink + "/manga/" + mangaID + "/feed", params=payload)
        with open("{}/logs/jsons/{}".format(globals.rootDir, "chapterResults.json"), "w") as f:
            json.dump(getChapterList.json(), f, indent=2)

        globals.log += "{} (#) Get Chapter list returned status code {}\n".format(datetime.now().isoformat().split(".")[0], getChapterList.status_code)

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
            chapterSelection = stringFormat(chapterSelection, len(chapterList["results"]))
            globals.log += "{} (#) Selected chapters {}\n".format(datetime.now().isoformat().split(".")[0], chapterSelection)

            qualitySelect = input("\nSelect the quality to save.\n[1]: Original Quality\n[2]: Data Saver\n\nSelect one: ")
            globals.log += "{} (#) Selected quality: {}\n".format(datetime.now().isoformat().split(".")[0], "Original Quality" * (qualitySelect == "1") + "Data Saver" * (qualitySelect == "2"))
            print()

            for selectedChapter in chapterSelection.split(","):
                chapterNumber = chapterList["results"][int(selectedChapter) - 1]["data"]["attributes"]["chapter"]
                try:
                    os.makedirs("{}/manga/{}/{}".format(globals.rootDir, mangaName.replace("?", "").replace("\"", ""), chapterNumber))
                except FileExistsError:
                    pass

            for selectedChapter in chapterSelection.split(","):
                chapterNumber = chapterList["results"][int(selectedChapter) - 1]["data"]["attributes"]["chapter"]

                globals.log += "{} (#) Getting chapter {} groups.\n".format(datetime.now().isoformat().split(".")[0], chapterNumber)
                groups = getChapterGroups(chapterList["results"][int(selectedChapter) - 1])
                globals.log += "{} (#) Initiating chapter {} send/retrieval\n".format(datetime.now().isoformat().split(".")[0], chapterNumber)
                pageIDs, contents, success = sendToImgur.sendChapter(chapterList["results"][int(selectedChapter) - 1], mangaName, qualitySelect, saveOption, data)

                if not success:
                    globals.log += "{} (!) Failed to receive all pages for chapter {}\n".format(datetime.now().isoformat().split(".")[0], chapterNumber)
                    if input("(!) Failed to receive all pages for chapter {}. Would you like to continue with the next chapter? (y/n): ".format(chapterNumber)) != "y":
                        globals.log += "{} (#) User initiated program shutdown\n".format(datetime.now().isoformat().split(".")[0])
                        raise Exception

                else:
                    if saveOption == "imgur":
                        albumTitle = mangaName + " - Chapter " + list(contents.keys())[0]
                        payload = {"title": albumTitle, "cover": pageIDs[0], "privacy": "hidden", "ids[]": pageIDs}

                        globals.log += "{} (#) Creating album\n".format(datetime.now().isoformat().split(".")[0])

                        albumCreate = requests.post(globals.albumCreateLink, data=payload, headers=globals.headers)
                        if albumCreate.status_code == 200:
                            albumID = albumCreate.json()["data"]["id"]

                            globals.log += "{} (#) Chapter {} album successfully created, id = {}\n".format(datetime.now().isoformat().split(".")[0], list(contents.keys())[0], albumID)

                            contents[list(contents.keys())[0]]["groups"][groups] = "/proxy/api/imgur/chapter/{}/".format(albumID)

                        cubariJson["chapters"][list(contents.keys())[0]] = contents[list(contents.keys())[0]]


        # UPLOADING COVER
        if saveOption == "imgur":
            coverRetries = 5
            coverId = None
            if customOrMangadexCover == "mangadex":
                print("(#) Uploading cover")
                while coverRetries > 0:
                    covers = requests.get("{}/cover".format(globals.mdlink), params = {"manga[]": mangaID})

                    if covers.status_code == 200:
                        if len(covers.json()["results"]) > 0:
                            coverFilename = covers.json()["results"][0]["data"]["attributes"]["fileName"]
                            coverFullLink = "https://uploads.mangadex.org/covers/{}/{}".format(mangaID, coverFilename)
                            globals.log += "{} (#) Cover link: {}\n".format(datetime.now().isoformat().split(".")[0], coverFullLink)
                            globals.log += "{} (#) Downloading cover\n".format(datetime.now().isoformat().split(".")[0])
                            coverImg = requests.get(coverFullLink)
                            if coverImg.status_code == 200:
                                globals.log += "{} (#) Cover downloaded, sending to imgur\n".format(datetime.now().isoformat().split(".")[0])

                                coverSend = requests.post(globals.imgurUploadLink, data={"image": coverImg.content}, headers={"Authorization": "Client-ID {}".format(data["clientID"])})

                                if coverSend.status_code == 200:
                                    coverRetries = 0
                                    print("(#) Cover successfully uploaded\n")
                                    coverId = coverSend.json()["data"]["id"]
                                    globals.log += "{} (#) Cover uploaded, id: {}\n".format(datetime.now().isoformat().split(".")[0], coverId)
                                else:
                                    print("(!) Unable to send cover to imgur, error code: {}".format(coverSend.status_code))
                                    globals.log += "{} (!) Unable to send cover to imgur, error code {}\n".format(datetime.now().isoformat().split(".")[0], coverSend.status_code)
                        else:
                            print("(!) Didn't find any covers for the manga, using first page")
                            globals.log += "{} (!) Didn't find any covers for the manga, using first page\n".format(datetime.now().isoformat().split(".")[0])
                            coverRetries = 0
                    else:
                        coverRetries -= 1

            elif customOrMangadexCover == "custom":
                globals.log += "{} (#) Selected custom cover\n".format(datetime.now().isoformat().split(".")[0])
                fileOrLink = input("\n[1]: Local path\n[2]: Image link\n\nChoose one: ").replace(' ', '')
                coverRetries = 5
                while coverRetries > 0:
                    globals.log += "{} (#) Selected local path.\n".format(datetime.now().isoformat().split(".")[0]) * (fileOrLink == "1") + "(#) Selected image link\n".format(datetime.now().isoformat().split(".")[0]) * (fileOrLink == "2")
                    if fileOrLink == "1":
                        coverPath = input("\nInput path for the image: ")
                        globals.log += "{} (#) Path input: {}\n".format(datetime.now().isoformat().split(".")[0], coverPath)
                        try:
                            with open(coverPath, 'rb') as f:
                                coverSend = requests.post(globals.imgurUploadLink, data={"image": f.read()}, headers={"Authorization": "Client-ID {}".format(data["clientID"])})
                                globals.log += "{} (#) Cover uploading returned status code {}\n".format(datetime.now().isoformat().split(".")[0], coverSend.status_code)
                                if coverSend.status_code == 200:
                                    coverRetries = 0
                                    print("(#) Cover successfully uploaded")
                                else:
                                    print("(!) Unable to send cover to imgur, error code: {}".format(coverSend.status_code))
                                    coverRetries -= 1
                        except OSError:
                            print("(!) Unable to access/locate file.")
                    elif fileOrLink == "2":
                        coverPath = input("\nInput link for the image: ")
                        globals.log += "{} (#) Image link: {}\n".format(datetime.now().isoformat().split(".")[0], coverPath)
                        coverSend = requests.post(globals.imgurUploadLink, data={"image": coverPath}, headers={"Authorization": "Client-ID {}".format(data["clientID"])})
                        globals.log += "{} (#) Cover uploading returned status code {}\n".format(datetime.now().isoformat().split(".")[0], coverSend.status_code)
                        if coverSend.status_code == 200:
                            coverRetries = 0
                            print("(#) Cover successfully uploaded")
                        else:
                            print("(!) Unable to send cover to imgur, error code: {}".format(coverSend.status_code))
                            coverRetries -= 1
                    else:
                        globals.log += "{} (!) Invalid input: {}\n".format(datetime.now().isoformat().split(".")[0], fileOrLink)
                        print("(!) Invalid input.")
                        fileOrLink = input("\n[1]: Local path\n[2]: Image link\n\nChoose one: ").replace(' ', '')

                coverId = coverSend.json()["data"]["id"]
                globals.log += "{} (#) Cover uploaded, id: {}\n".format(datetime.now().isoformat().split(".")[0], coverId)
            if coverId is None:
                firstChapter = cubariJson["chapters"][list(cubariJson["chapters"].keys())[0]]["groups"][list(cubariJson["chapters"][list(cubariJson["chapters"].keys())[0]]["groups"].keys())[0]]

                firstChapterID = firstChapter.split("/")[-2]
                globals.log += "{} (#) Getting the album id of the first chapter uploaded\n".format(datetime.now().isoformat().split(".")[0])

                r1 = requests.get("https://imgur-apiv3.p.rapidapi.com/3/album/" + firstChapterID + "/images", headers=globals.headers)

                cover = "https://i.imgur.com/{}.png".format(r1.json()["data"][0]["id"])
                cubariJson["cover"] = cover
            else:
                cubariJson["cover"] = "https://i.imgur.com/{}.png".format(coverId)

            with open("{}/cubari/cubari{}.json".format(globals.rootDir, datetime.now().isoformat().replace(":", " ")), "w") as f:
                json.dump(cubariJson, f, indent=2)

            if saveInGithub == "y":
                globals.log += "{} (#) Creating file '{}' on Github\n".format(datetime.now().isoformat().split(".")[0], friendlyName)
                cubariPage = makeFileAndGetGist(json.dumps(cubariJson, indent=2), friendlyName, makeGist, customURL)

    if success:
        print("(#) All chapters have been "
            + "uploaded"        * (saveOption == "imgur")
            + "downloaded"      * (saveOption == "local")
        )
    else:
        print("(#) Operation finished, not all chapters have been "
            + "uploaded"        * (saveOption == "imgur")
            + "downloaded"      * (saveOption == "local")
        )

    if cubariPage is not None:
        print("\nCubari page: {}".format(cubariPage))

if __name__ == "__main__":
    try:
        main()
        with open ("{}/logs/{}.txt".format(globals.rootDir, datetime.now().isoformat().replace(":", " ").split(".")[0]), "w") as f:
            f.write(globals.log)
    except KeyboardInterrupt:
        print("(!) Received keyboard interrupt\n")
        globals.log += "{} (!) Received keyboard interrupt\n".format(datetime.now().isoformat().split(".")[0])
        try:
            with open("{}/cubari/cubari{}.json".format(globals.rootDir, datetime.now().isoformat().replace(":", " ")), "w") as f:
                json.dump(cubariJson, f, indent=2)
        except Exception:
            globals.log += "{} (!) Couldn't write cubari.json\n".format(datetime.now().isoformat().split(".")[0])
        with open ("{}/logs/{}.txt".format(globals.rootDir, datetime.now().isoformat().replace(":", " ").split(".")[0]), "w") as f:
            f.write(globals.log)
    except Exception:
        print("(!) Exception occured. See logs for detials.\n")
        print(traceback.format_exc())
        globals.log += "{} (!) Exception occred. Details:\n{}".format(datetime.now().isoformat().split(".")[0], str(traceback.format_exc()))
        try:
            with open("{}/cubari/cubari{}.json".format(globals.rootDir, datetime.now().isoformat().replace(":", " ")), "w") as f:
                json.dump(cubariJson, f, indent=2)
        except Exception:
            globals.log += "{} (!) Couldn't write cubari.json\n".format(datetime.now().isoformat().split(".")[0])
            pass
        with open ("{}/logs/{}.txt".format(globals.rootDir, datetime.now().isoformat().replace(":", " ").split(".")[0]), "w") as f:
            f.write(globals.log)
