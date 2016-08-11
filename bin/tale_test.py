import sys
import os
import re
import datetime
import time
import signal
import yaml
from multiprocessing.pool import ThreadPool
import argparse

TATTLE_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['TATTLE_HOME'] = str(TATTLE_HOME)

sys.path.append(os.path.join(TATTLE_HOME, 'lib'))
sys.path.append(os.path.join(TATTLE_HOME))

from elasticsearch import Elasticsearch
import tattle
import tattle.workers
import tattle.config

logger = tattle.get_logger('tattled')

# Load configs
tcfg = tattle.config.load_configs().get('tattle')

def handleargs():
    # Run the alerts
    parser = argparse.ArgumentParser(description='Validate a tattle tale configuration')
    parser.add_argument('alert_filename', type=str, help="tattle tale configuration filename")
    args = parser.parse_args()
 
    alert = tattle.config.load_yaml_file(args.alert_filename)
    worker(alert)

try:
    from ES import connect as es_connect 
    es = es_connect()
except Exception as e:
    logger.exception("Unable to establish connection to ES cluster. Reason: %s" % (e))
    sys.exit()

#eslogger = tattle.get_logger('elasticsearch')
#estracelogger = tattle.get_logger('elasticsearch.trace')

# checks to see if the tattle index exists
tattle_index = es.indices.exists(index='tattle-int')
# check to see if the tattle index template exists
tattle_index_template = es.indices.exists_template(name='tattle-int')

if not tattle_index_template:
    with open(os.path.join(TATTLE_HOME, 'usr','share','templates','index', 'tattle-int.json'), 'r') as f:
        template_json = f.read()
    createit = es.indices.put_template(name='tattle-int', create=True, body=template_json)

if not tattle_index:
    # Creates our tattle-internal index if its not already there
    index_create = es.indices.create(index='tattle-int', ignore=400)
    logger.info('tattle index did not exist.  creating it')

def worker(alert):
    try:
        workit = tattle.workers.tnd(es, alert)
    except Exception as e:
        logger.exception("Unable to complete worker task, alert: {}, reason: {}".format(alert['name'], e))  

if __name__ == "__main__":
    handleargs()
