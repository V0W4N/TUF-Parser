import requests as r, json, math as m

chartLink = "https://be.t21c.kro.kr/levels"
passLink = "https://be.t21c.kro.kr/passes"
chartPath = "charts.json"
passPath = "passes.json"

gmConst = 315
start = 1
end = 50
startDeduc = 10
endDeduc = 50
pwr = 0.7


class Utils:
    def __init__(self):
        self.allPassSortPriority = [
            "rankedScore",
            "generalScore",
            "universalPasses",
            "avgXacc",
            "WFPasses",
            "totalPasses",
            "topDiff",
            "top12kDiff",
            "player"
        ]
        self.allClearSortPriority = [
            "score",
            "Xacc",
            "pdnDiff",
            "date"
        ]

    def getScoreV2Mtp(self, tiles, inputs):
        misses = inputs[0]
        if not misses:
            return 1.1
        tp = (start + end) / 2
        tpDeduc = (startDeduc + endDeduc) / 2
        am = max(0, misses - m.floor(tiles / gmConst))
        if am <= 0:
            return 1
        elif am <= start:
            return 1 - startDeduc / 100
        if am <= tp:
            kOne = m.pow((am-start) / (tp - start), pwr) * (tpDeduc - startDeduc) / 100
            return 1 - startDeduc / 100 - kOne
        elif am <= end:
            kTwo = m.pow((end - am) / (end - tp), pwr) * (endDeduc - tpDeduc) / 100
            return 1 + kTwo - endDeduc / 100
        else:
            return 1 - endDeduc / 100


    def getXacc(self, inp):
        if not all([type(i) == int for i in inp]):
            return 0.95
        return ((inp[3] +
                 (inp[2] + inp[4]) * 0.75 +
                 (inp[1] + inp[5]) * 0.4 +
                 (inp[0] + inp[6]) * 0.2)
                / sum(inp))

    def getXaccMtp(self, inp):
        xacc = self.getXacc(inp)
        if xacc * 100 < 95:
            return 1

        elif xacc * 100 < 99:
            return (xacc * 100 - 94) ** 1.6 / 12.1326 + 0.9176

        elif xacc * 100 < 99.8:
            return (xacc * 100 - 97) ** 1.5484 - 0.9249

        elif xacc * 100 < 100:
            return (xacc * 100 - 99) * 5

        elif xacc * 100 == 100:
            return 6

    def getSpeedMtp(self, SPEED, isDesBus=False):
        if isDesBus:
            if not SPEED or SPEED == 1:
                return 1
            elif SPEED > 1:
                return 2-SPEED
        if SPEED is None or SPEED == 1:
            return 1
        if SPEED < 1:
            return 0
        if SPEED < 1.1:
            return 25 * (SPEED - 1.1) ** 2 + 0.75
        if SPEED < 1.2:
            return 0.75
        if SPEED < 1.25:
            return 50 * (SPEED - 1.2) ** 2 + 0.75
        if SPEED < 1.3:
            return -50 * (SPEED - 1.3) ** 2 + 1
        if SPEED < 1.5:
            return 1
        if SPEED < 1.75:
            return 2 * (SPEED - 1.5) ** 2 + 1
        if SPEED < 2:
            return -2 * (SPEED - 2) ** 2 + 1.25
        return 0

    def getScore(self, passData, chartData):
        speed = passData['speed']
        diff = chartData['pdnDiff']
        inputs = passData['judgements']
        base = chartData['baseScore']
        xaccMtp = self.getXaccMtp(inputs)
        if diff == 64:
            speedMtp = self.getSpeedMtp(speed, True)
            score = max(base * xaccMtp * speedMtp, 1)
        else:
            speedMtp = self.getSpeedMtp(speed)
            score = base * xaccMtp * speedMtp
        return score

    def getScoreV2(self, passData, chartData):
        speed = passData['speed']
        diff = chartData['pdnDiff']
        inputs = passData['judgements']
        scoreOrig = self.getScore(passData, chartData)
        if all([type(i) == int for i in inputs]):
            tilecount = sum(inputs[1:-1])
            mtp = self.getScoreV2Mtp(tilecount, inputs)
        else:
            mtp = 1
        if passData['isNoHoldTap']: mtp *= 0.9
        return scoreOrig * mtp

    def getRankedScore(self, scores, top=20):
        if len(scores) < top:
            top = len(scores)

        rankedScore = 0
        for n in range(top):
            rankedScore += (0.9**n)*scores[n]
        return rankedScore

    def getGeneralScore(self, scores):
        return sum(scores)




class DataScraper:
    def __init__(self, chartPath=None, passPath=None):
        self.charts = None
        self.passes = None
        self.chartsCount, self.passesCount = 0,0
        try:
            self.readCharts(chartPath)
            self.readPasses(passPath)
        except:
            self.getCharts()
            self.getPasses()
        self.pguSort = {"P": 1,
                        "G": 2,
                        "U": 3}

    def readCharts(self, path):
        with open(path, "r") as f:
            file = json.load(f)
            self.charts = file["results"]
            self.chartsCount = file["count"]

    def readPasses(self, path):
        with open(path, "r") as f:
            file = json.load(f)
            self.passes = file["results"]
            self.passesCount = file["count"]

    def getCharts(self):
        res = r.get(chartLink)
        print("got charts")
        self.charts = json.loads(res.content)["results"]
        self.chartsCount = json.loads(res.content)["count"]
        with open(chartPath, "w+") as f:
            json.dump(json.loads(res.content), f)

    def getPasses(self):
        res = r.get(passLink)
        print("got passes")
        self.passes = json.loads(res.content)["results"]
        self.passesCount = json.loads(res.content)["count"]
        with open(passPath, "w+") as f:
            json.dump(json.loads(res.content), f)



