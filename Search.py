from Core import *
import os, sys
from io import StringIO
from datetime import datetime

DEBUG = False
chartPathDef = "charts.json"
passPathDef = "passes.json"
useSavedDef = 1

# redirects all text from printfs to useless IO if not debugging=


def initData(chartPath, passPath, useSaved):
    if chartPath and passPath and useSaved:
        if os.path.exists(chartPath) and os.path.exists(passPath):
            print("using saved...")
            return DataScraper(chartPath, passPath)
        else:
            return DataScraper()
    else:
        return DataScraper()

def searchByChart(chartId: int, chartPath=chartPathDef, passPath=passPathDef, useSaved=useSavedDef, data=None, getAll=False) \
        -> (list, list):
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, useSaved)

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
        # [id, xacc, name, score, vidLink, datetime, isFirst, is12k, noHolds]
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







def searchByPlayer(playerName: str, chartPath=chartPathDef , passPath=passPathDef, useSaved=useSavedDef, data=None, TwvKOnly=False) \
        -> dict:
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, useSaved)

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
                #print(f"bad id, skipping ({chartId})")
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
        if badFlag: continue
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
                        "diff":chart["pguDiff"],
                        "song": chart['song'],
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
    return {"player":playerName,
            "rankedScore":rankedScore,
            "generalScore": general,
            "avgXacc": avgAcc,
            "totalPasses": len(validScores),
            "universalPasses": uPasses,
            "WFPasses": firstPasses,
            "topDiff": topDiff,
            "top12kDiff": top12kDiff,
            "allScores": scoresNew}


def checkWorldsFirst(Pass, data):
    passes = searchByChart(Pass["levelId"], data=data, getAll=True)
    for p in passes:
        if p["WFPass"]:
            #print()
            #print(p)
            #print(Pass)
            if p["id"] == Pass["id"]:
                return True
    return False


def searchAllPlayers(chartPath=chartPathDef , passPath=passPathDef, useSaved=useSavedDef, sortBy="rankedScore", data=None, disableCharts=True, TwvKOnly= False):
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, useSaved)

    playerNameList = []
    for Pass in data.passes:
        if Pass["player"] not in playerNameList:
            playerNameList.append(Pass["player"])
    playerLeaderboard = []
    i = 0
    n = len(playerNameList)
    print("Players checked:")
    for player in playerNameList:
        i += 1
        print("\r",i / n * 100, "%          ", end="", flush=True)
        search = searchByPlayer(player, chartPath, passPath, True, data, TwvKOnly)
        if search["avgXacc"]:
            playerLeaderboard.append(search)
            if disableCharts:
                del playerLeaderboard[-1]["allScores"]
    priority = util.allPassSortPriority.copy()
    priority.remove(sortBy)
    sortCriteria = [sortBy] + priority
    return reversed(sorted(playerLeaderboard, key=lambda x: [x[criteria] for criteria in sortCriteria]))

def searchAllClears(chartPath=chartPathDef , passPath=passPathDef, useSaved=useSavedDef, sortBy="score", data=None, minScore=0, TwvKOnly=False):
    util = Utils()
    directCall = False
    if data is None:
        directCall = True
        data = initData(chartPath, passPath, useSaved)

    leaderboard = list(searchAllPlayers(data=data, disableCharts=False))
    clears = []
    i = 0
    n = len(leaderboard)
    print("Players checked:")
    for player in leaderboard:
        i += 1
        print("\r",i / n * 100, "%                   ", end="", flush=True)
        allClears = player["allScores"]
        for clear in allClears:
            if clear["score"] >= minScore and (not TwvKOnly or score["is12K"]):
                result = {"player": player["player"]}
                result.update(clear)
                clears.append(result)
    priority = util.allClearSortPriority.copy()
    priority.remove(sortBy)
    sortCriteria = [sortBy] + priority
    return reversed(sorted(clears, key=lambda x: [x[criteria] for criteria in sortCriteria]))

if __name__ == "__main__":
    [print(n) for n in searchAllPlayers(TwvKOnly=True, disableCharts=False)]