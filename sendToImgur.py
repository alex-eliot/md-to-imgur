import requests
import dateutil.parser as dp

import globals

from datetime import datetime

def zeropad(zeros, name):
    return "0" * (zeros - len(name)) + name

def reportServer(link, success, bytes, duration, cached):
    globals.log += "{} (#) Reporting: url: {}, success: {}, bytes: {}, duration: {}, cached: {}\n".format(datetime.now().isoformat().split(".")[0], link, success, bytes, duration, cached)
    payload = {"url": link, "success": success, "bytes": bytes, "duration": duration, "cached": cached}
    report = requests.post("https://api.mangadex.network/report", data=payload)
    return report.status_code

def saveLocal(mangaName, pageNumber, chapterNumber, link):
    globals.log += "{} (#) Downloading page {} of chapter {}\n".format(datetime.now().isoformat().split(".")[0], pageNumber, chapterNumber)
    img = requests.get(link)
    extention = "." + link.split(".")[-1]
    filename = "{}/manga/{}/{}/{}".format(globals.rootDir, mangaName, chapterNumber, zeropad(3, str(pageNumber)) + extention)
    if img.status_code == 200:
        globals.log += "{} (#) Page {} of chapter {} downloaded\n".format(datetime.now().isoformat().split(".")[0], pageNumber, chapterNumber)
        with open(filename, 'wb') as outfile:
            outfile.write(img.content)
        return True
    else:
        globals.log += "{} (!) Unable to retrieve page {}, error code: {}, url = {}\n".format(datetime.now().isoformat().split(".")[0], pageNumber, img.status_code, link)
        if i < len(data["priorityServers"]):
            globals.log += "{} (#) Trying next priority server\n".format(datetime.now().isoformat().split(".")[0])
        i += 1
        return False

def saveToImgur(mangaName, pageNumber, chapterNumber, link, pageIDs):
    globals.log += "{} (#) Sending page {} of chapter {} to imgur\n".format(datetime.now().isoformat().split(".")[0], pageNumber, chapterNumber)
    response = requests.post(globals.imgUploadLink, data=link, headers=globals.headers)
    if response.status_code == 200:
        globals.log += "{} (#) Page {} of chapter {} successfully sent to imgur\n".format(datetime.now().isoformat().split(".")[0], pageNumber, chapterNumber)
        pageIDs.append(response.json()["data"]["id"])
        return pageIDs, True
    else:
        globals.log += "{} (!) Failed to send page {} for chapter {} to imgur, error code: {}, url = {}\n".format(datetime.now().isoformat().split(".")[0], pageNumber, chapterNumber, response.status_code, link)
        return pageIDs, False


def imageRetrieveTest(atHomeServer, hash, page, quality, chapterID, data, report=False, getNewIfFail=False):
    link = atHomeServer + quality + hash + '/' + page
    success = False

    globals.log += "{} (#) Getting test image\n".format(datetime.now().isoformat().split(".")[0])
    start_time = datetime.now()
    testImg = requests.get(link)
    end_time = datetime.now()

    if "X-Cache" in testImg.headers:
        cached = (testImg.headers["X-Cache"] == "HIT")
    else:
        cached = False

    time_diff = end_time - start_time
    response_time = time_diff.total_seconds() * 1000

    if testImg.status_code == 200 and "Content-Type" in testImg.headers:
        if "image/" in testImg.headers["Content-Type"]:
            success = True
            globals.log += "{} (#) Test image successfully received\n".format(datetime.now().isoformat().split(".")[0])
            # extention = "." + page.split(".")[-1]
            # with open("test" + extention, 'wb') as outimg:
            #     outimg.write(testImg.content)
            if report:
                reportServer(link, success, len(testImg.content), int(response_time), cached)
            return atHomeServer

    globals.log += "{} (!) Unable to retrieve test image, error code {}\n".format(datetime.now().isoformat().split(".")[0], testImg.status_code)
    if report:
        reportServer(link, success, len(testImg.content), int(response_time), cached)
    if getNewIfFail:
        reconnections = 0
        while reconnections < data["maxReconnectAttempts"]:
            reconnections += 1
            globals.log += "{} (#) Finding another server\n".format(datetime.now().isoformat().split(".")[0])
            atHomeServer = requests.get("{}/at-home/server/{}?forcePort443=true".format(globals.mdlink, chapterID)).json()["baseUrl"]
            atHomeServer = imageRetrieveTest(atHomeServer, hash, page, quality, chapterID, data, report=report, getNewIfFail=False)
            if atHomeServer is not None:
                return atHomeServer

    else:
        return None

