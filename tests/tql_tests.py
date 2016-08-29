import sys
import os
import re
import datetime
import time
import yaml
import json
from pprint import pprint

TATTLE_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['TATTLE_HOME'] = str(TATTLE_HOME)

sys.path.append(os.path.join(TATTLE_HOME, 'lib'))
sys.path.append(os.path.join(TATTLE_HOME))
sys.path.append(os.path.join('.'))

import unittest

from elasticsearch import Elasticsearch
import pandas as pd

import tattle
import tattle.workers
import tattle.config
from tattle.search import Search
from tattle.result import results_to_df
from tattle.utils import EventQueue


s = Search()

class TestTQL(unittest.TestCase):

    def tql_query(self, query, index='logstash-*', start='2016-01-01||-2h', end='2016-01-01'):
        try:
            ourq = s.tql_query(query, index=index, start=start, end=end)
            return ourq
        except Exception as e:
            raise Exception("Unable to run TQL query, reason: {}".format(e))
   

    def testIndexPattern(self):
        """ tests to make sure we have the correct index pattern """
        indexes = self.tql_query('foobarbaz', index='logstash-*', start='2016-01-01||-3d', end='2016-01-01')
        expected = "logstash-2015.12.29,logstash-2015.12.30,logstash-2015.12.31,logstash-2016.01.01" 
        self.assertEqual(indexes['search_indexes'], expected) 


    def testLuceneQueryNoAggs(self):
        """ test just a lucene query """
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
        """ tests fields """
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
        """ tests a single agg """
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
        """ tests orders """
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

    def testScriptOne(self):
        """ tests scripting """
        tqlq = self.tql_query('* | stats name=grades_stats, script={"inline": "_value * correction", "params": {"correction": 1.2}}')
        expected = """
            {
                "query": {
                    "bool": {
                        "must_not": [
                            {
                                "query_string": {
                                    "query": ""
                                }
                            }
                        ],
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
                        ]
                    }
                },
                "_source": {
                    "include": [
                        "*"
                    ]
                },
                "from": 0,
                "aggs": {
                    "grades_stats": {
                        "stats": {
                            "script": {
                                "inline": "_value * correction",
                                "params": {
                                    "correction": 1.2
                                }
                            }
                        }
                    }
                },
                "size": 0
            }
        """
        self.assertEqual(tqlq['esquery'], json.loads(expected)) 
        
    def testSingleAggResults(self):
        from results import single_agg
        results = json.loads(single_agg)
        buckets = tattle.find_in_dict(results, 'buckets')

        self.assertFalse(buckets)
        self.assertTrue(isinstance(results, dict))

    def testDoubleBucketedAgg(self):
        from results import tripple_nested_agg, nested_terms_agg
        r1 = json.loads(nested_terms_agg)
        r2 = json.loads(tripple_nested_agg)
        
        q = EventQueue(results=r1)
        q2 = EventQueue(results=r2)

        self.assertTrue(tattle.find_in_dict(r1, 'buckets'))
        self.assertTrue(tattle.find_in_dict(r2, 'buckets'))
        
        r1key = list(q.results_aggs.keys())[0]
        r2key = list(q2.results_aggs.keys())[0]

        rdf1 = results_to_df(q.results_aggs[r1key]['buckets'])
        rdf2 = results_to_df(q2.results_aggs[r2key]['buckets'])

        self.assertTrue(isinstance(rdf1, pd.DataFrame))
        self.assertTrue(isinstance(rdf2, pd.DataFrame)) 


if __name__ == "__main__":
    unittest.main()
