import requests
import json

# RUN THIS PROGRAM IF YOUR IMGUR TOKEN HAS EXPIRED TO CREATE A NEW ONE

def getImgurToken(imgurlink, data):
    clientId = data["clientID"]
    clientSecret = data["clientSecret"]
    refreshtoken = data["refreshToken"]
    payload = {"refresh_token": refreshtoken, "client_id": clientId, "client_secret": clientSecret, "grant_type": "refresh_token"}
    r = requests.post(imgurlink + "/oauth2/token", data=payload)

    data["imgurToken"] = r.json()["access_token"]
    with open("settings.json", 'w') as f:
        json.dump(data, f, indent=2)

    return 0

with open("settings.json", 'r') as f:
    data = json.load(f)

getImgurToken("https://api.imgur.com", data)
