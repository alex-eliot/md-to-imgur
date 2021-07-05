# A Mangadex collector, messenger

A simple project with the (currently) following functions.

 - Search and download manga chapters from the Mangadex's API
 - Send chapter pages to imgur albums
 - Create a .json file on Github with the appropriate format for cubari.moe
 - Shorten the link with git.io with support for custom link creation

# Dependencies

 - PyGithub
   + `pip3 install PyGithub`
 - dateutil
   + `pip3 install python-dateutil`

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
  "languageFilter": [
     "en"
  ],
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
   + `clientID`
 - Upload cubari.json to a Github repository with a custom name (and create git.io gist with custom link)
   + `githubToken`
   + `repoDirectory` (Must be in the format `"username/repo"`)
 - Automatically update imgurToken (access_token) running `refreshImgurToken.py` separately
   + `clientID`
   + `clientSecret`
   + `refreshToken`

# Running/Using

Simply `python3 main.py` to run. Manga search query is currently only available by title. Note that if a chapter has more than one groups that have released the same chapter, the program will indeed upload all selected chapters to imgur, BUT on the cubari.json, only the last one will be present. While I could make the program to separate them, cubari itself doesn't support more than one chapters having the same numbering, so it's meaningless for now. All of the uploaded imgur album IDs can be found in the logs, if you feel like digging and not spam your imgur account with unused images. The logs are verbose, so search for the matching term `id = ` to find the imgur IDs (yes, with spaces).

Quality of Life updates to the program "might" come. Currently, the only QoL feature is the program removing from your imgur account the previously uploaded pages of a chapter that failed to retrieve a page after all attempts (priority -> standard -> fallback -> reconnect n times). So for example, if the program uploaded 15 pages but the 16th fails, it will remove pages 1-15 (these are RapidAPI requests, for now).

Here are a few settings related searching and retrieving from Mangadex servers.

## Settings

 - `languageFilter`: Filter chapter by language, default=en (English)
 - `searchResultsLimit`: Search results limit (Mangadex values: min=1, max=100, default=10)
 - `chapterResultsLimit`: Chapter results limit (Mangadex values: min=1, max=500, default=100)
 - `priorityServers`: The program will attempt to retrieve the images first from the servers listed. If it fails to do so, it will move on to the standard servers.
 - `fallbackServers`: If retrieving from priority and/or standard servers fails, the program will attempt to retrieve the image from the fallback servers.
 - `maxReconnectAttempts`: If the program fails to retrieve from priority/standard/fallback, it will attempt n times to reconnect to a new md@home server and reattempt to send/retrieve the chapter pages.

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
 - Input `all except 5` or `allexcept5` to select all chapters except 5.

Note that when inputting selection, the numbers are following the chapters' indexes and not their numberings on Mangadex. Any spaces will be ignored.


<!--
## Uploading custom covers

If chosen to save to an imgur album, a prompt will appear asking if you wish to use a custom cover for the cubari.moe page.

 - Uploading from disk
   + Select `[1]: Local Path` and thus input relative or absolute path for the image.
 - Uploading from url
   + Select `[2]: Image link` and thus input the url pointing to the image. To make sure the given url doesn't get changed or moved by the respective web admin of the image's domain, the image will be uploaded anonymously to imgur (this will use the imgur's API and not rapidAPI's)

If you choose not to upload a custom cover, the program will assign the first page of the first chapter uploaded, as a cover. -->

## Saving to Github

As of lately, the program will have the prompts of whether you want to save to GitHub and create a gist are at the beginning (so that you can input all your settings and leave the computer waiting for the process to finish). Input `y` to proceed and then input a name to save the json file as. Note that the name must not have the .json extention. If you want your file to be named as `BestManga.json`, your input should be `BestManga`.

## Creating custom gist links

Lastly, if the chapter json is selected to be uploaded to Github, user is asked if they want to create a git.io gist for that file. Selecting yes will prompt the user to input a name for the custom URL. You can simply press enter without inputting anything, to create a random link, and not a custom one.
The program will finally print the finalized cubari page to the console.
For example `Cubari link: https://cubari.moe/read/gist/BestManga/`

## Request management

Imgur's API is limited to 1250 uploads per day, and 12500 requests per day (and a global limit of 50 uploads per hour and 500 requests per hour). For that reason, the program incorporates higher RapidAPI upload and request limits. The free plan offers 10,000 uploads and 100,000 total requests per month. As of the moment, the program doesn't do any tracking/checking for the remaining requests and uploads. Beware of the page count before uploading chapters, because if you pass the request limit on RapidAPI, you will be charged for every next request. My recommendation is to use a prepaid card with no credit, to avoid any potential charges that may occur. I am not responsible for any charges that may occur to you through using this program. Due to the complexity of the program regarding the requests (because of priority/fallback/reconnections, failures, etc.), it isn't easy to predict how many RapidAPI requests will be used, and calculating the worst-case scenario wouldn't be too practical 
