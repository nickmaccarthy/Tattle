import sys
import os
import datetime
import time
import calendar
import dateutil
import collections
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch
import elasticsearch_dsl
from elasticsearch_dsl.aggs import AGGS 
from datemath import datemath, dm
import tattle 
from tattle.exceptions import TQLException, ESQueryException
import re
import json

logger = tattle.get_logger('tattle.search.Search')

class DSLBase(object):
    def __init__(self, **kwargs):
        self._ISO_TS = 'YYYY-MM-DDTHH:mm:ssZZ'
        self._PRETTY_TS = 'MMM D YYYY, HH:mm:ss ZZ'
        self.agg_size_from = 0
        self.agg_size = 0
        self.hit_size_from = 0
        self.hit_size = 10000 
        self._query_raw = ''
        self._query = ''
        self._start = None
        self._start_time = dm('now-1m')
        self._end_time = dm('now')
        self.exclude = ''
        self._ts_field = '@timestamp'
        self._index_ts_pattern = 'YYYY.MM.DD'
        self._index_name_pattern = 'logstash-*'

        for key, value in kwargs.items():
            if key in ('start', 'from', '_from'):
                self._start = value 
            elif key in ('end', 'to', '_to'):
                self._end = value
            setattr(self, key, value)

        self._index = tattle.get_indexes(self.index, self._start_time, self._end_time, pattern=self._index_ts_pattern)


class ESQuery(DSLBase):


    def __init__(self, query, **kwargs):

        super(ESQuery, self).__init__(**kwargs)

        self.es_query = query
        if self._start is None:
            raise TQLException("Searches require at least a start time with either a timestamp or datemath expression: start='now-10m', end='now' | start='20160101', end='now'")

        self.build_es_query()

    def build_es_query(self,):
        if self.query_args:
            self.query_args = tuple(self.query_args)
            self.es_query = self.es_query % ( self.query_args )

        try:
            self._esq = self.es_query
            self._esqd = json.loads(self.es_query)
        except Exception as e:
            raise ESQueryException("Unable to JSON load our ES Query, reason: {}".format(e))


