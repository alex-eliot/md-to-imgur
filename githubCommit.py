import requests
import json
from github import Github

with open("settings.json", 'r') as f:
    data = json.load(f)

g = Github(data["githubToken"])

def makeFileAndGetGist(filedata, friendlyName, createGitIo):
    repo = g.get_repo(data["repoDirectory"])
    repo.create_file(friendlyName, "", filedata, branch="main")
    raw_url = "https://github.com/{}/raw/main/{}".format(data["repoDirectory"], friendlyName)

    if createGitIo == "y":
        customName = input("Input a custom name for the cubari link (leave empty to create a random one): ")
        files = {
            "url": (None, raw_url),
            "code": (None, customName)
            }

        if customName == "":
            r = requests.post("https://git.io/", files={"url": (None, raw_url)})
        else:
            r = requests.post("https://git.io/", files=files)

        if r.status_code == 201:
            code = r.headers["Location"].split("/")[-1]
            return "https://cubari.moe/read/gist/{}/".format(code)

    return None
