import requests
import dateutil.parser as dp
from datetime import datetime

def imageRetrieveTest(atHomeServer, hash, page, quality, chapterID):
    mdlink = "https://api.mangadex.org"
    link = atHomeServer.json()["baseUrl"] + quality + hash + '/' + page
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
        print("(#) Successfully retrieved image.")
        # extention = "." + page.split(".")[-1]
        # with open("test" + extention, 'wb') as outimg:
        #     outimg.write(testImg.content)
        payload = {"url": link, "success": True, "bytes": len(testImg.content), "duration": int(response_time), "cached": cached}
        requests.post("https://api.mangadex.network/report", data=payload)
        return atHomeServer
    else:
        print("(!) Unable to retrieve the image, error code: " + str(testImg.status_code))
        payload = {"url": link, "success": False, "bytes": len(testImg.content), "duration": int(response_time), "cached": cached}
        requests.post("https://api.mangadex.network/report", data=payload)
        print("(#) Finding another server...")
        atHomeServer = requests.get(mdlink + "/at-home/server/" + chapterID)
        return imageRetrieveTest(atHomeServer.json()["baseUrl"], hash, page, isDataSaver, chapterID)

def sendChapter(chapter, dataSaver, saveOption, data, headers):

    mdlink = "https://api.mangadex.org"
    imgurlink = "https://api.imgur.com"
    imgUploadLink = "https://imgur-apiv3.p.rapidapi.com/3/image"
    albumCreateLink = "https://imgur-apiv3.p.rapidapi.com/3/album"

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
    + "(#) Proceeding to download chapter {}.".format(chapterNumber)        * (saveOption == "local")
    + "(#) Sending chapter {} to imgur.".format(chapterNumber)              * (saveOption == "imgur")
    )

    chapterPagesOriginal = chapter["data"]["attributes"]["data"]
    chapterPagesDataSaver = chapter["data"]["attributes"]["dataSaver"]

    atHomeServer = requests.get(mdlink + "/at-home/server/" + chapterID)

    if dataSaver == "1":
        pages = chapterPagesOriginal
        quality = "/data/"
    elif dataSaver == "2":
        pages = chapterPagesDataSaver
        quality = "/data-saver/"

    print(""
    + "(#) Proceeding to download the rest pages..."           * (saveOption == "local")
    + "(#) Proceeding to send the rest pages to imgur..."      * (saveOption == "imgur")
    )
    pageIDs = []

    for index, page in enumerate(pages):
        retrieved = False

        # PRIORITY SERVERS
        i = 0
        while not retrieved and i < len(data["priorityServers"]):
            server = data["priorityServers"][i]
            if server[-1] == "/":
                server = server[0:len(server) - 1]
            link = server + quality + chapterHash + "/" + page

            if saveOption == "local":
                img = requests.get(link)
                extention = "." + page.split(".")[-1]
                filename = zeropad(3, str(index + 1)) + extention
                if img.status_code == 200:
                    with open(filename, 'wb') as outfile:
                        outfile.write(img.content)
                    retrieved = True
                else:
                    print("(!) Unable to retrieve page {}, error code: {}".format(index + 1, img.status_code))
                    if i < len(data["priorityServers"]):
                        print("(#) Trying next priority server...")
                    i += 1

            elif saveOption == "imgur":
                response = requests.post(imgUploadLink, data=link, headers=headers)
                if response.status_code == 200:
                    pageIDs.append(response.json()["data"]["id"])
                    retrieved = True
                else:
                    print("(!) Failed to send page {} to imgur for chapter {}.".format(index + 1, chapterNumber))


        # STANDARD SERVERS
        link = atHomeServer.json()["baseUrl"] + quality + chapterHash + '/' + page

        print("(#) Running server health test...")
        atHomeServer = imageRetrieveTest(atHomeServer, chapterHash, pages[0], quality, chapterID)

        if saveOption == "local":
            img = requests.get(link)
            extention = "." + page.split(".")[-1]
            filename = zeropad(3, str(index + 1)) + extention
            if img.status_code == 200:
                with open(filename, 'wb') as outfile:
                    outfile.write(img.content)
                retrieved = True
            else:
                print("(!) Unable to retrieve page {} from chapter {}, error code: {}".format(index + 1, img.status_code, img.status_code))

        elif saveOption == "imgur":
            response = requests.post(imgUploadLink, data=link, headers=headers)
            if response.status_code == 200:
                pageIDs.append(response.json()["data"]["id"])
                retrieved = True
            else:
                print("(!) Failed to send page {} to imgur for chapter {}, error code: {}.".format(index + 1, chapterNumber, response.status_code))


        # FALLBACK SERVERS
        i = 0
        while not retrieved and i < len(data["fallbackServers"]):
            link = data["fallbackServers"][i] + quality + chapterHash + "/" + page

            if saveOption == "local":
                img = requests.get(link)
                extention = "." + page.split(".")[-1]
                filename = zeropad(3, str(index + 1)) + extention
                if img.status_code == 200:
                    with open(filename, 'wb') as outfile:
                        outfile.write(img.content)
                    retrieved = True
                else:
                    print("(!) Unable to retrieve page {}, error code: {}".format(index + 1, img.status_code))
                    if i < len(data["priorityServers"]):
                        print("(#) Trying next priority server...")
                    i += 1

            elif saveOption == "imgur":
                response = requests.post(imgUploadLink, data=link, headers=headers)
                if response.status_code == 200:
                    pageIDs.append(response.json()["data"]["id"])
                    retrieved = True
                else:
                    print("(!) Failed to send page {} to imgur for chapter {}.".format(index + 1, chapterNumber))

        # ALL SERVERS FAIL
        reconnectAttempts = 0
        while not retrieved and reconnectAttempts < data["maxReconnectAttempts"]:
            reconnectAttempts += 1
            print("(!) Unable to retrieve page {} of chapter {} from all attempts, attempting reconnection...".format(index + 1, chapterNumber))
            atHomeServer = imageRetrieveTest(atHomeServer, chapterHash, page, quality, chapterID)

            link = atHomeServer.json()["baseUrl"] + quality + chapterHash + '/' + page

            if saveOption == "local":
                img = requests.get(link)
                extention = "." + page.split(".")[-1]
                filename = zeropad(3, str(index + 1)) + extention
                if img.status_code == 200:
                    with open(filename, 'wb') as outfile:
                        outfile.write(img.content)
                    retrieved = True
                else:
                    print("(!) Unable to retrieve page {} from chapter {}, error code: {}".format(index + 1, img.status_code, img.status_code))

            elif saveOption == "imgur":
                response = requests.post(imgUploadLink, data=link, headers=headers)
                if response.status_code == 200:
                    pageIDs.append(response.json()["data"]["id"])
                    retrieved = True
                else:
                    print("(!) Failed to send page {} to imgur for chapter {}, error code: {}.".format(index + 1, chapterNumber, response.status_code))

        if not retrieved:
            print("(!) Failed to retrieve page {} of chapter {} from all attempts.".format(index + 1, chapterNumber))

            if len(pageIDs) > 0:
                print("(#) Attempting to delete pages {}-{} of chapter {} from account".format(1, index + 1, chapterNumber))
                del_headers = {
                    "authorization": headers["authorization"],
                    "x-rapidapi-key": headers["x-rapidapi-key"],
                    "x-rapidapi-host": headers["x-rapidapi-host"]
                }
                deleted = 0
                for id in pageIDs:
                    imgDel = requests.delete("https://imgur-apiv3.p.rapidapi.com/3/account/{}/image/{}".format(data["imgurUser"], id), headers=del_headers)
                    failedPages = []
                    if imgDel.status_code == 200:
                        deleted += 1
                    else:
                        failedPages.append(str(index + 1))
                if deleted == len(pageIDs):
                    print("(#) Successfully deleted pages {}-{} of chapter {} from account.".format(1, index + 1, chapterNumber))
                else:
                    print("(!) Failed to delete all of the pages {}-{} of chapter {} from account, error code: {}".format(1, index + 1, chapterNumber, imgDel.status_code))
            return None, None

    print(""
    + "(#) All {} pages for chapter {} have been successfully downloaded.".format(len(pages), chapterNumber)       * (saveOption == "local")
    + "(#) All {} pages for chapter {} have been successfully sent to imgur.".format(len(pages), chapterNumber)    * (saveOption == "imgur")
    )

    if saveOption == "imgur":
        return pageIDs, contents
    elif saveOption == "local":
        return 0, 0