class TQL(DSLBase):


    def __init__(self, query, **kwargs):

        super(TQL, self).__init__(**kwargs)

        if self._start is None:
            raise TQLException("Searches require at least a start time with either a timestamp or datemath expression: start='now-10m', end='now' | start='20160101', end='now'")
        try:
            self._query_raw = query
            self._query = query
            self._start_time = dm(self._start)
            self._end_time = dm(self._end)
            self._index = tattle.get_indexes(self._index_name_pattern, self._start_time, self._end_time, pattern=self._index_ts_pattern)
        except TQLException as e:
            raise TQLArgsException("Unable to set arguments for TQL, I am missing: %s" % (e))

        self._start_time_iso_str = self._start_time.format(self._ISO_TS)
        self._end_time_iso_str = self._end_time.format(self._ISO_TS)
        self._start_time_pretty = self._start_time.format(self._PRETTY_TS)
        self._end_time_pretty = self._end_time.format(self._PRETTY_TS)
        self._qd = self.get_intentions(self._query_raw)
        self.build_es_query()
   
    
    def get_intentions(self, query):
        query_parts = None
        qd = {}
        qd['fields'] = ['*']
        if "|" in query:
            query_parts = query.split("|")
            query_base = query_parts[0]
        else:
            query_base = query

        query_base = re.sub('index:.*? ', '', query_base)

        if query_parts:
            # clean up any whitespace in the elements
            query_parts = [ q.strip() for q in query_parts ]

            qd['query_opts'] = {}
            qd['query_opts'] = self.build_main_query(query_parts[0])
            qd['aggs'] = []
            for i,part in enumerate(query_parts):
                if '>>' in part:
                    parts = part.split('>>')
                    parts = [ q.strip() for q in parts ]
                    #print("get_intentions() - Non nested parts after split: {}".format(parts))
                    #tattle.pprint(parts)
                    non_nested = []
                    for part in parts:
                        #print('get_intention() - part: {}'.format(part))
                        #print('get_intention() - part0: {}'.format(part.split()[0]))
                        base,fname,args = self.get_agg(part.split()[0])
                        td = defaultdict(dict)
                        td['type'] = fname
                        td['agg'] = self.build_agg(part)
                        non_nested.append(td)
                    #print("get_intention() - Non nested:")
                    #tattle.pprint_as_json(non_nested)
                    qd['aggs'].append(non_nested)
                elif self.get_agg(part.split()[0]):
                    base,fname,args = self.get_agg(part.split()[0])
                    td = defaultdict(dict)
                    td['type'] = fname
                    td['agg'] = self.build_agg(part)
                    qd['aggs'].append(td)
                if 'fields' in part:
                    qd['fields'] = self.build_fields(part)

        else:
            qd['query_opts'] = self.build_main_query(query_base)

        #print("get_intentions() - query dict:")
        #tattle.pprint_as_json(qd) 
        #print('\n\n\n')

        return qd

    def build_fields(self, string):
        field_str = None
        if re.match("fields (.*?)", string):
            field_match = re.search("fields (.*?)$", string)
            if field_match.group(1):
                field_str = field_match.group(1)

        if field_str:
            fields = [ x.strip() for x in field_str.split(',') ]
            return fields

        return ['*'] 

    def get_agg(self, agg_name):
        our_tuple = None
        for base, fname, params_def in AGGS:
            if agg_name == fname:
                our_tuple = (base, fname, params_def)
                return our_tuple

    def build_agg(self,string):
        agg_name = None
        order = None
        script = None
        m = None
        args = {}
        agg_type, agg_args = string.split(" ", 1)

        '''
            find any of our key=value pairs, will even match order statements and the such as well
            examples: field=@timestamp, order=[{'_count':'desc'},{'field':'foobar'}]
        '''
        args = dict(re.findall('(\w+)\s*=\s*([^=]*)(?=\s+\w+\s*=\s*|$)', agg_args))

        # clean up commas out of the arg keys and vals
        args = { k.strip(','):v.strip(',') for k,v in args.items() }

        if 'name' in args or 'title' in args:
            agg_name = args.get('name') or args.get('title')
            try:
                del(args['name'])
            except:
                del(args['title'])

        if 'order' in args:
            args['order'] = eval(args['order'])
        if 'script' in args:
            args['script'] = eval(args['script'])


        thed = { 'title': agg_name or agg_type, 'args': args, 'type': agg_type }
        return thed

    def build_main_query(self, lquery):
        if '_type' in lquery:
            m = re.search('_type:(.*?)\s*', lquery)
            _type = m.group(0)
        else:
            _type = None
        index = self._index
        return { '_type': _type, 'index': index, 'args': lquery }

    def find_method(self, cls):
        cls = str(cls)
        if 'Bucket' in cls:
            return 'bucket'
        elif 'Metric' in cls:
            return 'metric'
        elif 'Pipeline' in cls:
            return 'pipeline'
        elif 'Agg' in cls:
            return 'bucket'


    def build_aggs(self, aggobj, aggs):
        #print("build_aggs() - aggs that came in")
        #tattle.pprint_as_json(aggs)
        #print("build_aggs() - aggobj: {}".format(aggobj))

        if isinstance(aggs, dict):
            try:
                agg = aggs['agg']
                agg_type = aggs['type']
                base, fname, params_def = self.get_agg(agg_type)
                basename = self.find_method(base)
                aggobj = getattr(aggobj, basename)(*[agg['title'], fname], **agg['args'])
            except Exception as e:
                raise TQLException("Unable to agg in a loop: reason: {}, agg: {}".format(e, agg))
        elif isinstance(aggs, list):
            for agg in aggs:
                #print('build_aggs() - AGG:')
                #tattle.pprint_as_json(agg)
                #print('build_aggs() - type: {}'.format(type(agg)))
                #if isinstance(agg, collections.defaultdict):
                if isinstance(agg, dict):
                    #print("build_aggs() - was a defaultdict: {}".format(agg))
                    try:
                        agg = agg['agg']
                        agg_type = agg['type']
                        base, fname, params_def = self.get_agg(agg_type)
                        basename = self.find_method(base)
                        #print('build_aggs() - basename: {}'.format(basename))
                        aggobj = getattr(aggobj, basename)(*[agg['title'], fname], **agg['args'])
                    except Exception as e:
                        raise TQLException("Unable to agg in a loop: reason: {}, agg: {}".format(e, agg))
                elif isinstance(agg, list):
                    #print("build_aggs() - got a list, details below:")
                    #tattle.pprint(aggobj)
                    #tattle.pprint(agg)
                    #print('\n\n')
                    #self.build_aggs(aggobj, agg)
                    for a in agg:
                        #print('build_aggs() - list loop: {}'.format(a)) 
                        agg = a['agg']
                        agg_type = agg['type']
                        base, fname, params_def = self.get_agg(agg_type)
                        basename = self.find_method(base)
                        #print('build_aggs() - basename: {}'.format(basename))
                        getattr(aggobj, basename)(*[agg['title'], fname], **agg['args'])
        return aggobj


    def build_es_query(self,):
        qd = self._qd 

        rangeq = elasticsearch_dsl.Q('range', **{ '{}'.format(self._ts_field) : { 'from': self._start_time.format(self._ISO_TS), 'to': self._end_time.format(self._ISO_TS)}})
        luceneq = elasticsearch_dsl.Q('query_string', query=qd['query_opts']['args'])
        excludeq = elasticsearch_dsl.Q('query_string', query=self.exclude)

        s = elasticsearch_dsl.Search()
        s = s.source(include=qd['fields'])
        q = elasticsearch_dsl.Q('bool', must=[luceneq,rangeq], must_not=excludeq)
        s = s.query(q)

        # aggs
        if 'aggs' in qd and len(qd.get('aggs')) >= 1:
            aggs = qd['aggs']

            #try:
            #    fa = aggs[0]['agg']
            #    base, fname, params_def = self.get_agg(fa['type'])
            #    basename = self.find_method(base)
            #    aggobj = getattr(s.aggs, basename)(*[fa['title'] , fa['type']], **fa['args'])
            #except Exception as e:
            #    raise TQLException("Unable to agg base: reason: {}, agg: {}".format(e, aggs[0]))

            #print('build_es_query() - aggs that came in:')
            #tattle.pprint_as_json(aggs)
            try:
                #aggobj = self.build_aggs(s.aggs, aggs)
                aggobj = self.build_aggs(s.aggs, aggs[0])

                #print("build_es_query() - aggs[0]:")
                #tattle.pprint_as_json(aggs[0])
            except Exception as e:
                raise TQLException("Unable to agg base: reason: {}, agg: {}".format(e, aggs))

            if len(aggs) > 1:
                aggobj = self.build_aggs(aggobj, aggs[1:])
                
            #if len(aggs) > 1:
            #    for agg in aggs[1:]:
            #        try:
            #            agg = agg['agg']
            #            agg_type = agg['type']
            #            base, fname, params_def = self.get_agg(agg_type)
            #            basename = self.find_method(base)
            #            aggobj = getattr(aggobj, basename)(*[agg['title'], fname], **agg['args'])

            #            # todo: support pipelines
            #            #if basename == 'pipeline':
            #            #    print "pipeline"
            #            #    #s.aggs(agg_title, fname, **args)
            #            #    aggz = getattr(s.aggs, basename)(*[agg_title,fname], **args)
            #            #else:
            #            #    aggz = getattr(aggz, basename)(*[agg_title,fname], **args)

            #        except Exception as e:
            #            raise TQLException("Unable to agg base in a loop: reason: {}".format(e))

            s = s[self.agg_size_from:self.agg_size]
        else:
            s = s[self.hit_size_from:self.hit_size]

        self._esq = s
        self._esqd = self._esq.to_dict()


