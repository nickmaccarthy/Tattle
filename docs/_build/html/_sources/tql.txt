Tattle Query Language (TQL)
===============================

The Tattle Query Language (TQL) is a short hand syntax used for building Elasticsearh DSL queries.  

Introduction
-------------------------------
Since Elasticsearch queries can get quite long, it can make managing them for a rolling window alerting system like Tattle a bit difficult.  The Tattle Query Language aims to shorten some of these common queries into an easier read and understand syntax.

Examples
-------------------------------
Let uses NGINX logs for our example (if you are familiar with Apache access-combined logs, this will be similar as well).

Lets get a count of events that have a `status code` of 502, grouped by their respective host for the past hour. 

The Elasticsearch query will look like
::
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
                            "query": "status:502"
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "to": "now",
                                "from": "now-1h"
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
            "hostname": {
                "terms": {
                    "field": "host.raw"
                }
            }
        },
        "size": 0
    }

The TQL equivilent would be
::
    status:502 | terms name=hostname, field=host.raw

Note:  The times for these queries not handled in TQL, but instead are determined in the alert/tale.  For demo purposes, we left the times in the DSL query.

Lets break it down
------------------------------

Anything before the first ``|`` (pipe) is going to be Lucey Query Syntax.  There are many tutorials out there that can explain it much better than here, but in essance what we did was run a lucene query for any logs/events that have a ``status`` of ``502``. But just keep in mind, that any lucene query you would use in Kibana or Elasticsearch you will put here.   

To the right of our first ``|`` is our ``terms`` aggregation.  In this case we are running a ``terms`` agg on the field ``host.raw``, and we are naming that aggregation ``hostname``.  

If we ran this against our Elasticsearch cluster, we would get results similar to the following:
::
    {
        "aggregations": {
            "hostname": {
                "buckets": [
                    {
                        "key": "host1.mycompany.com",
                        "doc_count": 37
                    },
                    {
                        "key": "host2.mycompany.com",
                        "doc_count": 29
                    },
                    {
                        "key": "host3.mycompany.com",
                        "doc_count": 16
                    }
                ],
                "sum_other_doc_count": 0,
                "doc_count_error_upper_bound": 0
            }
        },
        "timed_out": false
    }

In this case we have three hosts in the ``hostname`` aggregation that have had 502 errors in the last hour, ``host1.mycompany.com`` (37 events), ``host2.mycompany.com`` (29 events), ``host3.mycompany.com`` (16 events).

Nesting
---------------------------------
Aggregations in Elasticserach can be nested, and this is the default behaviour in TQL.  You can nest as many aggregations as you with by using `|`.  

In this example, we can want to average a metric and group it by the host.  
::
    metric:DatabaseConnections | terms field=database.raw, name=DB_Name | avg field=connections, name=connection_avg

Here we used two aggregations, a `terms` and and `avg`.  The `avg` aggregation will nest below the `terms`.  Here are the aggregations for the Elasticsearch Query TQL would generate:
::
    {
        "aggs": {
            "DB_Name": {
                "terms": {
                    "field": "database.raw"
                },
                "aggs": {
                    "connection_avg": {
                        "avg": {
                            "field": "connections"
                        }
                    }
                }
            }
        },
        "size": 0
    }

Mappings
----------------------------------
Generally all of the aggregations available in Elasticsearch can be used in TQL.  Simply use the syntax ``<agg_name> <arguments>`` - example ``terms field=host.raw, name=hostname, order={ "hostname": "desc" }``, ``cardinality field=author_hash, precision_threshold=100``, ``stats field=grade``

However this rule applies all but one name, ``fields``.  The ``fields`` name is special to TQL and will display only the fields you want to see in your tale/alert.

For example, let use NGINX events.  They can have many different fields, but we might only want to see one or two fields in our alert.  We can use the `fields` argument to help with that
::
    status:502 | fields @timestamp, message

In this example we would only see two fields, the ``@timestamp`` for the event, an the ``message`` for the event. 

Read up more on Elasticsearch Aggregations here: https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html

Ordering
----------------------------------
Certain Elasticserach aggregations, such as `terms` can order your results.  You can pass along your order syntax as documented by Elasticsearch into the `order` argument
::
    ....| terms field=database.raw, name=database, order=[ { "database.raw": "desc"}, {"_count": "desc"} ]

Scripting
-----------
Like ordering, certain Elasticsearch aggs can contain `scripts` to enhance their values during search time.  Much like the `order` function, these are evaluated just like they are in the docs
::  
    .... | stats name=grades_stats, script={"inline": "_value * correction", "params": {"correction": 1.2}} 


An example deomonstrating inline scripting with the choice of language, and converting bytes to MB
::
    host.raw:app-servers* | avg name=mb_sent, script="doc['body_bytes_sent']/1024/1024", lang=expression

.. note::
    Groovy inline scripting is disabled by default in modern Elasticsearch clusters. As always, check out the scripting documentation on elastic.co for more examples: https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-scripting.html


