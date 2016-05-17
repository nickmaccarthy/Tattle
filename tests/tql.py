#!/usr/local/bin/python
import sys
import os
import re
import datetime
import time
import yaml
import json

TATTLE_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['TATTLE_HOME'] = str(TATTLE_HOME)

sys.path.append(os.path.join(TATTLE_HOME, 'lib'))
sys.path.append(os.path.join(TATTLE_HOME))

import unittest

from elasticsearch import Elasticsearch
import tattle
import tattle.workers
import tattle.config
from tattle.search import Search

s = Search()

class TestTQL(unittest.TestCase):

    def tql_query(self, query, index='logstash-*', start='2016-01-01||-2h', end='2016-01-01'):
        try:
            ourq = s.tql_query(query, index=index, start=start, end=end)
            return ourq
        except Exception as e:
            raise Exception("Unable to run TQL query, reason: {}".format(e))
   

    def testIndexPattern(self):
        indexes = self.tql_query('foobarbaz', index='logstash-*', start='2016-01-01||-3d', end='2016-01-01')
        expected = "logstash-2015.12.29,logstash-2015.12.30,logstash-2015.12.31,logstash-2016.01.01" 
        self.assertEqual(indexes['search_indexes'], expected) 


    def testLuceneQueryNoAggs(self):
        tqlq = self.tql_query('hostname.raw:foobarbaz')
        expected = """
            {
                    "_source": {
                        "include": [
                            "*"
                        ]
                    },
                    "from": 0,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "query_string": {
                                        "query": "hostname.raw:foobarbaz"
                                    }
                                },
                                {
                                    "range": {
                                        "@timestamp": {
                                            "from": "2015-12-31T22:00:00-00:00",
                                            "to": "2016-01-01T00:00:00-00:00"
                                        }
                                    }
                                }
                            ],
                            "must_not": [
                                {
                                    "query_string": {
                                        "query": ""
                                    }
                                }
                            ]
                        }
                    },
                    "size": 10000
                } 
        """        
        self.assertEqual(tqlq['esquery'], json.loads(expected)) 

    def testFields(self):
        tqlq = self.tql_query('status:[500-502] | fields @timestamp, status, message')
        expected = """
                {
                    "_source": {
                        "include": [
                            "@timestamp",
                            "status",
                            "message"
                        ]
                    },
                    "from": 0,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "query_string": {
                                        "query": "status:[500-502]"
                                    }
                                },
                                {
                                    "range": {
                                        "@timestamp": {
                                            "from": "2015-12-31T22:00:00-00:00",
                                            "to": "2016-01-01T00:00:00-00:00"
                                        }
                                    }
                                }
                            ],
                            "must_not": [
                                {
                                    "query_string": {
                                        "query": ""
                                    }
                                }
                            ]
                        }
                    },
                    "size": 10000
                }
        """
        self.assertEqual(tqlq['esquery'], json.loads(expected)) 

    def testTermsAgg(self):
        tqlq = self.tql_query('* | terms field=hostname.raw')
        expected = """
                  {
                    "_source": {
                        "include": [
                            "*"
                        ]
                    },
                    "aggs": {
                        "terms": {
                            "terms": {
                                "field": "hostname.raw"
                            }
                        }
                    },
                    "from": 0,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "query_string": {
                                        "query": "*"
                                    }
                                },
                                {
                                    "range": {
                                        "@timestamp": {
                                            "from": "2015-12-31T22:00:00-00:00",
                                            "to": "2016-01-01T00:00:00-00:00"
                                        }
                                    }
                                }
                            ],
                            "must_not": [
                                {
                                    "query_string": {
                                        "query": ""
                                    }
                                }
                            ]
                        }
                    },
                    "size": 0
                }
                """ 
        self.assertEqual(tqlq['esquery'], json.loads(expected)) 

    def testTermsWithOrder(self):
        tqlq = self.tql_query('metric:ReadIOPS | date_histogram field=@timestamp, interval=minute | terms field=database.raw, order=[ { "database.raw": "desc"}, {"_count": "desc"} ] | avg field=average')
        expected = """
                       {
                    "_source": {
                        "include": [
                            "*"
                        ]
                    },
                    "aggs": {
                        "date_histogram": {
                            "aggs": {
                                "terms": {
                                    "aggs": {
                                        "avg": {
                                            "avg": {
                                                "field": "average"
                                            }
                                        }
                                    },
                                    "terms": {
                                        "field": "database.raw",
                                        "order": [
                                            {
                                                "database.raw": "desc"
                                            },
                                            {
                                                "_count": "desc"
                                            }
                                        ]
                                    }
                                }
                            },
                            "date_histogram": {
                                "field": "@timestamp",
                                "interval": "minute"
                            }
                        }
                    },
                    "from": 0,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "query_string": {
                                        "query": "metric:ReadIOPS"
                                    }
                                },
                                {
                                    "range": {
                                        "@timestamp": {
                                            "from": "2015-12-31T22:00:00-00:00",
                                            "to": "2016-01-01T00:00:00-00:00"
                                        }
                                    }
                                }
                            ],
                            "must_not": [
                                {
                                    "query_string": {
                                        "query": ""
                                    }
                                }
                            ]
                        }
                    },
                    "size": 0
                }
        """
        self.assertEqual(tqlq['esquery'], json.loads(expected)) 

if __name__ == "__main__":
    unittest.main()
