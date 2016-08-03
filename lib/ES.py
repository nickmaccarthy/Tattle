from elasticsearch import Elasticsearch
import tattle.config
import tattle

logger = tattle.get_logger('es-client')

class ESConnectException(Exception):
    pass

''' 
    Establishes a connection to our ES cluster
    underneath the covers, the Elasticsearch class will maintain state for us and keep us thread safe
'''
def connect():
    conf = tattle.config.load_configs().get('elasticsearch')
    try:
        es = Elasticsearch(conf['servers'], **conf['args'])
        return es
    except Exception as e:
        err_msg = "Unable to establish connection to the Elasticsearch cluster. Config: {}, error: {}".format(conf, e)
        logger.exception(err_msg)
        raise ESConnectException(err_msg)
        

