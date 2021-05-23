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
    try:
        os.makedirs("{}/cubari".format(globals.rootDir))
    except FileExistsError:
        pass
    pass

def zeropad(zeros, name):
    return "0" * (zeros - len(name)) + name

def main():
    cubariPage = None

    with open("./settings.json", 'r') as f:
        globals.log += "(#) Loading settings\n"
        data = json.load(f)
        globals.log += "(#) Settings loaded\n"
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
            globals.log += "(#) imgurToken ok\n"
        if len(data["clientID"]) == 15:
            settingsStatus["clientID"] = "ok"
            globals.log += "(#) clientID ok\n"
        if len(data["clientSecret"]) == 40:
            settingsStatus["clientSecret"] = "ok"
            globals.log += "(#) clientSecret ok\n"
        if len(data["refreshToken"]) == 40:
            settingsStatus["refreshToken"] = "ok"
            globals.log += "(#) refreshToken ok\n"
        if len(data["x-rapidapi-key"]) == 50:
            settingsStatus["x-rapidapi-key"] = "ok"
            globals.log += "(#) x-rapidapi-key ok\n"
        if len(data["githubToken"]) == 40:
            settingsStatus["githubToken"] = "ok"
            globals.log += "(#) githubToken ok\n"
        if "" not in data["repoDirectory"].split("/"):
            settingsStatus["repoDirectory"] = "ok"
            globals.log += "(#) repoDirectory ok\n"




    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "authorization": "Bearer " + data["imgurToken"],
        "x-rapidapi-key": data["x-rapidapi-key"],
        "x-rapidapi-host": "imgur-apiv3.p.rapidapi.com"
    }

    query = input("Search for a manga: ")
    globals.log += "(#) Searching for [{}]\n".format(query)
    searchResults = requests.get(globals.mdlink + "/manga", params = {"title": query, "limit": data["searchResultsLimit"]})
    with open("{}/logs/jsons/{}".format(globals.rootDir, "searchResults.json"), "w") as f:
        json.dump(searchResults.json(), f, indent=2)

    globals.log += "(#) Search returned status code {}\n".format(searchResults.status_code)

    if searchResults.status_code == 200:

        mangaQuery = searchResults.json()
        print("\n(#) Found " + str(len(mangaQuery["results"])) + " manga.\n")

        manga_list = []

        for index, item in enumerate(mangaQuery["results"]):
            print("[" + str(index + 1), end=']: ')
            print(item["data"]["attributes"]["title"]["en"])
        mangaSelection = input("\nSelect one: ")

        mangaID = mangaQuery["results"][int(mangaSelection) - 1]["data"]["id"]
        mangaName = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["title"]["en"]
        mangaMU = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["links"]["mu"]

        saveOption = input("\n[1]: Save locally\n[2]: Save to imgur album\n\nSelect one: ")
        saveOption = (""
                + "local" * (saveOption == "1")
                + "imgur" * (saveOption == "2")
        )

        globals.log += "(#) Save option: {}\n".format(saveOption)

        if saveOption == "imgur":
            customCover = input("Would you like to use a custom cover? (y/n): ").replace(' ', '')
            if customCover == "y":
                globals.log += "(#) Selected custom cover\n"
                fileOrLink = input("\n[1]: Local path\n[2]: Image link\n\nChoose one: ").replace(' ', '')
                success = False
                while not success:
                    globals.log += "(#) Selected local path.\n" * (fileOrLink == "1") + "(#) Selected image link\n" * (fileOrLink == "2")
                    if fileOrLink == "1":
                        coverPath = input("\nInput path for the image: ")
                        globals.log += "(#) Path input: {}\n".format(coverPath)
                        try:
                            with open(coverPath, 'rb') as f:
                                coverSend = requests.post(globals.imgurUploadLink, data={"image": f.read()}, headers={"Authorization": "Client-ID {}".format(data["clientID"])})
                                globals.log += "(#) Cover uploading returned status code {}\n".format(coverSend.status_code)
                                if coverSend.status_code == 200:
                                    success = True
                                    print("(#) Cover successfully uploaded.")
                                else:
                                    print("(!) Unable to send cover to imgur, error code: {}".format(coverSend.status_code))
                        except OSError:
                            print("(!) Unable to access/locate file.")
                    elif fileOrLink == "2":
                        coverPath = input("\nInput link for the image: ")
                        globals.log += "(#) Image link: {}\n".format(coverPath)
                        coverSend = requests.post(globals.imgurUploadLink, data={"image": coverPath}, headers={"Authorization": "Client-ID {}".format(data["clientID"])})
                        globals.log += "(#) Cover uploading returned status code {}\n".format(coverSend.status_code)
                        if coverSend.status_code == 200:
                            success = True
                            print("(#) Cover successfully uploaded.")
                        else:
                            print("(!) Unable to send cover to imgur, error code: {}".format(coverSend.status_code))
                    else:
                        globals.log += "(!) Invalid input: {}\n".format(fileOrLink)
                        print("(!) Invalid input.")
                        fileOrLink = input("\n[1]: Local path\n[2]: Image link\n\nChoose one: ").replace(' ', '')
                coverId = coverSend.json()["data"]["id"]
                globals.log += "(#) Cover uploaded, id: {}".format(coverId)

            mdDescription = mangaQuery["results"][int(mangaSelection) - 1]["data"]["attributes"]["description"]["en"]
            mdDescriptionFiltered = mdDescription[0:mdDescription.index("\r")]

            cubariJson = {}
            artistIds = []
            authorsIds = []
            globals.log += "(#) Getting author and artist names from ID\n"
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
            if customCover == "y":
                cubariJson["cover"] = "https://i.imgur.com/{}.png".format(coverId)
            cubariJson["chapters"] = {}

        payload = {
            "limit":            data["chapterResultsLimit"],
            "locales[]":        data["languageFilter"],
            "order[chapter]":   "asc"
        }
        getChapterList = requests.get(globals.mdlink + "/manga/" + mangaID + "/feed", params=payload)
        with open("{}/logs/jsons/{}".format(globals.rootDir, "chapterResults.json"), "w") as f:
            json.dump(getChapterList.json(), f, indent=2)

        globals.log += "(#) Get Chapter list returned status code {}\n".format(getChapterList.status_code)

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
            globals.log += "(#) Selected chapters {}\n".format(chapterSelection)

            qualitySelect = input("\nSelect the quality to save.\n[1]: Original Quality\n[2]: Data Saver\n\nSelect one: ")
            globals.log += "(#) Selected quality: {}\n".format("Original Quality" * (qualitySelect == "1") + "Data Saver" * (qualitySelect == "2"))
            print()

            for selectedChapter in chapterSelection.split(","):
                chapterNumber = chapterList["results"][int(selectedChapter) - 1]["data"]["attributes"]["chapter"]
                try:
                    os.makedirs("{}/manga/{}/{}".format(globals.rootDir, mangaName, chapterNumber))
                except FileExistsError:
                    pass

            for selectedChapter in chapterSelection.split(","):
                chapterNumber = chapter["data"]["attributes"]["chapter"]

                globals.log += "(#) Getting chapter {} groups.\n".format(chapterNumber)
                groups = getChapterGroups(chapterList["results"][int(selectedChapter) - 1])
                globals.log += "(#) Initiating chapter {} send/retrieval\n".format(chapterNumber)
                pageIDs, contents, success = sendToImgur.sendChapter(chapterList["results"][int(selectedChapter) - 1], mangaName, qualitySelect, saveOption, data, headers)

                if not success:
                    globals.log += "(#) Failed to receive all pages for chapter {}\n".format(chapterNumber)
                    if input("(#) Failed to receive all pages for chapter {}. Would you like to create a cubari.json with the previously fetched chapters? (y/n): ").format(chapterNumber) != "y":
                        exit()

                else:
                    if saveOption == "imgur":
                        albumTitle = mangaName + " - Chapter " + list(contents.keys())[0]
                        payload = {"title": albumTitle, "cover": pageIDs[0], "privacy": "hidden", "ids[]": pageIDs}

                        globals.log += "(#) Creating album\n"

                        albumCreate = requests.post(globals.albumCreateLink, data=payload, headers=headers)
                        if albumCreate.status_code == 200:
                            albumID = albumCreate.json()["data"]["id"]

                            globals.log += "(#) Chapter {} album successfully created, id = {}".format(list(contents.keys())[0], albumID)

                            contents[list(contents.keys())[0]]["groups"][groups] = "/proxy/api/imgur/chapter/{}/".format(albumID)

                        cubariJson["chapters"][list(contents.keys())[0]] = contents[list(contents.keys())[0]]

        if saveOption == "imgur":
            if customCover != "y":
                firstChapter = cubariJson["chapters"][list(cubariJson["chapters"].keys())[0]]["groups"][list(cubariJson["chapters"][list(cubariJson["chapters"].keys())[0]]["groups"].keys())[0]]

                firstChapterID = firstChapter.split("/")[-2]
                globals.log += "(#) Getting the album id of the first chapter uploaded\n"

                r1 = requests.get("https://imgur-apiv3.p.rapidapi.com/3/album/" + firstChapterID + "/images", headers=headers)

                cover = "https://i.imgur.com/{}.png".format(r1.json()["data"][0]["id"])
                cubariJson["cover"] = cover

                with open("{}/cubari/cubari{}.json".format(globals.rootDir, datetime.now().isoformat().replace(":", " ")), "w") as f:
                    json.dump(cubariJson, f, indent=2)

            if input("Would you like to create a file in Github? (y/n): ") == "y":
                friendlyName = input("Input a friendly name for the json file on GitHub (without the extention): ").replace(' ', '') + ".json"
                globals.log += "(#) Creating file '{}' on Github\n".format(friendlyName)
                cubariPage = makeFileAndGetGist(json.dumps(cubariJson, indent=2), friendlyName)

    if success:
        print("(#) All chapters have uploaded")
    else:
        print("(#) Operation finished, not all chapters have been uploaded")

    if cubariPage is not None:
        print("\nCubari page: {}".format(cubariPage))

if __name__ == "__main__":
    try:
        main()
        with open ("{}/logs/{}.txt".format(globals.rootDir, datetime.now().isoformat().replace(":", " ").split(".")[0]), "w") as f:
            f.write(globals.log)
    except KeyboardInterrupt:
        print("(!) Received keyboard interrupt\n")
        globals.log += "(!) Received keyboard interrupt\n"
        with open ("{}/logs/{}.txt".format(globals.rootDir, datetime.now().isoformat().replace(":", " ").split(".")[0]), "w") as f:
            f.write(globals.log)
        try: # idk why this here but saw this on stackoverflow so yeah
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception:
        print("(!) Exception occured. See logs for detials.\n")
        print(traceback.format_exc())
        globals.log += "(!) Exception occred. Details:\n{}".format(str(traceback.format_exc()))
        with open ("{}/logs/{}.txt".format(globals.rootDir, datetime.now().isoformat().replace(":", " ").split(".")[0]), "w") as f:
            f.write(globals.log)
