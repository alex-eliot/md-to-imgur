import requests
from datetime import datetime
from auth import *

def zeropad(zeros, name):
    return "0" * (zeros - len(name)) + name

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

    curTime = requests.get("https://showcase.api.linx.twenty57.net/UnixTime/tounix?date=now")
    if curTime.status_code == 200:
        contents[chapterNumber]["last_updated"] = curTime.text[1:len(curTime.text)-1]
    else:
        print("(!) Failed to revieve current unix timestamp from server.")
        contents[chapterNumber]["last_updated"] = "1549892280"

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

    print("(#) Running server health test...")
    atHomeServer = imageRetrieveTest(atHomeServer, chapterHash, pages[0], quality, chapterID)

    print(""
    + "(#) Proceeding to download the rest pages..."           * (saveOption == "local")
    + "(#) Proceeding to send the rest pages to imgur..."      * (saveOption == "imgur")
    )
    pageIDs = []

    for index, page in enumerate(pages):
        link = atHomeServer.json()["baseUrl"] + quality + chapterHash + '/' + page

        if saveOption == "local":
            img = requests.get(link)
            extention = "." + page.split(".")[-1]
            filename = zeropad(3, str(index + 1)) + extention
            if img.status_code == 200:
                with open(filename, 'wb') as outfile:
                    outfile.write(img.content)
            else:
                print("(!) Unable to retrieve image, error code: " + str(img.status_code))

                if len(data["fallbackServers"]) == 0:
                    return None, None
                for server in data["fallbackServers"]:
                    print("(#) Retrying from {}".format(server))
                    if server[-1] == "/":
                        server = server[0:len(server) - 1]
                    link = server + quality + chapterHash + '/' + page
                    img = requests.get(link)
                    extention = "." + page.split(".")[-1]
                    filename = zeropad(3, str(index + 1)) + extention
                    if img.status_code == 200:
                        print("(#) Image successfully retrieved from reattempt.")
                        with open(filename, 'wb') as outfile:
                            outfile.write(img.content)
                    else:
                        return None, None

        elif saveOption == "imgur":
            response = requests.post(imgUploadLink, data=link, headers=headers)
            if response.status_code == 200:
                pageIDs.append(response.json()["data"]["id"])
            else:
                print("(!) Failed to send page {} to imgur for chapter {}.".format(index + 1, chapterNumber))

                if len(data["fallbackServers"]) == 0:
                    return None, None
                for server in data["fallbackServers"]:
                    if server[-1] == "/":
                        server = server[0:len(server) - 1]
                    print("(#) Retrying from {}...".format(server))
                    link = server + quality + chapterHash + '/' + page
                    response = requests.post(imgUploadLink, data=link, headers=headers)
                    if response.status_code == 200:
                        print("(#) Image successfully sent from reattempt.")
                        pageIDs.append(response.json()["data"]["id"])
                    else:
                        if len(pageIDs) > 0:
                            del_headers = {
                                "authorization": headers["authorization"],
                                "x-rapidapi-key": headers["x-rapidapi-key"],
                                "x-rapidapi-host": headers["x-rapidapi-host"]
                            }
                            for id in pageIDs:
                                requests.delete("https://imgur-apiv3.p.rapidapi.com/3/account/{}/image/{}".format(data["imgurUser"], id), headers=del_headers)
                        return None, None

    print(""
    + "(#) All pages for chapter {} have been successfully downloaded.".format(chapterNumber)       * (saveOption == "local")
    + "(#) All pages for chapter {} have been successfully sent to imgur.".format(chapterNumber)    * (saveOption == "imgur")
    )

    if saveOption == "imgur":
        return pageIDs, contents
    elif saveOption == "local":
        return 0, 0
