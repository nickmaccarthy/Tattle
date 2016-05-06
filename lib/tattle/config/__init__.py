import sys
import os
import glob
import yaml

TATTLE_HOME = os.path.join(os.environ['TATTLE_HOME'])

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

def load_tattle_config():
    ''' loads our tattle config '''
    tattle_conf = load_yaml_file(os.path.join(TATTLE_HOME, 'etc', 'tattle', 'tattle.yml'))
    return tattle_conf
            
def load_alerts():
    ''' loads our alerts '''
    alert_dir = os.path.join(TATTLE_HOME, 'etc', 'alerts')
    alerts = []
    for alert in glob.glob("{}/*.y*ml".format(alert_dir)):
        alert_filename = os.path.basename(alert) 
        loaded = load_yaml_file(alert)
        if loaded.has_key('alerts'):
            for conf in loaded['alerts']:
                conf['alert_filename'] = alert_filename
                alerts.append(conf)
        else:
            loaded['alert_filename'] = alert_filename
            alerts.append(loaded)        
    return alerts 
    
