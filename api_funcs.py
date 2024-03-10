import settings
import requests
from urllib.parse import urlencode

def fetchPuuid(gameName, tagLine, region = settings.REGION): #get a user's puuid from gameName, tagLine
    params = {'api_key': settings.API_KEY}
    endpoint = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"

    try:
        response = requests.get(endpoint, params=urlencode(params))
        response.raise_for_status()
        response_body = response.json()
        return response_body['puuid']
    except requests.exceptions.RequestException as err:
        print(f"Issue retrieiving summoner data from API: {err}") #to do: better error handling?
        return None

def fetchMatchIds(puuid, region = settings.REGION): #get most recent 100 matchIds from the given puuid 
    endpoint = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    params = {'api_key': settings.API_KEY, 'start': 0, 'count': 100}
    try:
        response = requests.get(endpoint, params=urlencode(params))
        response.raise_for_status()
        responseJSON = response.json()
        return responseJSON
    except requests.exceptions.RequestException as err:
        print(f"Issue retrieving match information: {err}") #to do: better error handling?
        return None

def fetchSummoners(matchId, region=settings.REGION): #use API to look up the match information from a matchId, then build and return a list of this data
    endpoint = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}"
    params = {'api_key': settings.API_KEY}
    try:
        response = requests.get(endpoint, params = urlencode(params))
        response.raise_for_status()
        responseJSON = response.json()
        puuidsRaw = str(responseJSON['metadata']['participants']).split(',') #turn list into string
        puuids = [str(puuidsRaw[x])[2:-1] for x in range(len(puuidsRaw)-1)] #THIS FAILS FOR LAST PUUID IN LIST - decreased range by one
        puuids.append(str(puuidsRaw[len(puuidsRaw)-1])[2:-2]) #fixes the last puuid's formatting to avoid issue... to-do, do this whole part better
        matchDTC = responseJSON['info']['gameStartTimestamp']
        queueId = responseJSON['info']['queueId']
        summonerData = []
        if int(queueId) in [1700, 1300, 1900, 1400, 700, 490, 450, 440, 430, 420, 400]: #this comes from riot's queues.json, just some gamemodes I picked to track
            i=0
            for i in range(len(puuids)): #build the list, one "row" for each puuid
                puuid = puuids[i]
                summonerData.append((puuid, matchId, queueId, matchDTC, f"{matchId}-{puuid}")) #last is rowGUID
                i=i+1
        return summonerData
    except requests.exceptions.RequestException as err:
        print(f"Issue retrieving match information: {err}") #to do: better error handling?
        return None
    
def fetchPuuids(puuid, region=settings.REGION_KEY):
    endpoint = f"https://{region}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
    params = {'api_key': settings.API_KEY}
    try:
        response = requests.get(endpoint, params = urlencode(params))
        response.raise_for_status()
        responseJSON = response.json()
        puuidsRaw = responseJSON['participants'] #turn list into string
        puuidsArr = []
        for x in range(len(puuidsRaw)):
            puuidsArr.append([puuids for key, puuids in puuidsRaw[x].items() if "puuid" in key])
        return puuidsArr
    except requests.exceptions.RequestException as err:
        print(f"Issue retrieving match information: {err}") #to do: better error handling?
        return None
    
def fetchSummonerFromPuuid(puuid, region=settings.REGION):
    endpoint = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    params = {'api_key': settings.API_KEY}
    try:
        response = requests.get(endpoint, params = urlencode(params))
        response.raise_for_status()
        responseJSON = response.json()
        gameName = responseJSON['gameName']
        tagLine = responseJSON['tagLine']
        return f"{gameName}#{tagLine}"
    except requests.exceptions.RequestException as err:
        print(f"Issue retrieving match information: {err}") #to do: better error handling?
        return None
    
def fetchChampInfo(matchId, myPuuid, otherPuuid, region = settings.REGION):
    endpoint = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}"
    params = {'api_key': settings.API_KEY}
    try:
        response = requests.get(endpoint, params = urlencode(params))
        response.raise_for_status()
        responseJSON = response.json()
        myIndex = responseJSON['metadata']['participants'].index(myPuuid)
        otherIndex = responseJSON['metadata']['participants'].index(otherPuuid)
        myChamp = responseJSON['info']['participants'][myIndex]['championName']
        otherChamp = responseJSON['info']['participants'][otherIndex]['championName']
        myKills = int(responseJSON['info']['participants'][myIndex]['kills'])
        myAssists = int(responseJSON['info']['participants'][myIndex]['assists'])
        myDeaths = int(responseJSON['info']['participants'][myIndex]['deaths'])
        otherKills = int(responseJSON['info']['participants'][otherIndex]['kills'])
        otherAssists = int(responseJSON['info']['participants'][otherIndex]['assists'])
        otherDeaths = int(responseJSON['info']['participants'][otherIndex]['deaths'])
        myKDA = (myKills + myAssists)/myDeaths
        otherKDA = (otherKills + otherAssists)/otherDeaths
        positionsRaw = [responseJSON['info']['participants'][myIndex]['teamPosition'], responseJSON['info']['participants'][otherIndex]['teamPosition']]
        positionsFormatted = []
        x = 0
        for x in range(len(positionsRaw)):
            if positionsRaw[x] == "TOP":
                positionsFormatted.append("Top")
            elif positionsRaw[x] == "JUNGLE":
                positionsFormatted.append("Jungle")
            elif positionsRaw[x] == "MIDDLE":
                positionsFormatted.append("Middle")
            elif positionsRaw[x] == "BOTTOM":
                positionsFormatted.append("ADC")
            else:
                positionsFormatted.append("Support")
        myPosition = positionsFormatted[0]
        otherPosition = positionsFormatted[1]
        if responseJSON['info']['participants'][myIndex]['win'] is True:
            myOutcome = 'win'
        else:
            myOutcome = 'loss'
        if responseJSON['info']['participants'][myIndex]['win'] == responseJSON['info']['participants'][otherIndex]['win']:
            sameTeam = True
            otherOutcome = myOutcome
        else:
            sameTeam = False
            if responseJSON['info']['participants'][myIndex]['win'] is True:
                otherOutcome = 'loss'
            else:
                otherOutcome = 'win'
        myData = [myChamp, myPosition, myKDA, myOutcome]
        otherData = [otherChamp, otherPosition, otherKDA, otherOutcome]
        return myData, otherData, sameTeam #simplify the above later...
    except requests.exceptions.RequestException as err:
        print(f"Issue retrieving match information: {err}") #to do: better error handling?
        return None