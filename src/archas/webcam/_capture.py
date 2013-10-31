
'''
Created on Oct 30, 2013

@author: uli
'''

import archas, os, subprocess, tempfile, re

_FS_WEBCAM_CONFIG_TEMPLATE = \
"""#
# Archas fswebcam configuration template, adjust to your needs.
#
# Archas firmware does a search/replace on the following strings
#
#     __TEMP__  Gets replaced with the current temperature
#     __PATH__  Gets replaced with the picture output path
#
# To list all available controls of your video device issue:
#
#     fswebcam -d /dev/video0 --list-controls
#
# subsequently the parameters can be set like this:
#
#     set Saturation=50%
#

device /dev/video0
input 0

# When skipping the first frames
#  * The MJPEG palette becomes available suddenly
#  * The picture quality and lighting gets much better
# usually this is because of the automatic exposure adjustment
# of the camera which is iterative.
skip 60

resolution 640x480
palette MJPEG

font /usr/share/fonts/truetype/msttcorefonts/arial.ttf

title "7554 Sent, Grisons, Switzerland, __TEMP__"
timestamp "%d-%m-%Y %H:%M:%S (%Z)"

jpeg 85
save __PATH__

verbose

"""

def capture(configFile, outputPaths, temperature):
    archas.logDebug("Capturing to '%s'..." % str(outputPaths))

    if archas.createFileIfNotThere(configFile, _FS_WEBCAM_CONFIG_TEMPLATE):
        archas.logWarning("Fswebcam config file not available. Created template at %s" % configFile)
    
    picFile = tempfile.NamedTemporaryFile()
    
    with open(configFile, 'r') as f:
        content = f.read().decode("utf-8")
    
    content = content.replace("__TEMP__", temperature)
    content = content.replace("__PATH__", picFile.name)

    confFile = tempfile.NamedTemporaryFile()
    confFile.write(content.encode("utf-8"))
    confFile.flush()
        
    p = subprocess.Popen(["fswebcam", "-c", confFile.name,],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode < 0:
        archas.logError("Capture has been terminated by signal %i" % -p.returncode)
        return False
    if p.returncode > 0:
        archas.logError("Capture failed with %s %s (%i)" %(out, err, p.returncode))
        return False
    
    archas.logDebug("%s %s" % (out, err))
    
    picFile.seek(0, os.SEEK_END)
    picBytes = picFile.tell()
    if picBytes < 100:
        archas.logError("Capture failed without returning error code. But output image has no (%i bytes) of data.")
        return False
    
    for out in outputPaths:
        import shutil
        shutil.copy(picFile.name, out)
    
    return True
