import sqlite3
import time
from api_funcs import fetchSummoners

def createTables(): #create the 4 tables if they don't all already exist
    con = sqlite3.connect("runback.db")
    cursor = con.cursor()
    #print(len(cursor.execute("SELECT name FROM sqlite_master").fetchall()))
    if len(cursor.execute("SELECT name FROM sqlite_master").fetchall()) != 7:
        cursor.execute("DROP TABLE IF EXISTS summoners")
        cursor.execute("DROP TABLE IF EXISTS host")
        cursor.execute("DROP TABLE IF EXISTS exclude")
        cursor.execute("DROP TABLE IF EXISTS matchIds")
        cursor.execute("CREATE TABLE summoners(puuid, matchId, queueId, matchDTC, rowGUID, UNIQUE(rowGUID))")
        cursor.execute("CREATE TABLE host(summoner, puuid)")
        cursor.execute("CREATE TABLE exclude(summoner, puuid, UNIQUE(puuid))")
        cursor.execute("CREATE TABLE matchIds(matchId, UNIQUE(matchId))")
    cursor.close()

def saveHost(gameName, tagLine, puuid, cursor): #save the information of the person running to the db
    summonerName = f"{gameName}#{tagLine}"
    summonerPuuid = f"{puuid}"
    summoner_host = [(summonerName, summonerPuuid)]
    cursor.executemany("INSERT INTO host VALUES(?,?)", summoner_host)
    cursor.executemany("INSERT OR IGNORE INTO exclude VALUES(?,?)", summoner_host)


def saveMatchId(matchIds, cursor): #save each matchId to the matchIds table
    i=0
    while i < len(matchIds):
        cursor.executemany("INSERT OR IGNORE INTO matchIds VALUES(?)", [(matchIds[i],)])
        i=i+1

def saveSummoner(summonerData, cursor): #save the summonerData to the summoners table
    cursor.executemany("INSERT OR IGNORE INTO summoners VALUES(?,?,?,?,?)", summonerData)

def saveExclusion(exclusions, cursor): #save the exclusions to the exclusions table, coming back to this later...
    cursor.executemany("INSERT OR IGNORE INTO exclude VALUES(?,?)", exclusions)

def retrieveMatchIds(cursor): #retrieve all entries from the matchIds table as a list
    getMatches = cursor.execute("SELECT matchId FROM matchIds")
    matchIdsRaw = getMatches.fetchall()
    matchIds = []
    for matchId in matchIdsRaw: #each tuple in the list
        for match in matchId: #each matchId in each tuple
            matchIds.append(match)
    return matchIds #get a list back at the end

def saveNewMatchIds(matchIdsDB, matchIdsAPI, cursor):
    x=0
    for x in range(len(matchIdsAPI)):
        if matchIdsAPI[x] not in matchIdsDB:
            cursor.execute("INSERT OR IGNORE INTO matchIds VALUES(?)", (matchIdsAPI[x],)) #insert missing match id
            summonerData = fetchSummoners(matchIdsAPI[x]) #get summoner info from this match id
            time.sleep(1.5) #to get around API limit
            saveSummoner(summonerData, cursor)
