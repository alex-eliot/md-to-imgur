import requests
import json
from github import Github

with open("settings.json", 'r') as f:
    data = json.load(f)

g = Github(data["githubToken"])

def makeFileAndGetGist(filedata, friendlyName):

    # Configure settings.json for the github directory you want to save to. For example: "user41/foobar"
    repo = g.get_repo(data["repoDirectory"])
    repo.create_file(friendlyName, "", filedata, branch="main")

    raw_url = "https://github.com/{}/raw/main/{}".format(data["repoDirectory"], friendlyName)

    if input("Would you like to create a gist? (y/n): ") == "y":
        created = False
        while not created:
            customURL = input("Input custom name (leave empty if you want a random one): ")
            if customURL == "":
                r = requests.post("https://git.io/", data={"url": raw_url})
            else:
                r = requests.post("https://git.io/", files={"url": (None, raw_url), "code": (None, customURL)})

            r = requests.post("https://git.io/", data={"url": raw_url})
            if r.status_code == 201:
                code = r.headers["Location"].split("/")[-1]
                return "https://cubari.moe/read/gist/{}/".format(code)
            elif r.status_code == 422:
                print("(!) Could not create custom link because it is taken, please try another.")
            else:
                return None