def sendChapter(chapter, mangaName, dataSaver, saveOption, data):

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
        globals.log += "{} (#) Testing priority servers\n".format(datetime.now().isoformat().split(".")[0])
    for index, priorityServer in enumerate(data["priorityServers"]):
        if imageRetrieveTest(priorityServer, chapterHash, pages[0], quality, chapterID, data, report=False, getNewIfFail=False) is None:
            data["priorityServers"].pop(index)
            globals.log += "{} (!) Server {} failed to retrieve test image, removing from list\n".format(datetime.now().isoformat().split(".")[0], priorityServer)
        else:
            globals.log += "{} (#) Server {} successfully retrieved the test image\n".format(datetime.now().isoformat().split(".")[0], priorityServer)

    if len(data["fallbackServers"]) > 0:
        globals.log += "{} (#) Testing fallback servers\n".format(datetime.now().isoformat().split(".")[0])
    for index, fallbackServer in enumerate(data["fallbackServers"]):
        if imageRetrieveTest(fallbackServer, chapterHash, pages[0], quality, chapterID, data, report=False, getNewIfFail=False) is None:
            data["fallbackServers"].pop(index)
            globals.log += "{} (#) Server {} failed to retrieve test image, removing from list\n".format(datetime.now().isoformat().split(".")[0], fallbackServer)
        else:
            globals.log += "{} (#) Server {} successfully retrieved the test image\n".format(datetime.now().isoformat().split(".")[0], fallbackServer)

    globals.log += "{} (#) Receiving md@home server address for chapter {}. ChapterID={} ChapterHash={}\n".format(datetime.now().isoformat().split(".")[0], chapterNumber, chapterID, chapterHash)
    atHomeServer = requests.get("{}/at-home/server/{}?forcePort443=true".format(globals.mdlink, chapterID))
    globals.log += "{} (#) Server retrieval returned status code {}\n".format(datetime.now().isoformat().split(".")[0], atHomeServer.status_code)
    if atHomeServer.status_code == 200:
        globals.log += "{} (#) Server url = {}\n".format(datetime.now().isoformat().split(".")[0], atHomeServer.json()["baseUrl"])
        globals.log += "{} (#) Testing standard server\n".format(datetime.now().isoformat().split(".")[0])
        standardServer = imageRetrieveTest(atHomeServer.json()["baseUrl"], chapterHash, pages[0], quality, chapterID, data, report=True, getNewIfFail=True)
        if standardServer is None:
            globals.log += "{} (!) Server test failed, url = {}".format(datetime.now().isoformat().split(".")[0], atHomeServer.json()["baseUrl"])
        else:
            globals.log += "{} (#) Server test success\n".format(datetime.now().isoformat().split(".")[0])


    for index, page in enumerate(pages):
        globals.log += "{} (#) Proceeding with page {} of chapter {}\n".format(datetime.now().isoformat().split(".")[0], index + 1, chapterNumber)
        globals.log += "{} (#) Page link: {}\n".format(datetime.now().isoformat().split(".")[0], page)
        retrieved = False

        # PRIORITY SERVERS
        i = 0
        while not retrieved and i < len(data["priorityServers"]):
            globals.log += "{} (#) Receiving from priority server no.{}.\n".format(datetime.now().isoformat().split(".")[0], i + 1)

            server = data["priorityServers"][i]
            if server[-1] == "/":
                server = server[0:len(server) - 1]

            link = server + quality + chapterHash + "/" + page
            globals.log += "{} (#) Server no.{}, full link: {}\n".format(datetime.now().isoformat().split(".")[0], i + 1, link)

            if saveOption == "local":
                retrieved = saveLocal(mangaName, index + 1, chapterNumber, link)

            elif saveOption == "imgur":
                pageIDs, retrieved = saveToImgur(mangaName, index + 1, chapterNumber, link, pageIDs)

        # STANDARD SERVERS
        if not retrieved:
            globals.log += "{} (!) Unable to download/send image from all priority servers\n".format(datetime.now().isoformat().split(".")[0]) * (len(data["priorityServers"]) > 0)
            globals.log += "{} (#) Proceeding with standard servers\n".format(datetime.now().isoformat().split(".")[0])

            if standardServer is not None:
                link = standardServer + quality + chapterHash + '/' + page
                globals.log += "{} (#) Full page link: {}\n".format(datetime.now().isoformat().split(".")[0], link)

                if saveOption == "local":
                    retrieved = saveLocal(mangaName, index + 1, chapterNumber, link)

                elif saveOption == "imgur":
                    pageIDs, retrieved = saveToImgur(mangaName, index + 1, chapterNumber, link, pageIDs)


        # FALLBACK SERVERS
        i = 0
        while not retrieved and i < len(data["fallbackServers"]):
            globals.log += "{} (#) Receiving from fallback server no.{}.\n".format(datetime.now().isoformat().split(".")[0], i + 1)

            server = data["fallbackServers"][i]
            if server[-1] == "/":
                server = server[0:len(server) - 1]
            link = data["fallbackServers"][i] + quality + chapterHash + "/" + page

            globals.log += "{} (#) Server no.{} full link: {}\n".format(datetime.now().isoformat().split(".")[0], i + 1, link)

            if saveOption == "local":
                retrieved = saveLocal(mangaName, index + 1, chapterNumber, link)

            elif saveOption == "imgur":
                pageIDs, retrieved = saveToImgur(mangaName, index + 1, chapterNumber, link, pageIDs)

        # ALL SERVERS FAIL -> RECONNECTION
        if not retrieved:
            globals.log += "{} (!) Unable to retrieve page {} of chapter {} from all attempts, attempting reconnection\n".format(datetime.now().isoformat().split(".")[0], index + 1, chapterNumber)

            atHomeServer = requests.get("{}/at-home/server/{}?forcePort443=true".format(globals.mdlink, chapterID))
            standardServer = imageRetrieveTest(atHomeServer.json()["baseUrl"], chapterHash, page, quality, chapterID, data, report=True, getNewIfFail=True)

            if standardServer is None:
                globals.log += "{} (!) Server test failed, url = {}\n".format(datetime.now().isoformat().split(".")[0], atHomeServer.json()["baseUrl"])
            else:
                globals.log += "{} (#) Server test success\n".format(datetime.now().isoformat().split(".")[0])

                link = standardServer + quality + chapterHash + '/' + page

                globals.log += "{} (#) New server found, Full url = {}\n".format(datetime.now().isoformat().split(".")[0], link)

                if saveOption == "local":
                    retrieved = saveLocal(mangaName, index + 1, chapterNumber, link)

                elif saveOption == "imgur":
                    pageIDs, retrieved = saveToImgur(mangaName, index + 1, chapterNumber, link, pageIDs)

        # ALL ATTEMPTS FAIL -> DELETE IMAGES
        if not retrieved:
            if len(pageIDs) > 0:
                globals.log += "{} (#) Attempting to delete pages {}-{} of chapter {} from account\n".format(datetime.now().isoformat().split(".")[0], 1, index + 1, chapterNumber)
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
                        globals.log += "{} (!) Failed to delete page {}, pageID = {}".format(datetime.now().isoformat().split(".")[0], delImgIndex + 1, id)
                        failedPages[str(delImgIndex + 1)] = id

                if deleted == len(pageIDs):
                    globals.log += "{} (#) Successfully deleted pages {}-{} of chapter {} from account\n".format(datetime.now().isoformat().split(".")[0], 1, index + 1, chapterNumber)
                else:
                    dateNow = datetime.now().isoformat().replace(":", " ")
                    globals.log += "{} (!) Failed to delete all of the pages {}-{} of chapter {} from account, error code: {}. Check failedPages{}.json for more details\n".format(datetime.now().isoformat().split(".")[0], 1, index + 1, chapterNumber, imgDel.status_code, dateNow)
                    with open("{}/logs/jsons/failedPages{}.json".format(globals.rootDir, dateNow), 'w') as f:
                        json.dump(failedPages, f, indent=2)
            if saveOption == "local":
                return 0, 0, False
            elif saveOption == "imgur":
                return None, None, False

    if saveOption == "local":
        globals.log += "{} (#) All {} pages for chapter {} have been successfully downloaded\n".format(datetime.now().isoformat().split(".")[0], len(pages), chapterNumber)
        print("(#) Chapter {} download successful".format(chapterNumber))
        return 0, 0, True

    elif saveOption == "imgur":
        globals.log += "{} (#) All {} pages for chapter {} have been successfully sent to imgur\n".format(datetime.now().isoformat().split(".")[0], len(pages), chapterNumber)
        print("(#) Chapter {} send successful".format(chapterNumber))
        return pageIDs, contents, True
