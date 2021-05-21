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

In order to use the program, you need to make a settings.json file with the (temporary) contents:

```json
{
  "imgurToken": "YOUR_IMGUR_TOKEN",
  "clientID": "YOUR_IMGUR_CLIENT_ID",
  "clientSecret": "YOUR_IMGUR_CLIENT_SECRET",
  "refreshToken": "YOUR_IMGUR_REFRESH_TOKEN",
  "x-rapidapi-key": "YOUR_X-RAPIDAPI-KEY",
  "githubToken": "YOUR_GITHUB_TOKEN",
  "repoDirectory": "YOUR_GITHUB_REPO_DIRECTORY",
  "languageFilter": "en",
  "searchResultsLimit": 30,
  "chapterResultsLimit": 500,
  "priorityServers": [],
  "fallbackServers": [],
  "maxReconnectAttempts": 10
}
```

Below are listed what you need to set up in `settings.json` to get several functions working

 - Search and save chapters locally
   + Nothing
 - Search and save chapters on an imgur album (with an active token) (also creates a `cubari.json` with the appropriate format)
   + `imgurToken`
   + `x-rapidapi-key`
 - Upload cubari.json to a Github repository with a custom name (and create git.io gist with custom link)
   + `githubToken`
   + `repoDirectory` (Must be in the format `"username/repo"`)
 - Upload a custom cover for the cubari page
   + `clientID`
 - Automatically update imgurToken (access_token) running `refreshImgurToken.py` separately
   + `clientID`
   + `clientSecret`
   + `refreshToken`

# Running/Using

Simply `python3 main.py` to run. Manga search query is currently only available by name. Here are a few settings related searching and retrieving from Mangadex servers.

## Settings

 - `languageFilter`: Filter chapter by language, default=en (English)
 - `searchResultsLimit`: Search results limit (Mangadex values: min=1, max=100, default=10)
 - `chapterResultsLimit`: Chapter results limit (Mangadex values: min=1, max=500, default=100)
 - `priorityServers`: The program will attempt to retrieve the images first from the servers listed. If it fails to do so, it will move on to the standard servers.
 - `fallbackServers`: If retrieving from priority and/or standard servers fails, the program will attempt to retrieve the image from the fallback servers.
 - `maxReconnectAttempts`: If the program fails to retrieve from priority/standard/fallback, it will attempt x times to reconnect to a new md@home server and reattempt to send/retrieve the chapter pages (Note, the program will inevitably attempt to retrieve the pages from the priority servers before moving to the new md@home server. In the future, the program will be updated to ignore priority and fallback servers in the case of reconnection).

## Selecting chapters

For example, if the chapter list is printed as such:

```
[1]: (en) Chapter 1 - No Group Scanlation
[2]: (en) Chapter 2 - No Group Scanlation
[3]: (en) Chapter 3 - No Group Scanlation
[4]: (en) Chapter 4 - No Group Scanlation
[5]: (en) Chapter 5 - No Group Scanlation
[6]: (en) Chapter 6 - No Group Scanlation
[7]: (en) Chapter 7 - No Group Scanlation
[8]: (en) Chapter 8 - No Group Scanlation
[9]: (en) Chapter 9 - No Group Scanlation
[10]: (en) Chapter 10 - No Group Scanlation
```

 - Input `4` to select chapter 4.
 - Input `1,2,5,10` to select chapters 1, 2, 5, 10.
 - Input `1-5` to select chapters 1, 2, 3, 4, 5
 - Input `1-3, 6-10` to select chapters 1, 2, 3, 6, 7, 8, 9, 10
 - Input `all` to select all listed chapters.

Note that when inputting selection, the numbers are following the chapters' indexes and not their numberings on Mangadex. Any spaces will be ignored.



## Uploading custom covers

If chosen to save to an imgur album, a prompt will appear asking if you wish to use a custom cover for the cubari.moe page.

 - Uploading from disk
   + Select `[1]: Local Path` and thus input relative or absolute path for the image.
 - Uploading from url
   + Select `[2]: Image link` and thus input the url pointing to the image. To make sure the given url doesn't get changed or moved by the respective web admin of the image's domain, the image will be uploaded anonymously to imgur (this will use the imgur's API and not rapidAPI's)

If you choose not to upload a custom cover, the program will assign the first page of the first chapter uploaded, as a cover.

## Saving to Github

After the image sending process is complete, a prompt appears asking whether you want to save the appropriately formatted cubari.json into a Github repo. Input `y` to proceed and then input a name to save the json file as. Note that the name must not have the .json extention. If you want your file to be named as `BestManga.json`, your input should be `BestManga`.

## Creating custom gist links

Lastly, if the image is selected to be uploaded to Github, user is asked if they want to create a git.io gist for that file. Selecting yes will prompt the user to input a name for the custom URL. You can simply press enter without inputting anything, to create a random link, and not a custom one.
The program will finally print the finalized cubari page to the console.
For example `Cubari link: https://cubari.moe/read/gist/BestManga/`

## Request management

Imgur's API is limited to 1250 uploads per day, and 12500 requests per day (and a global limit of 50 uploads per hour and 500 requests per hour). For that reason, the program incorporates higher RapidAPI upload and request limits. The free plan offers 10,000 uploads and 100,000 total requests per month. As of the moment, the program doesn't do any tracking/checking for the remaining requests and uploads. Beware of the page count before uploading chapters, because if you pass the request limit on RapidAPI, you will be charged for every next request. My recommendation is to use a prepaid card with no credit, to avoid any potential charges that may occur.

### Total RapidAPI requests depending on scenario

WIP

For the sake of consistency, let's declare the following:
 - Number of chapters selected: <img src="https://latex.codecogs.com/gif.latex?n\text{}"/>
 - Number of pages in chapter <img src="https://latex.codecogs.com/gif.latex?n\text{}"/>: <img src="https://latex.codecogs.com/gif.latex?k_n\text{}"/>
 - Number of priority servers: <img src="https://latex.codecogs.com/gif.latex?P\text{}"/>
 - Number of failure to receive from priority servers: "https://latex.codecogs.com/gif.latex?fail_P \leq P\text{}"/>
 - Number of fallback servers: <img src="https://latex.codecogs.com/gif.latex?F\text{}"/>
 - Number of failure to receive from fallback servers: <img src="https://latex.codecogs.com/gif.latex?fail_F \leq F\text{}"/>
 - Number of reconnection attempts: <img src="https://latex.codecogs.com/gif.latex?R\text{}"/>

 - Search and download chapters from Mangadex
   + None
 - Send a chapter to imgur (without custom cover)
   +

# Disclaimer

The project is created simply for educational use.
