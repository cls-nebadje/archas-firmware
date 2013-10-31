'''
Created on Oct 30, 2013

@author: uli
'''

import os

def createFileIfNotThere(filePath, template=""):
    if not os.path.exists(filePath):
        path, _file = os.path.split(filePath)
        if not os.path.exists(path):
            os.makedirs(path)
        with open(filePath, 'w') as f:
            f.write(template)
        return True
    return False
