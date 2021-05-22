import requests
import json

import globals

from github import Github

with open("settings.json", 'r') as f:
    data = json.load(f)

g = Github(data["githubToken"])

def makeFileAndGetGist(filedata, friendlyName):

    # Configure settings.json for the github directory you want to save to. For example: "user41/foobar"

    globals.log += "(#) Getting repository directory {}\n".format(data["repoDirectory"])
    repo = g.get_repo(data["repoDirectory"])

    globals.log += "(#) Creating file {} on main branch\n".format(friendlyName)
    repo.create_file(friendlyName, "", filedata, branch="main")

    raw_url = "https://github.com/{}/raw/main/{}".format(data["repoDirectory"], friendlyName)
    globals.log += "(#) Raw url = {}\n".format(raw_url)

    if input("Would you like to create a gist? (y/n): ") == "y":
        created = False
        while not created:
            customURL = input("Input custom name (leave empty if you want a random one): ")
            if customURL == "":
                globals.log += "(#) Creating gist with a random URL\n"
                r = requests.post("https://git.io/", data={"url": raw_url})
            else:
                globals.log += "(#) Creating gist with custom URL = {}\n".format(customURL)
                r = requests.post("https://git.io/", files={"url": (None, raw_url), "code": (None, customURL)})

            if r.status_code == 201:
                code = r.headers["Location"].split("/")[-1]
                gist = "https://cubari.moe/read/gist/{}/".format(code)
                globals.log += "(#) Gist created on link {}\n".format(gist)
                return gist
            elif r.status_code == 422:
                globals.log += "(#) Could not create gist with custom URL because it's already taken\n"
                print("(!) Could not create custom URL because it is taken, please try another.")
            else:
                globals.log += "(#) Could not create gist link, status code {}".format(r.status_code)
                return None
