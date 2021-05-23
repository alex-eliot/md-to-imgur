import requests
import dateutil.parser as dp

import globals

from datetime import datetime

def zeropad(zeros, name):
    return "0" * (zeros - len(name)) + name

def imageRetrieveTest(atHomeServer, hash, page, quality, chapterID, report=False, getNewIfFail=False):
    globals.mdlink = "https://api.mangadex.org"
    link = atHomeServer + quality + hash + '/' + page

    globals.log += "(#) Getting test image\n"
    start_time = datetime.now()
    testImg = requests.get(link)
    end_time = datetime.now()

    if "X-Cache" in testImg.headers:
        cached = (testImg.headers["X-Cache"] == "HIT")
    else:
        cached = False

    time_diff = (end_time - start_time)
    response_time = time_diff.total_seconds() * 1000

    if testImg.status_code == 200:
        globals.log += "(#) Test image successfully received\n"
        globals.log += "(#) Image bytes = {}\n".format(len(testImg.content))
        globals.log += "(#) server url = {}\n".format(atHomeServer)
        # extention = "." + page.split(".")[-1]
        # with open("test" + extention, 'wb') as outimg:
        #     outimg.write(testImg.content)
        if report:
            payload = {"url": link, "success": True, "bytes": len(testImg.content), "duration": int(response_time), "cached": cached}
            requests.post("https://api.mangadex.network/report", data=payload)
        return atHomeServer
    else:
        globals.log += "(!) Unable to retrieve test image, error code {}\n".format(testImg.status_code)
        if report:
            payload = {"url": link, "success": False, "bytes": len(testImg.content), "duration": int(response_time), "cached": cached}
            requests.post("https://api.mangadex.network/report", data=payload)
        if getNewIfFail:
            globals.log += "(#) Finding another server\n"
            atHomeServer = requests.get(globals.mdlink + "/at-home/server/" + chapterID).json()["baseUrl"]
            return imageRetrieveTest(atHomeServer, hash, page, isDataSaver, chapterID, report=report, getNewIfFail=getNewIfFail)
        else:
            return None

