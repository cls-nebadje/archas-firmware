'''
Created on Oct 31, 2013

@author: uli
'''

import archas, os, tempfile, subprocess, shlex

def _getTimeLapseFiles(lapseDir, startTimeS, rangeBackS):
    stopTimeS = startTimeS - rangeBackS
    files = []
    for filename in os.listdir (lapseDir):
        if filename.lower().endswith(".jpg"):
            filePath = os.path.join(lapseDir, filename)
            st = os.stat(filePath)
            if st.st_size == 0:
                archas.logError("Deleting empty file: %s" % filename)
                os.remove(filePath)
                continue
            if st.st_ctime > startTimeS and st.st_ctime < stopTimeS:
                continue
            files.append(filePath)
    return files

_TIME_LAPSE_ENCODER_CMD = ("mencoder mf://@%s "
                           "-mf w=640:h=480:fps=10:type=jpg "
                           "-ovc x264 "
                           "-x264encopts pass=1:bitrate=8000:crf=20 "
                           "-nosound "
                           "-lavfopts format=mp4 "
                           "-o %s")

def timeLapseRender(videoOutPath,
                    lapseDir,
                    startTimeS,
                    rangeBackS,
                    deleteFilesAfterRendering=False):
    
    files = _getTimeLapseFiles(lapseDir, startTimeS, rangeBackS)
    
    fileListFile = tempfile.NamedTemporaryFile()
    for f in files:
        fileListFile.write("%s\n" % f)
    
    cmd = _TIME_LAPSE_ENCODER_CMD % (fileListFile.name, videoOutPath)
    archas.logDebug("Rendering time lapse from files in '%s' to '%s'..." % (fileListFile.name, videoOutPath))
    archas.logDebug("Render command: %s" % cmd)
    
    ok = False    
    
    # TODO: Render
    if 0:
        p = subprocess.Popen(shlex.split(cmd),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode < 0:
            archas.logError("Time lapse rendering has been terminated by signal %i" % -p.returncode)
        elif p.returncode > 0:
            archas.logError("Time lapse rendering failed with %s %s (%i)" %(out, err, p.returncode))
        else:
            archas.logDebug("Time lapse rendering: %s\n%s" % (out, err))
            ok = True
    
    if ok and deleteFilesAfterRendering:
        for f in files:
            os.remove(f)
    
    return ok
