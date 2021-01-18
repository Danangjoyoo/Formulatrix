import time, random as rd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class Plotter():
    plotStat = False
    init_t = time.time()
    avgTime = []
    x = []
    limit = 30
    varPack = {
        'y1': [[], 'y1', False],
        'y2': [[], 'y2', False],
        'y3': [[], 'y3', False],
        'y4': [[], 'y4', False],
        'y5': [[], 'y5', False],
        'y6': [[], 'y6', False],
        'y7': [[], 'y7', False],
    }

    @staticmethod
    def run(**hide):
        container, label, showStat = 0, 1, 2
        if 'limit' in hide: Plotter.limit = hide['limit']
        for var in Plotter.varPack:
            if Plotter.varPack[var][label] in hide:
                Plotter.varPack[var][showStat] = hide[Plotter.varPack[var][label]]
        ani = FuncAnimation(plt.gcf(), Plotter.autoUpdate, interval=15)
        plt.show()

    @staticmethod
    def autoUpdate(i):
        t1 = time.time()
        # start to add data =======================

        container, label, showStat = 0, 1, 2
        if len(Plotter.x) >= Plotter.limit:
            Plotter.x.pop(0)
            for var in Plotter.varPack: Plotter.varPack[var][container].pop(0)
        Plotter.x.append(round(time.time() - Plotter.init_t, 2))
        for var in Plotter.varPack: Plotter.varPack[var][container].append(rd.choice(np.arange(10,50)))
        # start to plot
        plt.cla()
        for var in Plotter.varPack:
            if Plotter.varPack[var][showStat]:
                plt.plot(Plotter.x, Plotter.varPack[var][container], linewidth=1, label=Plotter.varPack[var][label])
        plt.legend(loc='upper left')
        
        # end of plotting =======================
        #print("Elapsed:", round(time.time() - t1, 4), "ms")

if __name__ == '__main__':
    Plotter.run(y1=True,y2=True,limit=20)