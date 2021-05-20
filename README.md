# A Mangadex collector, messenger

A simple project with the (currently) following functions.

 - Search and download manga chapters from the Mangadex's API
 - Send chapter pages to imgur albums
 - Create a .json file on Github with the appropriate format for cubari.moe
 - Shorten the link with git.io with support for custom link creation

# Dependencies

 - PyGithub
   + `pip3 install PyGithub`

You will need PyGithub in order to send the .json file into your Github repository. As of the moment, this project will not run if PyGithub is not installed, but it will be an optional dependency in the future.

You will also need to have an imgur subscription in rapidAPI. For more information, [https://rapidapi.com/imgur/api/imgur-9/pricing](https://rapidapi.com/imgur/api/imgur-9/pricing). And the guide to set up the Client ID, Client Secret, Access Token, Refresh Token here: [https://rapidapi.com/blog/imgur-api-tutorial/](https://rapidapi.com/blog/imgur-api-tutorial/)

# Configuration

In order to use program, you need to make a settings.json file with the (temporary) contents:

```json
{
  "clientID": "YOUR_IMGUR_CLIENT_ID",
  "clientSecret": "YOUR_IMGUR_CLIENT_SECRET",
  "refreshToken": "YOUR_IMGUR_REFRESH_TOKEN",
  "x-rapidapi-key": "YOUR_X-RAPIDAPI-KEY",
  "githubToken": "YOUR_GITHUB_TOKEN",
  "maxReconnectAttempts": 10,
  "repoDirectory": "YOUR_GITHUB_REPO_DIRECTORY",
  "languageFilter": "en",
  "searchResultsLimit": 30,
  "chapterResultsLimit": 500,
  "fallbackServers": [],
  "imgurToken": "YOUR_IMGUR_TOKEN"
}```

Below are listed what you need to set up in settings.json to get several functions working

 - Search and save chapters locally
   + Nothing
 - Search and save chapters on an imgur album (with an active token) (also creates a cubari.json with the appropriate format)
   + imgurToken
   + x-rapidapi-key
 - Upload cubari.json to a Github repository with a custom name (and create git.io gist with custom link)
   + githubToken
   + repoDirectory (Must be in the format `"username/repo"`)
 - Upload a custom cover for the cubari page
   + clientID
 - Automatically update imgurToken (access_token) running auth.py separately
   + clientID
   + clientSecret
   + refreshToken

# Running/Using

Simply `python3 main.py` to run. Manga search query is currently only available by name. Change the

# Disclaimer

The project is simply created for educational use.
