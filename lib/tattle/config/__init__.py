import sys
import os
import glob
import yaml

TATTLE_HOME = os.path.join(os.environ['TATTLE_HOME'])

import tattle

#logger = tattle.get_logger('tattle.config')

class TattleYAMLLoadException(Exception):
    pass

''' opens a yml file and returns a dictionary representing the configuration '''
def load_yaml_file(filename):
    ''' loads a yaml config file '''
    with open(filename, 'r') as f:
        try:
            doc = yaml.load(f)
        except Exception as e:
            raise TattleYAMLLoadException("Unable to load yaml file: {}, reason: {}".format(filename, e))
    return doc

''' gets a list all directories where Tattle will find Tales '''
def get_taledirs():
    ''' directories where we can find tales '''
    TATTLE_HOME = tattle.get_tattlehome()
    
    dirs = [
        os.path.join(TATTLE_HOME, 'etc', 'tattle', 'tales'),
        os.path.join(TATTLE_HOME, 'etc', 'tales'),
        os.path.join(TATTLE_HOME, 'etc', 'alerts'),

    ]

    env_dirs = os.environ.get('TATTLE_TALES')
    if env_dirs:
        env_dirs = env_dirs.split(':')
        for d in env_dirs:
            dirs.append(d)

    confs = load_configs()

    if 'tattle' in confs:
        if 'tale_dirs' in confs['tattle']:
            if isinstance(confs['tattle']['tale_dirs'], list):
                for d in confs['tattle']['tale_dirs']:
                    dirs.append(d)
            elif isinstance(confs['tattle']['tale_dirs'], str):
                tale_dirs = confs['tattle']['tale_dirs'].split(':')
                for d in tale_dirs:
                    dirs.append(d)

    return dirs

''' gets a list of all directies where Tattle can find its config files '''
def get_configdirs():
    confs = {}
    conf_dirs = [ os.path.join(TATTLE_HOME, 'etc', 'tattle') ]
    
    tattle_conf_env = os.environ.get('TATTLE_CONFIG_DIR')
    if tattle_conf_env:
        conf_env_dirs = tattle_conf_env.split(':')
        for d in conf_env_dirs:
            conf_dirs.append(d)
    
    return conf_dirs


''' 
    Loads all Tattle config files into a dictionary
    key for the dict is the name of the config
'''
def load_configs():

    confs = {}
    conf_dirs = get_configdirs()

    for dir in conf_dirs:
        for yaml_conf in glob.glob("{}/*.y*ml".format(dir)):
            conf_name = os.path.basename(yaml_conf).split('.')[0]
            try:
                loaded = load_yaml_file(yaml_conf)
            except Exception as e:
                raise "Unable to load tattle configuration: {}, reason: {}".format(yaml_conf, e)
            confs[conf_name] = loaded

    return confs  


''' Loads all of our Tales into a dictionary '''
def load_alerts():
    tale_dirs = get_taledirs()
    tales = []
    for tale_dir in tale_dirs:
        for tale in glob.glob("{}/*.y*ml".format(tale_dir)):
            tale_key = None
            tale_filename = os.path.basename(tale) 
            loaded = load_yaml_file(tale)
            if 'alerts' in loaded:
                tale_key = 'alerts'
            elif 'tales' in loaded:
                tale_key = 'tales'

            if tale_key:
                for conf in loaded[tale_key]:
                    conf['alert_filename'] = tale_filename
                    tales.append(conf)
            else:
                loaded['alert_filename'] = tale_filename
                tales.append(loaded)        
    return tales
   
''' alias to load_alerts() '''
def load_tales():
    return load_alerts() 

