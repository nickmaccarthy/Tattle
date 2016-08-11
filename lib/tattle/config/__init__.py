import sys
import os
import glob
import yaml

TATTLE_HOME = os.path.join(os.environ['TATTLE_HOME'])

import tattle

class TattleYAMLLoadException(Exception):
    pass

def load_yaml_file(filename):
    ''' loads a yaml config file '''
    with open(filename, 'r') as f:
        try:
            doc = yaml.load(f)
        except Exception as e:
            raise TattleYAMLLoadException("Unable to load yaml file: {}, reason: {}".format(filename, e))
    return doc

## These configs should be able to by dynamically loaded and stored and referenced by a key
## And they should be found via glob so we dont have to depend on the exact yml vs yaml reference
## Working on deprecating these
#def load_pd_config():
#    pdconf = load_yaml_file(os.path.join(TATTLE_HOME, 'etc', 'tattle', 'pagerduty.yml'))
#    return pdconf
#def load_email_config():
#    ''' loads our email config '''
#    emailconf = load_yaml_file(os.path.join(TATTLE_HOME, 'etc', 'tattle', 'email.yaml'))
#    return emailconf
#def load_tattle_config():
#    ''' loads our tattle config '''
#    tattle_conf = load_yaml_file(os.path.join(TATTLE_HOME, 'etc', 'tattle', 'tattle.yml'))
#    return tattle_conf
    
def get_taledirs():
    ''' directories where we can find tales '''
    TATTLE_HOME = tattle.get_tattlehome()
    dirs = [
        os.path.join(TATTLE_HOME, 'etc', 'tattle', 'tales'),
        os.path.join(TATTLE_HOME, 'etc', 'tales'),
        os.path.join(TATTLE_HOME, 'etc', 'alerts')
    ]
    return dirs

def load_configs():
    ''' 
        loads all tattle configurations
        key for the dict is the name of the config
    '''
    confs = {}
    conf_dirs = [ os.path.join(TATTLE_HOME, 'etc', 'tattle') ]
    for dir in conf_dirs:
        for yaml_conf in glob.glob("{}/*.y*ml".format(dir)):
            conf_name = os.path.basename(yaml_conf).split('.')[0]
            try:
                loaded = load_yaml_file(yaml_conf)
            except Exception as e:
                raise "Unable to load tattle configuration: {}, reason: {}".format(yaml_conf, e)
            confs[conf_name] = loaded
    return confs  

def load_alerts():
    ''' loads our alerts '''
    tale_dirs = get_taledirs()
    tales = []
    for tale_dir in tale_dirs:
        for tale in glob.glob("{}/*.y*ml".format(tale_dir)):
            tale_key = None
            tale_filename = os.path.basename(tale) 
            loaded = load_yaml_file(tale)
            if loaded.has_key('alerts'):
                tale_key = 'alerts'
            elif loaded.has_key('tales'):
                tale_key = 'tales'

            if tale_key:
                for conf in loaded[tale_key]:
                    conf['alert_filename'] = tale_filename
                    tales.append(conf)
            else:
                loaded['alert_filename'] = tale_filename
                tales.append(loaded)        
    return tales
   
def load_tales():
    return load_alerts() 

