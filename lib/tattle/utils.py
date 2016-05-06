import json
import pprint
import re
from collections import OrderedDict 
import os

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

