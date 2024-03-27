from Search import searchByChart, searchByPlayer, searchAllPlayers, searchAllClears
from Core import Utils
from time import perf_counter
import tkinter as tk
'''
searchByChart(chartId, chartsJsonPath, passesJsonPath, useSaved) 
    -> list

\/ \/ \/ \/ \/ \/

return validPasses 
-> [id, xacc, name, score, vidLink, datetime, is12k, noHolds, isFirst]

======================================================================

searchByName(name, chartsJsonPath, passesJsonPath, useSaved)
    -> dict

\/ \/ \/ \/ \/ \/

return {"rankedScore":rankedScore (float),
           "generalScore": general (float),
           "totalPasses": len(validScores) (int),
           "universalPasses": uPasses (int),
           "topDiff": topDiff (str),
           "allScores": validScores}

validScores : dict
List of all scores excluding duplicates in following format (might be changed to dict soon)
{chartId, isWorldsFirst, Xacc, chart, creator, pguDiff, scoreV2}
           
chartsJsonPath : str 
Path to the desired .json location of saved charts
If the path doesnt exist a fresh copy of charts will be pulled from the api and saved to the location
If the reading failed it will count as not existing and overwrite it with new copy

passesJsonPath : str
Same as chartsJsonPath but for passes

useSaved : boolean
Flag for whether you want to use saved both charts and passes or get a new copy from the api
Will overwrite existing files
'''

util = Utils()
clearOptions = util.allClearSortPriority
playerOptions = util.allPassSortPriority
def printList(l: dict):
    if not l:
        print("Nothing in the list!")
        return
    print("\n")
    if type(l) is dict:
        for item in l.items():
            if item[0] == "allScores":
                for chart in item[1]:
                    print(chart)
            else:
                print(item)
    else:
        for item in l:
            print(item)
    del l

def getInt(s):
    if s:
        return int(s)
    return 1


if __name__ == "__main__":
    win = tk.Tk()
    win.title('Text Editor')
    win.geometry('200x400')

    prompt = tk.Entry(win, width=40)
    minScore = tk.Entry(win, width=40)

    TwvKeyMode = tk.IntVar()
    check12k = tk.Checkbutton(win, text='12K passes only', variable=TwvKeyMode)

    reverseMode = tk.IntVar()
    reverse = tk.Checkbutton(win, text='Reverse sort order /\n Display cleared charts for plr', variable=reverseMode)

    updateSaved = tk.IntVar()
    update = tk.Checkbutton(win, text='Update from API', variable=updateSaved)

    sortByPlr = tk.StringVar()
    sortByPlr.set("rankedScore")
    sortPlrDrop = tk.OptionMenu(win, sortByPlr, *playerOptions)

    sortByClr = tk.StringVar()
    sortByClr.set("score")
    sortClrDrop = tk.OptionMenu(win, sortByClr, *clearOptions)

    searchChart = tk.Button(win, text='Search by chart id', command=lambda: printList(searchByChart(getInt(prompt.get()),
                                                                                                    useSaved=not updateSaved.get()
                                                                                                    )))
    searchPlr = tk.Button(win, text='Search by player', command=lambda: printList(searchByPlayer(prompt.get(),
                                                                                                 TwvKOnly=TwvKeyMode.get(),
                                                                                                 showCharts=reverseMode.get(),
                                                                                                 useSaved=not updateSaved.get()
                                                                                                 )))
    searchAllPlr = tk.Button(win, text='Search all players', command=lambda: printList(searchAllPlayers(sortBy=sortByPlr.get(),
                                                                                                        TwvKOnly=TwvKeyMode.get(),
                                                                                                        disableCharts=True,
                                                                                                        reverse=reverseMode.get(),
                                                                                                        useSaved=not updateSaved.get()
                                                                                                        )))
    searchAllClr = tk.Button(win, text='Search all charts', command=lambda: printList(searchAllClears(sortBy=sortByClr.get(),
                                                                                                      TwvKOnly=TwvKeyMode.get(),
                                                                                                      minScore=getInt(minScore.get()),
                                                                                                      reverse=reverseMode.get(),
                                                                                                      useSaved=not updateSaved.get()
                                                                                                      )))


    tk.Label(win, text="Chart ID / Player's nickname").pack()
    prompt.pack(fill=tk.NONE, side=tk.TOP)

    tk.Label(win, text="Minimal Score").pack()
    minScore.pack(fill=tk.NONE, side=tk.TOP)

    searchChart.pack(expand=tk.FALSE, fill=tk.X, side=tk.TOP)
    searchPlr.pack(expand=tk.FALSE, fill=tk.X, side=tk.TOP)
    searchAllPlr.pack(expand=tk.FALSE, fill=tk.X, side=tk.TOP)
    searchAllClr.pack(expand=tk.FALSE, fill=tk.X, side=tk.TOP)

    tk.Label(win, text="Sort by for All Player search").pack()
    sortPlrDrop.pack()
    tk.Label(win, text="Sort by for All Clear search").pack()
    sortClrDrop.pack()

    check12k.pack()
    reverse.pack()
    update.pack()





    win.mainloop()
