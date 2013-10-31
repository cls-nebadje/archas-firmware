'''
Created on Oct 30, 2013

@author: uli
'''

import archas, os, time

CONFIG_DIR             = os.path.expanduser("~/.archas")
_CONFIG_FILE            = os.path.join(CONFIG_DIR, "archas.conf")
_STATUS_FILE            = os.path.join(CONFIG_DIR, "archas.stat")

def createDirsIfNecessary():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

CONF_KEY_DIGTEMP_CONF    = "digitemp.config.file"
CONF_DEF_DIGTEMP_CONF    = u"digitemp.conf"

CONF_KEY_DIGTEMP_LOG    = "digitemp.log.file"
CONF_DEF_DIGTEMP_LOG    = u"archas-temp.log"

CONF_KEY_SENSOR_NAMES   = "digitemp.sensor.names"
CONF_DEF_SENSOR_NAMES   = u""

CONF_KEY_RUN_INTERVAL_S_TEMP_MEASURE = "run.interval.temp.measure"
CONF_DEF_RUN_INTERVAL_S_TEMP_MEASURE = 60.0 * 2 - 5

CONF_KEY_RUN_INTERVAL_S_TEMP_GRAPH = "run.interval.temp.graph"
CONF_DEF_RUN_INTERVAL_S_TEMP_GRAPH = 60.0 * 5 - 5

CONF_KEY_TEMP_GRAPH_PDF_FILE = "temp.graph.pdf.file"
CONF_DEF_TEMP_GRAPH_PDF_FILE = u"archas-temp-graph.pdf"

CONF_KEY_TEMP_GRAPH_PNG_FILE = "temp.graph.png.file"
CONF_DEF_TEMP_GRAPH_PNG_FILE = u""

CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE        = "run.interval.webcam.capture"
CONF_DEF_RUN_INTERVAL_S_WCAM_CAPTURE        = 60.0 * 5 - 5
CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE_CLOUD  = "run.interval.webcam.capture.cloud"
CONF_DEF_RUN_INTERVAL_S_WCAM_CAPTURE_CLOUD  = 60.0 * 5 - 5
CONF_KEY_WCAM_CONF                          = "webcam.config.file"
CONF_DEF_WCAM_CONF                          = u"fswebcam.conf"
CONF_KEY_WCAM_TEMP_ID                       = "webcam.temperature.sensor.id"
CONF_DEF_WCAM_TEMP_ID                       = 1
CONF_KEY_WCAM_CLOUD_FILE                    = "webcam.cloud.file"
CONF_DEF_WCAM_CLOUD_FILE                    = u"archas-webcam.jpg"
CONF_KEY_WCAM_LAPSE_DIR                     = u"webcam.timelapse.dir"
CONF_DEF_WCAM_LAPSE_DIR                     = u"timelapse"

CONF_KEY_CLOUD_SYNC_FOLDER = "cloud.sync.folder"
CONF_DEF_CLOUD_SYNC_FOLDER = u"~/gdrive"

_CONFIG_LIST = {CONF_KEY_DIGTEMP_CONF                : CONF_DEF_DIGTEMP_CONF,
                CONF_KEY_DIGTEMP_LOG                 : CONF_DEF_DIGTEMP_LOG,
                CONF_KEY_SENSOR_NAMES                : CONF_DEF_SENSOR_NAMES,
                CONF_KEY_RUN_INTERVAL_S_TEMP_MEASURE : CONF_DEF_RUN_INTERVAL_S_TEMP_MEASURE,
                
                CONF_KEY_RUN_INTERVAL_S_TEMP_GRAPH   : CONF_DEF_RUN_INTERVAL_S_TEMP_GRAPH,
                CONF_KEY_TEMP_GRAPH_PDF_FILE         : CONF_DEF_TEMP_GRAPH_PDF_FILE,
                CONF_KEY_TEMP_GRAPH_PNG_FILE         : CONF_DEF_TEMP_GRAPH_PNG_FILE,
                
                CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE : CONF_DEF_RUN_INTERVAL_S_WCAM_CAPTURE,
                CONF_KEY_RUN_INTERVAL_S_WCAM_CAPTURE_CLOUD : CONF_DEF_RUN_INTERVAL_S_WCAM_CAPTURE_CLOUD,
                CONF_KEY_WCAM_CONF                   : CONF_DEF_WCAM_CONF,
                CONF_KEY_WCAM_TEMP_ID                : CONF_DEF_WCAM_TEMP_ID,
                CONF_KEY_WCAM_CLOUD_FILE             : CONF_DEF_WCAM_CLOUD_FILE,
                CONF_KEY_WCAM_LAPSE_DIR              : CONF_DEF_WCAM_LAPSE_DIR,
                
                CONF_KEY_CLOUD_SYNC_FOLDER           : CONF_DEF_CLOUD_SYNC_FOLDER,
                }

class Config(archas.ConfigurationManager):
    def __init__(self):
        createDirsIfNecessary()
        archas.ConfigurationManager.__init__(self,
                                             _CONFIG_FILE,
                                             _CONFIG_LIST)
    def getSensorNames(self):
        sns = self.get(CONF_KEY_SENSOR_NAMES)
        return archas.temperature.digitemp.parseSensorNames(sns)

STAT_KEY_LAST_RUN       = "last.run"
STAT_DEF_LAST_RUN       = u""

STAT_KEY_CURRENT_SENSOR_STATE       = "current.sensor.state"
STAT_DEF_CURRENT_SENSOR_STATE       = u""

_STATUS_LIST = {STAT_KEY_LAST_RUN             : STAT_DEF_LAST_RUN,
                STAT_KEY_CURRENT_SENSOR_STATE : STAT_DEF_CURRENT_SENSOR_STATE,
                }

class Status(archas.ConfigurationManager):
    def __init__(self, cfg):
        self.cfg = cfg
        createDirsIfNecessary()
        archas.ConfigurationManager.__init__(self,
                                             _STATUS_FILE,
                                             _STATUS_LIST)
        
    def _parseLastRun(self, lrs):
        entries = {}
        for entry in lrs.split(","):
            if len(entry) == 0:
                return {}
            k, s = entry.split(":")
            entries[k] = float(s)
        return entries
    
    def _getLastRun(self, key):
        lrs = self.get(STAT_KEY_LAST_RUN)
        return self._parseLastRun(lrs).get(key, 0.0)
    
    def _setLastRun(self, key, secs):
        lrs = self.get(STAT_KEY_LAST_RUN)
        entries = self._parseLastRun(lrs)
        entries[key] = secs
        lrs = []
        for k, s in entries.items():
            lrs.append("%s:%f" % (k, s))
        self.set(STAT_KEY_LAST_RUN, u",".join(lrs), sync=True)
            
    def updateLastRun(self, key):
        self._setLastRun(key, time.time())

    def isDue(self, key, update=True):
        tDelta = time.time() - self._getLastRun(key)
        tMin = self.cfg.get(key)
        archas.logDebug("%s: %.2f, current delta: %.2f" % (key, tMin, tDelta))
        due = tDelta >= tMin
        if due and update:
            self.updateLastRun(key)
        return due

    def getCurrentSensorState(self):
        state = self.get(STAT_KEY_CURRENT_SENSOR_STATE)
        return archas.temperature.digitemp.parseSensorState(state)

    def setCurrentSensorState(self, sensors):
        state = archas.temperature.digitemp.createSensorState(sensors)
        self.set(STAT_KEY_CURRENT_SENSOR_STATE, state, sync=True)
    
        