class Search(object):

    def set_vars(self, **kwargs):
        for key, value in kwargs.items():
            if key in ('start', 'from', '_from'):
                self._start = value 
            elif key in ('end', 'to', '_to'):
                self._end = value
            if key in ('index'):
                self._index = value
            setattr(self, key, value)

    def build_indexes(self, index, **kwargs):
        args = {}
        for k,v in kwargs.items():
            args[k] = v
        return tattle.get_indexes(index, datemath(kwargs.get('start', 'now-1h')), datemath(kwargs.get('end', 'now')))

        
    def es_query(self, query, **qargs):
        self.set_vars(**qargs)

        esqargs = dict( index=index, start=start, end=end )
        for k,v in qargs.items():
            esqargs.update({k:v})

        qobj = ESQuery(query, **esqargs)
        
        search_indexes = self.build_indexes(index, start=start, end=end)
         
        returnd = {}
        returnd['search_indexes'] = search_indexes
        returnd['esquery'] = qobj._esqd
        returnd['intentions'] = vars(qobj)
        return returnd

    def tql_query(self, query, **qargs):
        self.set_vars(**qargs)

        exclude = qargs.get('exclude', '')
        filters = qargs.get('filters', '')

        tqlargs = dict(
                    index=self._index,
                    start=self._start,
                    end=self._end,
                    exclude=exclude)

        for k,v in qargs.items():
            tqlargs.update({k:v})

        qobj = TQL(query, **tqlargs)

        search_indexes = self.build_indexes(tqlargs['index'], start=tqlargs['start'], end=tqlargs['end'])

        returnd = {}
        returnd['search_indexes'] = search_indexes
        returnd['esquery'] = qobj._esqd
        returnd['intentions'] = vars(qobj)
        return returnd


