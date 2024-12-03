import requests
import json
import os

from dotenv import load_dotenv

load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")

REGION = "AMERICAS"
REGIONAL_HOST = "americas.api.riotgames.com"
PLATFORM = "NA1"
PLATFORM_HOST = "na1.api.riotgames.com"

byRiotID = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
byPUUID = "https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-puuid/"
bySummoner = "https://na1.api.riotgames.com/tft/league/v1/entries/by-summoner/"

RANK_ORDER = {
    "CHALLENGER" : 1,
    "GRANDMASTER" : 2,
    "MASTER" : 3,
    "DIAMOND" : 4,
    "PLATINUM" : 5,
    "GOLD" : 6,
    "SILVER" : 7,
    "BRONZE" : 8,
    "IRON" : 9
}

RANK_POSITION = {
    "I" : 1,
    "II" : 2,
    "III" : 3,
    "IV" : 4,
}

header = {
    "X-Riot-Token" : RIOT_KEY
}

def saveToJSON(file, data):
    try:
        with open(file, "r") as json_File:
            loadedData = json.load(json_File)
    except (FileNotFoundError, json.JSONDecodeError):
        loadedData = {}

    loadedData.update(data)

    players = [
        {
            "name": summoner,
            **info
        }
        for summoner, info in loadedData.items()
    ]

    players.sort(
        key=lambda x: (
            RANK_ORDER.get(x["Ranked Data"]["tier"].upper(), 10),  
            RANK_POSITION.get(x["Ranked Data"]["rank"].upper(), 10),  
            -x["Ranked Data"]["leaguePoints"]  
        )
    )

    sortedData = {
        player["name"]: {
            "Tag": player["Tag"],
            "PUUID": player["PUUID"],
            "Summoner Data": player["Summoner Data"],
            "Ranked Data": player["Ranked Data"]
        }
        for player in players
    }

    with open(file, "w") as json_File:
        json.dump(sortedData, json_File, indent=4)

def fetchCall(url):
    try:
        response = requests.get(url, headers = header)
        response.raise_for_status()

        data = response.json()
        return data

    except requests.exceptions.HTTPError as http_Err:
        print(f"HTTP error: {http_Err}")
    except requests.exceptions.RequestException as req_Err:
        print(f"Request error occured: {req_Err}")
    except KeyError:
        print("unexpected")
    return None

def getPUUID(summonerName, tagLine):
    url = f"{byRiotID}{summonerName}/{tagLine}"
    data = fetchCall(url)

    return data.get("puuid") if data else None

def getSummoner(puuid):
    url = f"{byPUUID}{puuid}"
    data = fetchCall(url)

    summonerID = data.get("id")

    return data.get("id")

def getTFTRankedData(summonerID):
    url = f"{bySummoner}{summonerID}"
    data = fetchCall(url)

    for entry in data:
        if entry.get("queueType") == "RANKED_TFT":
            tier = entry.get("tier")
            rank = entry.get("rank")
            leaguePoints = entry.get("leaguePoints")
            wins = entry.get("wins")
            losses = entry.get("losses")
            hotStreak = entry.get("hotStreak")

    return {
        "tier" : tier,
        "rank" : rank,
        "leaguePoints" : leaguePoints,
        "wins" : wins,
        "losses" : losses,
        "hotStreak" : hotStreak,
    } 

    return None

def refreshLeaderboard(file):
    updatedData = {}  

    try:
        with open(file, "r") as json_file:  
            loadedData = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        loadedData = {} 

    for summonerName, info in loadedData.items():
        puuid = info["PUUID"]
        summonerID = getSummoner(puuid)
        if not summonerID:
            print(f"Failed to fetch for {summonerName}. Skipping...")
            continue

        rankedData = getTFTRankedData(summonerID)
        if not rankedData:
            print(f"No ranked data found for {summonerName}. Skipping...")
            continue

        updatedData[summonerName] = {
            "Tag": info["Tag"],
            "PUUID": info["PUUID"],
            "Summoner Data": info["Summoner Data"],
            "Ranked Data": rankedData,
        }

    with open(file, "w") as json_file:  
        json.dump(updatedData, json_file, indent=4)

    print("Refreshed")
    return True

def combineDataAndSave(file, puuid, summonerName, tagLine, summonerData, rankedData):
    try:
        with open(file, "r") as jsonFile:
            loadedData = json.load(jsonFile)
    except (FileNotFoundError, json.JSONDecodeError):
        loadedData = {}

    normalizeSummonerName = summonerName.lower()
    normalizeTagLine = tagLine.lower()

    for existingSummoner, info in loadedData.items():
        if existingSummoner.lower() == normalizeSummonerName and info["Tag"].lower() == normalizeTagLine:
            print(f"{summonerName}#{tagLine} already exists, skipping.")
            return False  

    if rankedData:
        combinedData = {
            summonerName: {
                "Tag": tagLine,
                "PUUID": puuid,
                "Summoner Data": summonerData,
                "Ranked Data": rankedData
            }
        }

        loadedData.update(combinedData)

        with open(file, "w") as jsonFile:
            json.dump(loadedData, jsonFile, indent=4)

        print(f"Added {summonerName}#{tagLine} to the leaderboard.")
        return True  

    return False  


      
        

#testing
##summonerName = "Hayt"
##tagLine = "Life"

##puuid = getPUUID(summonerName, tagLine)
##summonerData = getSummoner(puuid)
##TFTRankedData = getTFTRankedData(summonerData)

##puuid2 = getPUUID("clo", "goat")
##summonerData2 = getSummoner(puuid2)
##TFTRankedData2 = getTFTRankedData(summonerData2)

##puuid3 = getPUUID("bachiXP", "NA1")
##summonerData3 = getSummoner(puuid3)
##tftRankedData3 = getTFTRankedData(summonerData3)


##if puuid:
    ##print(f"PUUID for: {summonerName} # {tagLine} : {puuid}")
  ##  print(f"Summoner ID: {summonerData}")
   ## print(f"TFT Ranked Data: {TFTRankedData}")

   ## combineDataAndSave("saved.json", puuid3, "bachiXP", "NA1", summonerData3, tftRankedData3)
  ##  combineDataAndSave("saved.json", puuid, summonerName, tagLine, summonerData, TFTRankedData)
  ##  combineDataAndSave("saved.json", puuid2, "clo", "goat", summonerData2, TFTRankedData2)
##else:
    ##print("Failed")