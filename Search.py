from Core import *
import os, sys
from io import StringIO
from datetime import datetime
from time import perf_counter

chartPathDef = "charts.json"
passPathDef = "passes.json"
playerPathDef = "player.json"
useSavedDef = 1

def initData(chartPath, passPath, playerPath, useSaved):
    if chartPath and passPath and playerPath and useSaved:
        if os.path.exists(chartPath) and os.path.exists(passPath) and os.path.exists(playerPath):
            print("using saved...")
            return DataScraper(chartPath, passPath, playerPath)
        else:
            return DataScraper(chartPathDef, passPathDef, playerPathDef, True)
    else:
        return DataScraper(chartPathDef, passPathDef, playerPathDef, True)


def searchByChart(chartId: int, chartPath=chartPathDef, passPath=passPathDef, playerPath=playerPathDef, useSaved=useSavedDef, data=None, getAll=False) \
        -> (list, list):
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, playerPath, useSaved)

    idOffset = 0
    initChartId = chartId
    if chartId >= data.chartsCount:
        chartId = data.chartsCount-1
    chart = data.charts[chartId-idOffset]
    while chart["id"] > chartId:
        idOffset += 1
        chart = data.charts[chartId-idOffset]
    validPasses = [Pass for Pass in data.passes
                   if Pass["levelId"] == initChartId]
    if not validPasses:
        return []
    scores = []
    for Pass in validPasses:
        try:
            date = datetime.strptime(Pass["vidUploadTime"].split("Z")[0], "%Y-%m-%dT%H:%M:%S")
        except:
            date = datetime.today()
        scores.append({"diff": chart["diff"],
                            "id": Pass["id"],
                            "chartId": chart["id"],
                            "song": chart["song"],
                            "Xacc": util.getXacc(Pass["judgements"]),
                            "player": Pass["player"],
                            "score": util.getScoreV2(Pass, chart),
                            "vidLink": Pass["vidLink"],
                            "date": date,
                            "WFPass": False,
                            "is12K": Pass["is12K"],
                            "isNoHold": Pass["isNoHoldTap"]
                       })
    scores = list(reversed(sorted(scores, key=lambda x: (x["score"]))))
    datedScores = sorted(scores, key=lambda x: (x["date"]))
    datedScores[0]["WFPass"] = True
    if getAll:
        return datedScores
    usedNames = []
    validScores = []
    for score in scores:
        if score["player"] not in usedNames:
            validScores.append(score)
            usedNames.append(score['player'])


    return validScores







def searchByPlayer(playerName: str, chartPath=chartPathDef , passPath=passPathDef, playerPath=playerPathDef, useSaved=useSavedDef, data=None, TwvKOnly=False, showCharts=True) \
        -> dict:
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, playerPath, useSaved)

    if playerName not in data.players.keys():
        print("Player not found!")
        return {}
    if data.players[playerName]["isBanned"]:
        print("Player is banned!")
        return {}

    playerPasses = []
    for Pass in data.passes:
        if Pass["player"] == playerName:
            playerPasses.append(Pass)

    scores = []
    uPasses = 0
    firstPasses = 0
    XaccList = []
    topDiff = ["P", 1]
    top12kDiff = ["P", 1]
    for Pass in playerPasses:
        chartId = Pass["levelId"]
        prevIdTemp = -9999
        prevId = -9999
        if not chartId:
            continue
        chartPos = chartId
        idOffset = 0
        if chartId >= data.chartsCount:
            chart = data.charts[-1]
            chartPos = data.chartsCount - 1
        else:
            chart = data.charts[chartPos + idOffset]
        badFlag = False
        while 1:
            if chart["id"] == prevId:
                badFlag = True
                break
            if chart["id"] == chartId:
                break
            elif chart["id"] < chartId:
                idOffset += 1
            else:
                idOffset -= 1
            prevId = prevIdTemp
            prevIdTemp = chart["id"]
            chart = data.charts[chartPos + idOffset]
        if badFlag:
            continue
        isWorldsFirst = checkWorldsFirst(Pass, data)
        if isWorldsFirst:
            firstPasses += 1
        try:
            date = datetime.strptime(Pass["vidUploadTime"].split("Z")[0], "%Y-%m-%dT%H:%M:%S")
        except:
            date = datetime.today()
        scores.append({
                        "chartId": chart["id"],
                        "score": util.getScoreV2(Pass, chart),
                        "Xacc": util.getXacc(Pass["judgements"]),
                        "song": chart['song'],
                        "diff":chart["pguDiff"],
                        "creator":chart['creator'],
                        "date":date,
                        "isWorldsFirst": isWorldsFirst,
                        "is12K":Pass['is12K'],
                        "pdnDiff":chart["pdnDiff"],
                        "vidLink":Pass["vidLink"],
                        })
        try:
            pgu = chart["pguDiff"][0]
            num = int(chart["pguDiff"][1:])
            if data.pguSort[topDiff[0]] < data.pguSort[pgu]:
                topDiff[0] = pgu
                topDiff[1] = num
                if Pass["is12K"]:
                    top12kDiff = topDiff.copy()
            if data.pguSort[topDiff[0]] == data.pguSort[pgu] and int(topDiff[1]) < num:
                topDiff[1] = num
                if Pass["is12K"]:
                    top12kDiff = topDiff.copy()
        except:
            pass

    scores = list(reversed(sorted(scores, key=lambda x: x["score"])))
    usedIds = []
    validScores = []
    for score in scores:
        if score["chartId"] not in usedIds and (not TwvKOnly or score["is12K"]):
            validScores.append(score)
            if score["diff"][0] == "U":
                uPasses += 1
            usedIds.append(score["chartId"])
            XaccList.append(score["Xacc"])

    rankedScore = util.getRankedScore([score["score"] for score in validScores])
    general = util.getGeneralScore([score["score"] for score in validScores])
    topDiff = topDiff[0]+str(topDiff[1])
    top12kDiff = top12kDiff[0]+str(top12kDiff[1])

    scoresNew = []
    for score in validScores:
        scoresNew.append(score)
    if XaccList:
        avgAcc = sum(XaccList)/len(XaccList)
    else:
        avgAcc = 0
    ret = {"player":playerName,
            "rankedScore":rankedScore,
            "generalScore": general,
            "avgXacc": avgAcc,
            "totalPasses": len(validScores),
            "universalPasses": uPasses,
            "WFPasses": firstPasses,
            "topDiff": topDiff,
            "top12kDiff": top12kDiff,
            "country": data.players[playerName]["country"]}
    if showCharts:
        ret.update({"allScores": scoresNew})
    return ret


