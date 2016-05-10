import sys
import os
import datetime
import time
import calendar
import dateutil
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch
import tattle 
import re
import json
import operator
import collections
from pprint import pprint

logger = tattle.get_logger('tattle.filter')

def date_histogram(res):
    intentions = res['intentions']
    events_by = 'events_by_%s' % intentions['qd']['agg_opts']['by']
    agg_type = intentions['qd']['agg_opts']['agg_type']
    agg_field = intentions['qd']['agg_opts']['agg_field']

    rd = {}
    rd['_results'] = {}
    for results in res['_results']['aggregations'][events_by]['buckets']:
        mres = []
        for r in results['events_by_date']['buckets']:
            val_key = "%s_%s" % (agg_type, agg_field)
            mres.append({'time': r['key_as_string'], 'value': r[val_key]['value']})
        rd['_results'][results['key']] = mres
    rd['query_intentions'] = intentions
    return rd

def terms(res):
    intentions = res['intentions']
    events_by = 'events_by_%s' % intentions['qd']['agg_opts']['by']
    agg_type = intentions['qd']['agg_opts']['agg_type']
    agg_field = intentions['qd']['agg_opts']['by']
    rd = {}
    rd['_results'] = {}
    for results in res['_results']['aggregations'][events_by]['buckets']:
        mres = []
        val_key = "%s_%s" % (agg_type, agg_field)
        mres.append({'doc_count': results.get('doc_count'), 'key': results['key']})
        
    rd['_results'] = mres
    rd['query_intentions'] = intentions
    return rd

def result_set(results):
    retd = {}
    retd['query_intentions'] = results['intentions']
    mres = []
    for r in results['_results']['hits']['hits']:
        mres.append(bluenote.flatten_dict(r))
    retd['_results'] = mres 
    return retd

def find_in_dict(dct, regex):
    results = []
    if isinstance(dct, dict):
        for k,v in dct.iteritems():
            if re.match(regex, k):
                # If we are matching an agg bucket, we will want the corrisponding key and doc values
                if re.match('.*doc_count$', k) or re.match('.*key$', k):
                    if 'doc_count' in k:
                        key1 = k.replace('doc_count', 'key')
                        key2 = k
                    elif 'key' in k:
                        key1 = k.replace('key', 'doc_count')
                        key2 = k
                    events_list = [k, { key1: dct[key1], key2: dct[key2] }]
                    results.append(events_list)
                #elif re.match('.*value$', k):
                #    events_list = [ k:v, 'key': 'omg', 'val': 'omg1' ]
                #    results.append(events_list)]
                else:
                    events_list = [k, {k:v}]
                    results.append(events_list)
    else:
        results = None
        #logger.info("No items found in find_in_dict, dct: {}, regex: {}".format(dct, regex))
    return results



''' 
    Sets an operator object for our shorthand operator syntax
'''
def get_operator(op):
    if not op: return None

    if "ge" in op:
        opr = operator.__ge__
    elif "gt" in op:
        opr = operator.__gt__
    elif "le" in op:
        opr = operator.__le__
    elif "lt" in op:
        opr = operator.__lt__
    elif "eq" in op:
        opr = operator.eq
    elif "ne" in op:
        opr = operator.ne
    return opr
    
def findindict(dct, regex):
    for k,v in dct.items():
        if isinstance(v, dict):
            return findindict(v, regex)
        else:
            if re.match(regex, k):
                ret = (k,v)
                return ret

def meets_in_field(results, regex, op, number):
    retl = []
    opr = get_operator(op)
    for result in results:
        found = findindict(result, regex)
        if found:
            k,v = found
            if opr(v, number):
                retl.append(result)
    return retl

def meets_threshold(lst, op, number):
    opr = get_operator(op) 
    retl = []
    for item in lst:
        item_key = item[0]
        #if item[1][item_key] >= number:
        if opr(item[1][item_key], number):
            d = {}
            ''' normalize the key and doc count, basically strip out everything except 'key' and 'doc_count' '''
            for k,v in item[1].iteritems():
                if 'doc_count' in k:
                    d['doc_count'] = v
                elif 'key' in k:
                    d['key'] = v
            item[1] = d
            retl.append(item)
    return retl

def meets_total(results, total, operator, number):
    ret = None
    #total = results['hits'].get('total')
    opr = get_operator(operator)
    if opr(total, number):
        return ( total, results )

