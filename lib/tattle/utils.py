import json
import pprint
import re
from collections import OrderedDict 
import os
from operator import itemgetter
from datemath import datemath
import tattle
import random

class FlattenDict(object):


    def __init__(self, opts_delimiter='.', kibana_nested=False, skip_hits_meta=True):
        self.csv_headers = [] 
        self.opts_delimiter = '.'
        self.kibana_nested = kibana_nested
        self.out = {}
        self.retl = []
        self.skip_hits_meta = skip_hits_meta


    def flatten_dict(self, source, ancestors=[], header_delimeter='.'):
        def is_list(arg):
            return type(arg) is list

        def is_dict(arg):
            return type(arg) is dict

        if is_dict(source):
            for key in source.keys():
                self.flatten_dict(source[key], ancestors + [key])

        elif is_list(source):
            if self.kibana_nested:
                [self.flatten_dict(item, ancestors) for item in source]
            else:
                [self.flatten_dict(item, ancestors + [str(index)]) for index, item in enumerate(source)]
        else:
            header = header_delimeter.join(ancestors)
            if header not in self.csv_headers:
                self.csv_headers.append(header)
            try:
                self.out[header] = '%s%s%s' % (out[header], self.opts.delimiter, source)
            except:
                self.out[header] = source
        return self.out

    def flatten_hits(self, source):
        retl = []
        for s in source:
            if self.skip_hits_meta:
                hit = s['_source']
                retl.append(self.flatten_dict(hit))
            else:
                retl.append(self.flatten_dict(s))

        return retl


class EventQueue(object):

    def __init__(self, **kwargs):
        self.alert = None
        self.es_results = None
        self.matches = None 
        self.intentions = None
        self.results_hits = None
        self.results_aggs = None
        self.results_total = None
        self.timeframe = datemath('now-1m') 
        self.timestamp = '@timestamp'
        self.data = (self.matches, self.es_results, self.alert)
        for k,v in kwargs.items():
            setattr(self, k, v)

    def count(self, key='matches'):
        #tattle.pprint(getattr(self,key))
        return len(getattr(self, key))

    def get_random(self, number, of='matches'):
        return random.sample(getattr(self, of), number)

    def duration(self, key='matches'):
        if not self.data:
            return datemath('now')
        else:
            d = getattr(self,key)
            d = sorted(d, key=itemgetter(self.timestamp))
            return datemath(d[-1]) - datemath(d[0])

    def __repr__(self):
        return "<EventQueue count=%s>" % ( self.count() )