def sendChapter(chapter, mangaName, dataSaver, saveOption, data, headers):

    chapterID = chapter["data"]["id"]
    chapterHash = chapter["data"]["attributes"]["hash"]
    chapterNumber = chapter["data"]["attributes"]["chapter"]
    chapterTitle = chapter["data"]["attributes"]["title"]
    chapterVolume = chapter["data"]["attributes"]["volume"]

    contents = {chapterNumber: {}}
    if chapterTitle == "":
        contents[chapterNumber]["title"] = "Chapter {}".format(chapterNumber)
    else:
        contents[chapterNumber]["title"] = chapterTitle
    if chapterVolume is None:
        contents[chapterNumber]["volume"] = "1"
    else:
        contents[chapterNumber]["volume"] = chapterVolume
    contents[chapterNumber]["groups"] = {}

    chapterTimeUpdated = dp.parse(chapter["data"]["attributes"]["updatedAt"])
    chapterTimeUpdatedUnix = int(chapterTimeUpdated.timestamp())
    contents[chapterNumber]["last_updated"] = chapterTimeUpdatedUnix

    print(""
    + "(#) Downloading chapter {}".format(chapterNumber)           * (saveOption == "local")
    + "(#) Sending chapter {} to imgur".format(chapterNumber)       * (saveOption == "imgur")
    )

    chapterPagesOriginal = chapter["data"]["attributes"]["data"]
    chapterPagesDataSaver = chapter["data"]["attributes"]["dataSaver"]

    if dataSaver == "1":
        pages = chapterPagesOriginal
        quality = "/data/"
    elif dataSaver == "2":
        pages = chapterPagesDataSaver
        quality = "/data-saver/"

    pageIDs = []

    if len(data["priorityServers"]) > 0:
        globals.log += "(#) Testing priority servers\n"
    for index, priorityServer in enumerate(data["priorityServers"]):
        if imageRetrieveTest(priorityServer, chapterHash, pages[0], quality, chapterID, report=False, getNewIfFail=False) is None:
            data["priorityServers"].pop(index)
            globals.log += "(!) Server {} failed to retrieve test image, removing from list\n".format(priorityServer)
        else:
            globals.log += "(#) Server {} successfully retrieved the test image\n".format(priorityServer)

    if len(data["fallbackServers"]) > 0:
        globals.log += "(#) Testing fallback servers\n"
    for index, fallbackServer in enumerate(data["fallbackServers"]):
        if imageRetrieveTest(fallbackServer, chapterHash, pages[0], quality, chapterID, report=False, getNewIfFail=False) is None:
            data["fallbackServers"].pop(index)
            globals.log += "(#) Server {} failed to retrieve test image, removing from list\n".format(fallbackServer)
        else:
            globals.log += "(#) Server {} successfully retrieved the test image\n".format(fallbackServer)

    globals.log += "(#) Receiving md@home server address for chapter {}. ChapterID={} ChapterHash={}\n".format(chapterNumber, chapterID, chapterHash)
    atHomeServer = requests.get(globals.mdlink + "/at-home/server/" + chapterID)
    globals.log += "(#) Server retrieval returned status code {}\n".format(atHomeServer.status_code)
    if atHomeServer.status_code == 200:
        globals.log += "(#) Server url = {}\n".format(atHomeServer.json()["baseUrl"])
        globals.log += "(#) Testing standard server\n"
        standardServer = imageRetrieveTest(atHomeServer.json()["baseUrl"], chapterHash, pages[0], quality, chapterID, report=True, getNewIfFail=True)
        if standardServer is None:
            globals.log += "(!) Server test failed, url = {}".format(atHomeServer.json()["baseUrl"])
        else:
            globals.log += "(#) Server test success\n"


    for index, page in enumerate(pages):
        globals.log += "(#) Proceeding with page {} of chapter {}\n".format(index + 1, chapterNumber)
        globals.log += "(#) Page link: {}\n".format(page)
        retrieved = False

        # PRIORITY SERVERS
        i = 0
        while not retrieved and i < len(data["priorityServers"]):
            globals.log += "(#) Receiving from priority server no.{}.\n".format(i + 1)

            server = data["priorityServers"][i]
            if server[-1] == "/":
                server = server[0:len(server) - 1]

            link = server + quality + chapterHash + "/" + page
            globals.log += "(#) Server no.{}, full link: {}\n".format(i + 1, link)

            if saveOption == "local":
                globals.log += "(#) Downloading page {} of chapter {}\n".format(index + 1, chapterNumber)
                img = requests.get(link)
                extention = "." + page.split(".")[-1]
                filename = "{}/manga/{}/{}/{}".format(globals.rootDir, mangaName, chapterNumber, zeropad(3, str(index + 1)) + extention)
                if img.status_code == 200:
                    globals.log += "(#) Page {} of chapter {} downloaded\n".format(index + 1, chapterNumber)
                    with open(filename, 'wb') as outfile:
                        outfile.write(img.content)
                    retrieved = True
                else:
                    globals.log += "(!) Unable to retrieve page {}, error code: {}, url = {}\n".format(index + 1, img.status_code, link)
                    if i < len(data["priorityServers"]):
                        globals.log += "(#) Trying next priority server\n"
                    i += 1

            elif saveOption == "imgur":
                globals.log += "(#) Sending page {} of chapter {} to imgur\n".format(index + 1, chapterNumber)
                response = requests.post(globals.imgUploadLink, data=link, headers=headers)
                if response.status_code == 200:
                    globals.log += "(#) Page {} of chapter {} sent to imgur. id = {}\n".format(index + 1, chapterNumber, response.json()["data"]["id"])
                    pageIDs.append(response.json()["data"]["id"])
                    retrieved = True
                else:
                    globals.log += "(!) Failed to send page {} for chapter {} to imgur, error code: {}, url = \n".format(index + 1, chapterNumber, response.status_code, link)

        # STANDARD SERVERS
        if not retrieved:
            globals.log += "(!) Unable to download/send image from all priority servers\n" * (len(data["priorityServers"]) > 0)
            globals.log += "(#) Proceeding with standard servers\n"

            if standardServer is not None:
                link = standardServer + quality + chapterHash + '/' + page
                globals.log += "(#) Full page link: {}\n".format(link)

                if saveOption == "local":
                    globals.log += "(#) Downloading page {} of chapter {}\n".format(index + 1, chapterNumber)
                    img = requests.get(link)
                    extention = "." + page.split(".")[-1]
                    filename = "{}/manga/{}/{}/{}".format(globals.rootDir, mangaName, chapterNumber, zeropad(3, str(index + 1)) + extention)
                    if img.status_code == 200:
                        globals.log += "(#) Page {} of chapter {} downloaded\n".format(index + 1, chapterNumber)
                        with open(filename, 'wb') as outfile:
                            outfile.write(img.content)
                        retrieved = True
                    else:
                        globals.log += "(!) Failed to send page {} for chapter {} to imgur, error code: {}\n".format(index + 1, chapterNumber, img.status_code)

                elif saveOption == "imgur":
                    globals.log += "(#) Sending page {} of chapter {} to imgur\n".format(index + 1, chapterNumber)
                    response = requests.post(globals.imgUploadLink, data=link, headers=headers)
                    if response.status_code == 200:
                        globals.log += "(#) Page {} of chapter {} successfully sent to imgur\n".format(index + 1, chapterNumber)
                        pageIDs.append(response.json()["data"]["id"])
                        retrieved = True
                    else:
                        globals.log += "(!) Failed to send page {} for chapter {} to imgur, error code: {}, url = {}\n".format(index + 1, chapterNumber, response.status_code, link)


        # FALLBACK SERVERS
        i = 0
        while not retrieved and i < len(data["fallbackServers"]):
            globals.log += "(#) Receiving from fallback server no.{}.\n".format(i + 1)

            server = data["fallbackServers"][i]
            if server[-1] == "/":
                server = server[0:len(server) - 1]
            link = data["fallbackServers"][i] + quality + chapterHash + "/" + page

            globals.log += "(#) Server no.{} full link: {}\n".format(i + 1, link)

            if saveOption == "local":
                globals.log += "(#) Downloading page {} of chapter {}\n".format(index + 1, chapterNumber)
                img = requests.get(link)
                extention = "." + page.split(".")[-1]
                filename = "{}/manga/{}/{}/{}".format(globals.rootDir, mangaName, chapterNumber, zeropad(3, str(index + 1)) + extention)
                if img.status_code == 200:
                    globals.log += "(#) Page {} of chapter {} downloaded\n".format(index + 1, chapterNumber)
                    with open(filename, 'wb') as outfile:
                        outfile.write(img.content)
                    retrieved = True
                else:
                    globals.log += "(!) Unable to retrieve page {}, error code: {}, url = {}\n".format(index + 1, img.status_code, link)
                    if i < len(data["priorityServers"]):
                        globals.log += "(#) Trying next fallback server\n"
                    i += 1

            elif saveOption == "imgur":
                globals.log += "(#) Sending page {} of chapter {} to imgur\n".format(index + 1, chapterNumber)
                response = requests.post(globals.imgUploadLink, data=link, headers=headers)
                if response.status_code == 200:
                    globals.log += "(#) Page {} of chapter {} successfully sent to imgur\n".format(index + 1, chapterNumber)
                    pageIDs.append(response.json()["data"]["id"])
                    retrieved = True
                else:
                    globals.log += "(!) Failed to send page {} for chapter {} to imgur, error code: {}, url = {}\n".format(index + 1, chapterNumber, response.status_code, link)

        # ALL SERVERS FAIL
        reconnectAttempts = 0
        while not retrieved and reconnectAttempts < data["maxReconnectAttempts"]:
            globals.log += "(!) Unable to retrieve page {} of chapter {} from all attempts, attempting reconnection\n".format(index + 1, chapterNumber)
            reconnectAttempts += 1

            atHomeServer = requests.get(globals.mdlink + "/at-home/server/" + chapterID)
            if atHomeServer.status_code == 200:
                globals.log += "(#) New server found, url = {}\n".format(atHomeServer.json()["baseUrl"])
                globals.log += "(#) Running server test\n"

                standardServer = imageRetrieveTest(atHomeServer.json()["baseUrl"], chapterHash, page, quality, chapterID, report=True, getNewIfFail=True)

                link = standardServer + quality + chapterHash + '/' + page

                if standardServer is None:
                    globals.log += "(!) Server test failed, url = {}\n".format(atHomeServer.json()["baseUrl"])
                else:
                    globals.log += "(#) Server test success\n"

                if saveOption == "local":
                    globals.log += "(#) Downloading page {} of chapter {}\n".format(index + 1, chapterNumber)
                    img = requests.get(link)
                    extention = "." + page.split(".")[-1]
                    filename = "{}/manga/{}/{}/{}".format(globals.rootDir, mangaName, chapterNumber, zeropad(3, str(index + 1)) + extention)
                    if img.status_code == 200:
                        globals.log += "(#) Page {} of chapter {} downloaded\n".format(index + 1, chapterNumber)
                        with open(filename, 'wb') as outfile:
                            outfile.write(img.content)
                        retrieved = True
                    else:
                        globals.log += "(!) Unable to retrieve page {}, error code: {}, url = {}\n".format(index + 1, img.status_code, link)

                elif saveOption == "imgur":
                    globals.log += "(#) Sending page {} of chapter {} to imgur\n".format(index + 1, chapterNumber)
                    response = requests.post(globals.imgUploadLink, data=link, headers=headers)
                    if response.status_code == 200:
                        globals.log += "(#) Page {} of chapter {} successfully sent to imgur\n".format(index + 1, chapterNumber)
                        pageIDs.append(response.json()["data"]["id"])
                        retrieved = True
                    else:
                        globals.log += "(!) Failed to send page {} to imgur for chapter {}, error code: {}, url = {}\n".format(index + 1, chapterNumber, response.status_code, link)
            else:
                globals.log += "(!) Failed to send page {} for chapter {} to imgur, error code: {}, url = {}\n".format(index + 1, chapterNumber, response.status_code, link)

        if not retrieved:
            globals.log += "(!) Failed to retrieve page {} of chapter {} from all attempts\n".format(index + 1, chapterNumber)

            if len(pageIDs) > 0:
                globals.log += "(#) Attempting to delete pages {}-{} of chapter {} from account\n".format(1, index + 1, chapterNumber)
                del_headers = {
                    "authorization": headers["authorization"],
                    "x-rapidapi-key": headers["x-rapidapi-key"],
                    "x-rapidapi-host": headers["x-rapidapi-host"]
                }
                deleted = 0
                for delImgIndex, id in enumerate(pageIDs):
                    imgDel = requests.delete("https://imgur-apiv3.p.rapidapi.com/3/account/{}/image/{}".format(data["imgurUser"], id), headers=del_headers)
                    failedPages = {}
                    if imgDel.status_code == 200:
                        deleted += 1
                    else:
                        globals.log += "(!) Failed to delete page {}, pageID = {}".format(delImgIndex + 1, id)
                        failedPages[str(delImgIndex + 1)] = id

                if deleted == len(pageIDs):
                    globals.log += "(#) Successfully deleted pages {}-{} of chapter {} from account\n".format(1, index + 1, chapterNumber)
                else:
                    dateNow = datetime.now().isoformat().replace(":", " ")
                    globals.log += "(!) Failed to delete all of the pages {}-{} of chapter {} from account, error code: {}. Check failedPages{}.json for more details\n".format(1, index + 1, chapterNumber, imgDel.status_code, dateNow)
                    with open("{}/logs/jsons/failedPages{}.json".format(globals.rootDir, dateNow), 'w') as f:
                        json.dump(failedPages, f, indent=2)
            if saveOption == "local":
                return 0, 0, False
            elif saveOption == "imgur":
                return None, None, False

    if saveOption == "local":
        globals.log += "(#) All {} pages for chapter {} have been successfully downloaded\n".format(len(pages), chapterNumber)
        print("(#) Chapter {} download successful".format(chapterNumber))
        return 0, 0, True

    elif saveOption == "imgur":
        globals.log += "(#) All {} pages for chapter {} have been successfully sent to imgur\n".format(len(pages), chapterNumber)
        print("(#) Chapter {} send successful".format(chapterNumber))
        return pageIDs, contents, True
