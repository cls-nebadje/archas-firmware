'''
Created on Oct 30, 2013

@author: uli
'''

import re, datetime, os, commands
import archas

# Detect sensors on LAN:
#
#     digitemp_DS9097 -w -s /dev/ttyS0
#
# Read all sensors listed in config file
#
#     digitemp_DS9097 -q -c <config> -a

_DIGITEMP_CONFIG_TEMPLATE = \
"""#
# Archas digitemp configuration template
# 
# Make sure you set the SENSORS variable precisely to the
# number of ROMs below or you'll get a segmentation fault.
# 
# Don't change the log format as it will be parsed by software
# and expects it like that.
#
TTY /dev/ttyS0
READ_TIME 1000
LOG_TYPE 1
LOG_FORMAT "%Y %b %d %H:%M:%S Sensor %s C: %.2C"
CNT_FORMAT "%Y %b %d %H:%M:%S Sensor %s #%n %C"
HUM_FORMAT "%Y %b %d %H:%M:%S Sensor %s C: %.2C H: %h%%"

SENSORS 3

# SERIAL PORT SENSOR
ROM 0 0x10 0x28 0xAD 0xAB 0x02 0x08 0x00 0x37
# OUTDOOR
ROM 1 0x10 0x2E 0x7D 0xB5 0x02 0x08 0x00 0xF6
# CELLAR
ROM 2 0x10 0x56 0x4F 0xB5 0x02 0x08 0x00 0xC8

"""

DIGITEMPCMD = "/usr/bin/digitemp_DS9097"
        
#Oct 28 23:59:39 Sensor 0 C: 21.75
DIGITEMP_REGEX = re.compile(r"([0-9]+\s[a-zA-Z]+\s[0-9]+\s[0-9]+:[0-9]+:[0-9]+) Sensor\s([0-9]+)\sC:\s([-0-9]+\.*[0-9]*)")

def parseLogLine(line):
    m = DIGITEMP_REGEX.search(line)
    if m != None:
        date = m.group(1)
        sens = int(m.group(2))
        temp = float(m.group(3))
        t = datetime.datetime.strptime(date, '%Y %b %d %H:%M:%S')
        return (t, sens, temp)
    return None

def parseSensorNames(sensorNamesStr):
    try:
        sensorNames = {}
        for entry in sensorNamesStr.split(","):
            sid, sname = entry.split(":")
            sensorNames[int(sid)] = sname
    except Exception as e:
        archas.logError("Failed to parse sensor names string: %s" % str(e))
        return {}
    return sensorNames

def measure(configFile, logFile, sensorNames, triggers=None, digitempCommand=DIGITEMPCMD):

    archas.logDebug("Measuring temperature, writing results to '%s'..." % logFile)

    if archas.createFileIfNotThere(configFile, _DIGITEMP_CONFIG_TEMPLATE):
        archas.logWarning("Digitemp config file not available. Created template at %s" % configFile)
    
    s, o = commands.getstatusoutput("%s -q -c %s -a" % (digitempCommand, configFile))
    if not os.WIFEXITED(s) or os.WEXITSTATUS(s) != 0:
        archas.logError("Digitemp failed with: %s (%i)" %(o, s))
        archas.logInfo(("Perhaps you are not in the 'dialout' group "
                        "or used the digitemp command for the wrong "
                        "serial controller"))
        return None
    
    archas.logDebug(o)
    
    with open(logFile, "a") as myfile:
        myfile.write(o)
        myfile.write("\n")
    
    sensors = {}
    
    for l in o.splitlines():
        v = parseLogLine(l)
        if v is not None:
            (date, sensor, temp) = v
            sensors[sensor] = (date, temp)
            if triggers is not None:
                # TODO: Process triggers use sensorNames in messages
                pass            
    
    return sensors

def parseSensorState(tState):
    try:
        sensors = {}
        for entry in tState.split("|"):
            if len(entry) == 0:
                return {}
            sid, sdate, stemp = entry.split("$")
            try:
                sdate = datetime.datetime.strptime(sdate, "%Y-%m-%d %H:%M:%S.%f")
            except:
                sdate = datetime.datetime.strptime(sdate, "%Y-%m-%d %H:%M:%S")
            sensors[int(sid)] = (sdate, float(stemp))
    except Exception as e:
        archas.logError("Failed to parse sensor state string '%s': %s" % (tState, str(e)))
        return {}
    return sensors

def createSensorState(sensors):
    state = []
    for sid, (sdate, stemp) in sensors.items():
        state.append(u"%i$%s$%f" % (sid, str(sdate), stemp))
    return u"|".join(state)
