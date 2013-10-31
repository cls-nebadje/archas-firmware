'''
Created on Oct 30, 2013

@author: uli
'''


import threading, os
from ConfigParser import RawConfigParser
import archas

#from WH10Logging import wh10LogWarning, wh10LogError
#from WH10OscTransport import wh10OscMessageArgumentPop

WH10_CONFIG_ERR_NO_ERR       = 0
WH10_CONFIG_ERR_READ_CONFIG  = 1
WH10_CONFIG_ERR_WRITE_CONFIG = 2
WH10_CONFIG_ERR_SET_CONFIG   = 3
WH10_CONFIG_ERR_AUTH         = 4

def wh10ConfigCreateEmptyIfNotAvailable(path, sections=["default"]):
    """Creates an empty config file if it doesn't exist and creates given
    sections.
    """
    if not os.path.exists(path):
        fp = open(path, "w")
        for section in sections:
            strg = "[%s]\n\n" % section
            fp.write(strg.encode("utf-8"))
        fp.close()

class WH10ConfigManagerItem:
    def __init__(self, default):
        self.value = default
        self.changed = False
        self.default = default
        
class ConfigurationManager:
    """
    Assumes that the configuration file is not modified while the config
    manager will access the file as we currently don't mark local
    modifications.
    
    Note: The configChangeHandler can be called from a different thread!
    
    TODO: * Add/Remove configuration items
          * Optional configuration sections for configuration items
    """
    def __init__(self, configFile, configList, configSection='default'):
        self.configFile = configFile
        self.configSection = configSection
        self.configChangeHandler=None
        self.oscPassArgKey="admin_pass"
        self.oscReturnValKey="return_value"
        self.oscReturnStrKey="return_str"
        self.lock = threading.Lock()
        # Registered validator functions for config value validation on "set".
        self.validators = {}
        
        self.remoteSetTransformators = {}
        self.remoteGetTransformators = {}
        
        # Load default values
        self.config = {}
        for key in configList:
            self.config[key] = WH10ConfigManagerItem(configList[key])
        
        wh10ConfigCreateEmptyIfNotAvailable(self.configFile, [self.configSection])
        self.sync()
    
    def get(self, key):
        value = None
        self.lock.acquire()
        try:
            value = self.config[key].value
        except:
            archas.logError("Config: Invalid configuration value key (get): %s."%key)
        self.lock.release()
        return value

    def getAll(self):
        self.lock.acquire()
        cfg_all = dict()
        for key,item in self.config.iteritems():
            cfg_all[key] = item.value
        self.lock.release()
        return cfg_all
        
    def set(self, key, value, sync = False):
        """
        """
        ret = True
        self.lock.acquire()
        
        # Validate value if validator available
        validator = self.validators.get(key, None)
        if validator != None:
            if not validator(key, value):
                self.lock.release()
                return False
        
        changed = False
        
        try:
            if isinstance(value, type(self.config[key].default)):
                oldValue = self.config[key].value
                self.config[key].value = value
                # We check actively, because self.config[key].changed could be
                # True from a previous operation and will only be reset by
                # a sync operation 
                changed = oldValue != value
                self.config[key].changed = self.config[key].changed or changed
            else:
                archas.logError("Config: Value type mismatch for %s." % key)
                ret = False
        except:
            archas.logError("Config: Invalid configuration value key (set): %s."%key)
            ret = False
        self.lock.release()
        
        if changed and callable(self.configChangeHandler):
            self.configChangeHandler()
        
        if sync:
            self.sync()
        
        return ret
        
    def registerValidator(self, validator, key):
        """
        validator - Validator function of the form <validator (key, value)>
                    which must return True if value is valid or False if not.
        key - Configuration value key for which the value should be validated.
        
        When setting a validator for a key a previously registered validator
        will be unregistered automatically.
        """
        self.validators[key] = validator

    def unregisterValidator(self, key):
        try:
            del self.validators[key]
        except:
            archas.logWarning('No validator for "%s" to remove'%key)
        
    def sync(self):
        changesLoaded = False
        self.lock.acquire()
        try:
            config = RawConfigParser()
            config.read(self.configFile)
        except Exception as err:
            archas.logError("Config: Can not open %s to sync config: %s" % (self.configFile,str(err)))
            err = WH10_CONFIG_ERR_READ_CONFIG
        else:
            if not config.has_section(self.configSection):
                config.add_section(self.configSection)
            
            err = WH10_CONFIG_ERR_NO_ERR
            writeRequired = False
            for key,c in self.config.iteritems():
                if c.changed:
                    writeRequired = True
                    try:
                        if isinstance(c.value, int):
                            config.set(self.configSection, key, "%i" % c.value)
                        elif isinstance(c.value, float):
                            config.set(self.configSection, key, "%f" % c.value)
                        elif isinstance(c.value, unicode):
                            config.set(self.configSection, key, c.value.encode("utf-8"))
                        else:
                            archas.logError("Config: Invalid value type for %s"%key)
                        c.changed = False
                    except Exception as err:
                        archas.logError("Config: Failed to set config value %s (%s)." % (key, str(err)))
                        err = WH10_CONFIG_ERR_SET_CONFIG
                        
                try:
                    fileValue = None
                    if isinstance(c.default, int):
                        fileValue = config.getint(self.configSection, key)
                    elif isinstance(c.default, float):
                        fileValue = config.getfloat(self.configSection, key)
                    elif isinstance(c.default, unicode):
                        fileValue = config.get(self.configSection, key).decode("utf-8")
                    else:
                        archas.logError("Config: Invalid default value type for %s."%key)
                    if fileValue != None and fileValue != c.value:
                        valid = True
                        validator = self.validators.get(key, None)
                        if validator != None:
                            valid = validator(key, fileValue)
                        if not valid:
                            # We read the value as string for log message again
                            v = config.get(self.configSection, key).decode("utf-8")
                            archas.logWarning('Invalid value "%s" in configuration file for key "%s".'%(v, key))
                        else:
                            c.value = fileValue
                            c.changed = False
                            changesLoaded = True
                except Exception as e:
#                     wh10LogWarning("fail to get value for %s: %s. Setting default."%(key,str(e)))
                    c.value = c.default
                    c.changed = False
            if writeRequired:
                try:
                    with open(self.configFile, 'wb') as cfg_file:
                        config.write(cfg_file)
                except:
                    archas.logError("Config: Failed to write config values to %s." % self.configFile)
                    err = WH10_CONFIG_ERR_WRITE_CONFIG

        self.lock.release()
        
        # Config change handler is called on local and file changes
        if (changesLoaded or writeRequired):
            if callable(self.configChangeHandler):                            
                self.configChangeHandler()
            
        return err
    
    def registerRemoteSetTransformator(self, key, transformator):
        self.remoteSetTransformators[key] = transformator
        
    def registerRemoteGetTransformator(self, key, transformator):
        self.remoteGetTransformators[key] = transformator

    def unRegisterRemoteSetTransformator(self, key):
        try:
            del self.remoteSetTransformators[key]
        except:
            archas.logWarning('No remote set transformator for "%s" to remove'%key)

    def unRegisterRemoteGetTransformator(self, key):
        try:
            del self.remoteGetTransformators[key]
        except:
            archas.logWarning('No remote get transformator for "%s" to remove'%key)

