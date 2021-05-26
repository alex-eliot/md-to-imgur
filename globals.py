import os

def init():
    global mdlink
    global imgurlink
    global imgurUploadLink
    global imgUploadLink
    global albumCreateLink
    global log
    global rootDir
    global headers

    mdlink = "https://api.mangadex.org"
    imgurlink = "https://api.imgur.com"
    imgurUploadLink = "https://api.imgur.com/3/image"
    imgUploadLink = "https://imgur-apiv3.p.rapidapi.com/3/image"
    albumCreateLink = "https://imgur-apiv3.p.rapidapi.com/3/album"

    log = ""
    rootDir = str(os.getcwd()).replace("\\", '/')

    headers = {}
