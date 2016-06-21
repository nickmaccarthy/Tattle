

import sys
import os
import datetime
import time
import calendar
import dateutil
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
        self._PRETTY_TS = 'MMM d YYYY, HH:mm:ss ZZ'
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
        except TQLException, e:
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
                if self.get_agg(part.split()[0]):
                    base,fname,args = self.get_agg(part.split()[0])
                    td = defaultdict(dict)
                    td['type'] = fname
                    td['agg'] = self.build_agg(part)
                    qd['aggs'].append(td)
                if 'fields' in part:
                    qd['fields'] = self.build_fields(part)

        else:
            qd['query_opts'] = self.build_main_query(query_base)

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

        if args.has_key('name') or args.has_key('title'):
            agg_name = args.get('name') or args.get('title')
            try:
                del(args['name'])
            except:
                del(args['title'])

        if args.has_key('order'):
            args['order'] = eval(args['order'])


        #print string

        #print re.search('(\[\s*\{.*?\])', string)

        ## extract our order by, etc
        #if re.search('(\[\s*\{.*?\])', string): 
        #    regex = '(\[\s*\{.*?\])'
        #    m = re.search(regex,string)
        #elif re.search('(\{.*?\})', string):
        #    regex = '(\{.*?\})'
        #    m = re.search(regex,string)

        #if m:
        #    order = m.group(1)
        #    try:
        #        order = eval(order)
        #    except Exception as e:
        #        msg = 'Unable to eval json into dict: %s' % (e)
        #        logger.exception(msg)
        #        raise Exception(msg)

        #    args['order'] = order
        #    # strip it out of the query arg
        #    string = re.sub(regex, '', string)

        #parts = string.split(" ")
        #tattle.pprint(parts)
        #for part in parts:
        #    splitkey = None
        #    if ":" in part:
        #        splitkey = ':'
        #    elif "=" in part:
        #        splitkey = '='

        #    if splitkey:
        #        k,v = part.split(splitkey, 1)
        #        # extract our order by, etc
        #        if re.search('(\[\s*\{.*?\])', string): 
        #            print "WTF"
        #            regex = '(\[\s*\{.*?\])'
        #            m = re.search(regex,string)
        #        elif re.search('(\{.*?\})', string):
        #            regex = '(\{.*?\})'
        #            m = re.search(regex,string)

        #        if m:
        #            order = m.group(1)
        #            try:
        #                order = eval(order)
        #            except Exception as e:
        #                msg = 'Unable to eval json into dict: %s' % (e)
        #                logger.exception(msg)
        #                raise Exception(msg)

        #            args['order'] = order
        #            # strip it out of the query arg
        #            string = re.sub(regex, '', string)

        #        print string
        #        args[k] = v

        thed = { 'title': agg_name or agg_type, 'args': args, 'type': agg_type }
        #tattle.pprint(thed)
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
            try:
                fa = aggs[0]['agg']
                base, fname, params_def = self.get_agg(fa['type'])
                basename = self.find_method(base)
                aggobj = getattr(s.aggs, basename)(*[fa['title'] , fa['type']], **fa['args'])
            except Exception as e:
                raise TQLException("Unable to agg base: reason: {}".format(e))

            if len(aggs) > 1:
                for agg in aggs[1:]:
                    try:
                        agg = agg['agg']
                        agg_type = agg['type']
                        base, fname, params_def = self.get_agg(agg_type)
                        basename = self.find_method(base)
                        aggobj = getattr(aggobj, basename)(*[agg['title'], fname], **agg['args'])

                        # todo: support pipelines
                        #if basename == 'pipeline':
                        #    print "pipeline"
                        #    #s.aggs(agg_title, fname, **args)
                        #    aggz = getattr(s.aggs, basename)(*[agg_title,fname], **args)
                        #else:
                        #    aggz = getattr(aggz, basename)(*[agg_title,fname], **args)

                    except Exception as e:
                        raise TQLException("Unable to agg base in a loop: reason: {}".format(e))

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
        # get a list of our indexes for searching against
        if '*' in index:
            index_name = index.strip('*')
            # todo - the interval and format should be set via config variable in the alert.yml
            search_indexes = tattle.get_indexes(index_name, datemath(args['start']), datemath(args['end']))
        else:
            search_indexes = index
        return search_indexes
        
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


