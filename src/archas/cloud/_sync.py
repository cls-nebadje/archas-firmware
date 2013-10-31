'''
Created on Oct 30, 2013

@author: uli
'''
import archas, os, subprocess

def sync(path):
    archas.logDebug("Synchronizing '%s'..." % path)
    
    p = subprocess.Popen(["./grive",],
                         cwd=path,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode < 0:
        archas.logError("Synchronizing has been terminated by signal %i" % -p.returncode)
        return False
    if p.returncode > 0:
        archas.logError("Synchronizing failed with %s %s (%i)" %(out, err, p.returncode))
        return False
    
    archas.logDebug("Synchronizing: %s\n%s" % (out, err))
    return True