def checkWorldsFirst(Pass, data):
    passes = searchByChart(Pass["levelId"], data=data, getAll=True)
    for p in passes:
        if p["WFPass"]:
            if p["id"] == Pass["id"]:
                return True
    return False


def searchAllPlayers(chartPath=chartPathDef , passPath=passPathDef, playerPath=playerPathDef, useSaved=useSavedDef, sortBy="rankedScore", data=None, disableCharts=True, TwvKOnly=False, reverse=False):
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, playerPath, useSaved)

    playerNameList = data.players.keys()
    playerLeaderboard = []
    i = 0
    n = len(playerNameList)
    print("Players checked:")
    for player in playerNameList:
        i += 1
        print("\r",round(i / n * 100,3), "%          ", end="", flush=True)
        if data.players[player]["isBanned"]:
            continue
        search = searchByPlayer(player, chartPath, passPath, playerPath,True, data, TwvKOnly)
        if search["avgXacc"]:
            playerLeaderboard.append(search)
            if disableCharts:
                del playerLeaderboard[-1]["allScores"]
    priority = util.allPassSortPriority.copy()
    priority.remove(sortBy)
    sortCriteria = [sortBy] + priority
    if reverse:
        return reversed(sorted(playerLeaderboard, key=lambda x: [x[criteria] for criteria in sortCriteria]))
    return sorted(playerLeaderboard, key=lambda x: [x[criteria] for criteria in sortCriteria])


def searchAllClears(chartPath=chartPathDef , passPath=passPathDef, playerPath=playerPathDef, useSaved=useSavedDef, sortBy="score", data=None, minScore=0, TwvKOnly=False, reverse=False):
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, playerPath, useSaved)

    leaderboard = list(searchAllPlayers(data=data, disableCharts=False))
    clears = []
    i = 0
    n = len(leaderboard)
    print("Players checked:")
    print(leaderboard)
    for player in leaderboard:
        i += 1
        print("\r",round(i / n * 100,3), "%                   ", end="", flush=True)
        if data.players[player['player']]["isBanned"]:
            continue
        allClears = player["allScores"]
        for clear in allClears:
            if clear["score"] >= minScore and (not TwvKOnly or score["is12K"]):
                result = {"player": player["player"]}
                result.update(clear)
                clears.append(result)
    priority = util.allClearSortPriority.copy()
    priority.remove(sortBy)
    sortCriteria = [sortBy] + priority
    if reverse:
        return reversed(sorted(clears, key=lambda x: [x[criteria] for criteria in sortCriteria]))
    return sorted(clears, key=lambda x: [x[criteria] for criteria in sortCriteria])

if __name__ == "__main__":
    st = perf_counter()
    [print(n) for n in searchAllPlayers(TwvKOnly=False, disableCharts=True, useSaved=1)]
    print(perf_counter()-st, " s")