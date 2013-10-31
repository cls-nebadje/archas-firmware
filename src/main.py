#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 29, 2013

@author: uli
'''

import archas, os, time
from config import Config, Status, \
                   CONFIG_DIR, \
                   CONF_KEY_DIGTEMP_CONF, \
                   CONF_KEY_DIGTEMP_LOG, \
                   CONF_KEY_RUN_INTERVAL_S_TEMP_MEASURE, \
                   CONF_KEY_RUN_INTERVAL_S_TEMP_GRAPH, \
                   CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE, \
                   CONF_KEY_WCAM_CONF, \
                   CONF_KEY_WCAM_TEMP_ID, \
                   CONF_KEY_CLOUD_SYNC_FOLDER, \
                   CONF_KEY_TEMP_GRAPH_PDF_FILE, \
                   CONF_KEY_TEMP_GRAPH_PNG_FILE, \
                   CONF_KEY_WCAM_CLOUD_FILE, \
                   CONF_KEY_WCAM_LAPSE_DIR, \
                   CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE_CLOUD

if __name__ == '__main__':
    
    year = time.strftime("%Y")
    archas.logInfo("Archas Firmware (c) 2013%s cls" % ("-%s" if year != "2013" else ""))
    
    config = Config()
    status = Status(config)
    
    
    tempLogPath = config.get(CONF_KEY_DIGTEMP_LOG)
    tempLogPath = os.path.join(CONFIG_DIR, tempLogPath)
    
    sync = False
    syncFolder = config.get(CONF_KEY_CLOUD_SYNC_FOLDER)
    syncFolder = os.path.expanduser(syncFolder)
    
    tempDue     = status.isDue(CONF_KEY_RUN_INTERVAL_S_TEMP_MEASURE, update=True)
    camLapseDue = status.isDue(CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE, update=True)
    camCloudDue = status.isDue(CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE_CLOUD, update=True)
    graphDue    = status.isDue(CONF_KEY_RUN_INTERVAL_S_TEMP_GRAPH, update=True)
    
    if tempDue:
        confPath = config.get(CONF_KEY_DIGTEMP_CONF)
        confPath = os.path.join(CONFIG_DIR, confPath)
        sensors = archas.temperature.digitemp.measure(confPath,
                                                      tempLogPath,
                                                      config.getSensorNames())
        if sensors is not None:
            status.setCurrentSensorState(sensors)
    
    if camLapseDue or camCloudDue:
        confPath = config.get(CONF_KEY_WCAM_CONF)
        confPath = os.path.join(CONFIG_DIR, confPath)
        
        sid = config.get(CONF_KEY_WCAM_TEMP_ID)
        sensors = status.getCurrentSensorState()
        sname = config.getSensorNames().get(sid, "Sensor %i" % sid)
        if sid not in sensors:
            temperature = "<%s>" % sname
        else:
            temperature = u"%.2f \u00B0C" % sensors[sid][1]
        
        wcSync = False
        outfiles = []
        if camLapseDue:
            lapseDir = config.get(CONF_KEY_WCAM_LAPSE_DIR)
            lapseDir = os.path.join(CONFIG_DIR, lapseDir)
            if not os.path.exists(lapseDir):
                os.makedirs(lapseDir)
            lapseFile = os.path.join(lapseDir, "%i.jpg" % int(time.time()))
            outfiles.append(lapseFile)
        if camCloudDue:
            cloudFile = os.path.join(syncFolder,
                                     config.get(CONF_KEY_WCAM_CLOUD_FILE))
            outfiles.append(cloudFile)
            wcSync = True
        ok = archas.webcam.capture(confPath, outfiles, temperature)
        if ok and wcSync:
            sync = True 
    
    if graphDue:
        pdf = os.path.join(syncFolder,
                           config.get(CONF_KEY_TEMP_GRAPH_PDF_FILE))
        png = config.get(CONF_KEY_TEMP_GRAPH_PNG_FILE)
        archas.temperature.graph(tempLogPath,
                                 config.getSensorNames(),
                                 pdfPath = pdf,
                                 pngPath = None if len(png) is 0 else png
                                 )
        sync = True
    
    if sync:
        archas.cloud.sync(syncFolder)
        
    try:
        lapseDir = config.get(CONF_KEY_WCAM_LAPSE_DIR)
        lapseDir = os.path.join(CONFIG_DIR, lapseDir)
        videoOutPath = ""
        startTimeS = time.time()
        rangeBackS = 2 * 24 * 60 * 60
        ok = archas.webcam.timeLapseRender(videoOutPath,
                                           lapseDir,
                                           startTimeS,
                                           rangeBackS,
                                           deleteFilesAfterRendering=False)
        
        # ATTENTION: WE HAVE TO TAKE CARE THAT WE DON'T RUN SYNC IN PARALLEL ...
        
    except Exception as e:
        archas.logDebug("EXCEPTION: %s" % str(e))
    
    archas.logDebug("Archas Firmware exit.")
