from inputs import get_name
from api_funcs import fetchPuuid, fetchMatchIds, fetchSummoners, fetchPuuids, fetchSummonerFromPuuid, fetchChampInfo
from db import createTables, retrieveMatchIds, saveExclusion, saveHost, saveMatchId, saveSummoner, saveNewMatchIds
from datetime import datetime
import sqlite3
import time
import settings
import exclude

""" todo - 
reduce number of globals
refactor the below
"""

def main():
    createTables() #create all tables if don't already exist

    con = sqlite3.connect("runback.db")
    cursor = con.cursor()

    saveExclusion(exclude.exclusions, cursor) #if you changed exclusions file since last run, will update. otherwise, nothing happens.

    checkIfHostExists = cursor.execute("SELECT * FROM host") #is there already a host?
    
    if checkIfHostExists.fetchone() is None: #if host table has no records, get the host's summoner info and puuid
        hostSummoner = get_name() #ask to input name
        puuid = fetchPuuid(hostSummoner[0], hostSummoner[1]) #get puuid from API
        saveHost(hostSummoner[0], hostSummoner[1], puuid, cursor) #save summonerName and puuid into db
        matchIds = fetchMatchIds(puuid) #get 100 matchIds from puuid
        saveMatchId(matchIds, cursor) #save matchIds to db
        i=0
        for i in range(len(matchIds)): #iterate over matchIds getting information and saving to file
            summonerData = fetchSummoners(matchIds[i])
            time.sleep(1.5) #to get around API limit
            saveSummoner(summonerData, cursor)
        print(f"Successfully saved summoner {hostSummoner[0]}#{hostSummoner[1]} as the host user.\n Run this program each time you load into a match to check if there are any Summoners in that match you have previously played with!")
    
    getPuuid = cursor.execute("SELECT puuid FROM host") #get the host puuid db entry
    matchIdsAPI = fetchMatchIds(str(getPuuid.fetchone())[2:-3]) #get matchIds from puuid, after putting puuid in a format API can understand
    matchIdsDB = retrieveMatchIds(cursor) #get the matchIds which already exist in DB
    saveNewMatchIds(matchIdsDB, matchIdsAPI, cursor) #save only the new matchIds to DB

    firstRun = 0 #cheap way to escape later down
    
    exclusionsList = [] #get this list started, will fill it with your exclusions
    for exclusion in exclude.exclusions:
        for excluded in exclusion:
            exclusionsList.append(excluded) #build your exclusion list, e.g. the people you frequently queue with
    
    recentSummonerPuuids = fetchPuuids(settings.MY_PUUID) #the current match you are loaded into
    for puuidValue in recentSummonerPuuids: #iterate over the recent puuids
        formatted1 = str(puuidValue)
        formatted2 = formatted1[2:-2]
        if formatted2 not in exclusionsList: #is the currrent puuid not excluded?
            retrievePuuidMatches = cursor.execute(f"SELECT puuid, matchId, matchDTC FROM summoners WHERE puuid = '{formatted2}' ORDER BY matchDTC") #select db rows where this puuid can be found
            puuidMatches = retrievePuuidMatches.fetchall() #get all those matched rows
            if len(puuidMatches) > 0: #it is someone you have played with before
                puuidMatchesArr = []
                for puuids in puuidMatches: #put them in a list instead of tuples, clean this up later
                    for duplicatePuuid in puuids:
                        puuidMatchesArr.append(duplicatePuuid)
                matchedSummonerName = fetchSummonerFromPuuid(puuidMatchesArr[0]) #get the 'summoner name' instead of the puuid
                mostRecentMatchTime = datetime.fromtimestamp(int(puuidMatchesArr[-1])/1000).strftime('%Y-%m-%d %H:%M:%S') #get the datetime instead of unix epoch time (uses user timezone, maybe fix this later)
                mostRecentMatchId = puuidMatchesArr[-2] #get the match ID from the most recent match that is not the current match, handle this more carefully later
                myRecentData, otherRecentData, recentTeam = fetchChampInfo(mostRecentMatchId, settings.MY_PUUID, puuidMatchesArr[0]) #get the champs you and the other player were playing last time you met
                print(f"Summoner {matchedSummonerName} is a duplicate! You most recently played on {mostRecentMatchTime} in match {mostRecentMatchId}.\nYou were playing {myRecentData[0]} {myRecentData[1]} ({myRecentData[2]:.2f} KDA), and {matchedSummonerName} was playing {otherRecentData[0]} {otherRecentData[1]} ({otherRecentData[2]:.2f} KDA)!")
                if recentTeam is True:
                    print(f"You were on the same team, and the game resulted in a {myRecentData[3]}.")
                else:
                    print(f"You were on opposing teams, and the game resulted in a {myRecentData[3]} for you and a {otherRecentData[3]} for {matchedSummonerName}.")
            if len(puuidMatches) <= 1 and firstRun == 0: #change this later lol
                print("No duplicates found in recent match.")
                firstRun = 1                    
    con.commit() #commit any changes to db at the end
    cursor.close() #close connection to db at the end

if __name__ == '__main__':
    main()