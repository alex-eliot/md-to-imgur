import requests
import json
from github import Github

with open("settings.json", 'r') as f:
    data = json.load(f)

g = Github(data["githubToken"])

def makeFileAndGetGist(filedata, friendlyName):
    url = "https://git.io/create"

    # Configure settings.json for the github directory you want to save to. For example: "user41/foobar"
    repo = g.get_repo(data["repoDirectory"])
    repo.create_file(friendlyName, "", filedata, branch="main")

    raw_url = "https://raw.githubusercontent.com/ateteen-plus/foobar1/main/{}".format(friendlyName)

    r = requests.post(url, data={"url": raw_url})
    if r.status_code == 200:
        return "https://cubari.moe/read/gist/{}/".format(r.text)
    else:
        return None

def self_start():
    with open("cubari.json", 'r') as f:
        cubariJson = json.load(f)

    friendlyName = input("Input a friendly name for the json file on GitHub (without the extention): ").replace(' ', '') + ".json"
    cubariPage = makeFileAndGetGist(json.dumps(cubariJson, indent=2), friendlyName)
    print("\nCubari page: {}".format(cubariPage))
