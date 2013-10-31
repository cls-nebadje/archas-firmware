'''
Created on Oct 30, 2013

@author: uli
'''

import datetime
import archas
from digitemp import parseLogLine

PLOT_START_NOW          = datetime.datetime.now()
PLOT_RANGE_TWO_DAYS     = datetime.timedelta(hours=24*2)
FIGURE_SIZE_A4          = (11.69,8.27)

def makePlot(sensors,
             sensorNames,
             pdfOutPath=None,
             pngOutPath=None,
             figureSize=FIGURE_SIZE_A4,
             pngDpi=100):
    import matplotlib
    matplotlib.use('Agg')
    import pylab
    
    f = pylab.figure(figsize=FIGURE_SIZE_A4)
    ax = f.gca()

    df = pylab.DateFormatter('%d.%m.%Y')
    dl = matplotlib.dates.DayLocator(range(1,32))
    ax.xaxis.set_major_locator(dl)
    ax.xaxis.set_major_formatter(df)

    hf = pylab.DateFormatter('%H:%M')
    hl = matplotlib.dates.HourLocator([0, 3, 6, 9, 12, 15, 18, 21])    
    ax.xaxis.set_minor_locator(hl)
    ax.xaxis.set_minor_formatter(hf)
    
    ax.xaxis.set_tick_params(which='major', pad=18)
    ax.tick_params(axis='x', which='minor', labelsize=10)
    
    ml = matplotlib.ticker.MultipleLocator(2)
    ax.yaxis.set_major_locator(ml)
    ml = matplotlib.ticker.MultipleLocator(1)
    ax.yaxis.set_minor_locator(ml)
    
    ax.set_ylabel(u"\u00B0C", rotation=0)
    
    for sensor, data in sensors.items():
        if sensor not in sensorNames:
            sensorNames[sensor] = "Sensor %i" % sensor
        x, y = zip(*data)
        ax.plot(x, y, label=sensorNames[sensor])
    
    ax.legend(loc='best', prop={'size':10})
    
    f.text(0.5, 0.93, 'Archas Temperatures', horizontalalignment='center')
    
    ax.xaxis_date()
    ax.autoscale_view()

    ax.grid(True)
    
    if pngOutPath is not None:
        f.savefig(pngOutPath, dpi=pngDpi)
    if pdfOutPath is not None:
        f.savefig(pdfOutPath)

def graph(logFile,
          sensorNames,
          pdfPath = None,
          pngPath = None,
          plotStartDate=PLOT_START_NOW,
          plotRange=PLOT_RANGE_TWO_DAYS):
    
    plotStopDate = plotStartDate - plotRange
    
    nfo = (str(plotStopDate),
           str(plotStartDate),
           logFile,
           pdfPath,
           pngPath)
    archas.logInfo("Generating graph from %s to %s: %s -> {%s, %s}" % nfo)
    
    log = open(logFile)    
    sensors = {}
    for l in archas.xreverse(log):
        v = parseLogLine(l)
        if v is not None:
            (t, sens, temp) = v
            if t > plotStartDate:
                continue
            if t <= plotStopDate:
                break
            if sensors.get(sens, None) == None:
                sensors[sens] = []
            sensors[sens].append((t, temp))
    log.close()
    
    makePlot(sensors,
             sensorNames,
             pdfOutPath = pdfPath,
             pngOutPath = pngPath
             )


