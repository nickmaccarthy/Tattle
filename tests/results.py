single_agg = """
{
    "hits": {
        "hits": [],
        "total": 19,
        "max_score": 0.0
    },
    "_shards": {
        "successful": 10,
        "failed": 0,
        "total": 10
    },
    "took": 10,
    "aggregations": {
        "queue_size": {
            "value": 138.0
        }
    },
    "timed_out": false
}
"""

nested_terms_agg = """
{
    "hits": {
        "hits": [],
        "total": 2,
        "max_score": 0.0
    },
    "_shards": {
        "successful": 5,
        "failed": 0,
        "total": 5
    },
    "took": 31,
    "aggregations": {
        "terms": {
            "buckets": [
                {
                    "avg": {
                        "value": 90.8
                    },
                    "key": "someserver1.somecompany.net",
                    "doc_count": 1
                },
                {
                    "avg": {
                        "value": 93.5
                    },
                    "key": "someserver2.somecompany.net",
                    "doc_count": 1
                }
            ],
            "sum_other_doc_count": 0,
            "doc_count_error_upper_bound": 0
        }
    },
    "timed_out": false
}
"""

tripple_nested_agg = """
{
    "hits": {
        "hits": [],
        "total": 20188,
        "max_score": 0.0
    },
    "_shards": {
        "successful": 40,
        "failed": 0,
        "total": 40
    },
    "took": 207,
    "aggregations": {
        "events_by_day": {
            "buckets": [
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 616
                            },
                            {
                                "avg": {
                                    "value": 93.0860162601628
                                },
                                "key": "rep-wpstaging1.somecompany.com",
                                "doc_count": 615
                            },
                            {
                                "avg": {
                                    "value": 99.70000000000016
                                },
                                "key": "stage-app1.or.somecompany.net",
                                "doc_count": 610
                            },
                            {
                                "avg": {
                                    "value": 92.38048780487807
                                },
                                "key": "searchindexer2.somecompany.com",
                                "doc_count": 123
                            },
                            {
                                "avg": {
                                    "value": 92.575
                                },
                                "key": "queryservicec1.somecompany.com",
                                "doc_count": 12
                            },
                            {
                                "avg": {
                                    "value": 92.17142857142858
                                },
                                "key": "queryservicec2.somecompany.com",
                                "doc_count": 7
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-16T00:00:00.000Z",
                    "key": 1463356800000,
                    "doc_count": 1983
                },
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 93.36074906367071
                                },
                                "key": "rep-wpstaging1.somecompany.com",
                                "doc_count": 1335
                            },
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 1335
                            },
                            {
                                "avg": {
                                    "value": 99.68317843866208
                                },
                                "key": "stage-app1.or.somecompany.net",
                                "doc_count": 1076
                            },
                            {
                                "avg": {
                                    "value": 90.1
                                },
                                "key": "autosuggestb2.somecompany.com",
                                "doc_count": 1
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-17T00:00:00.000Z",
                    "key": 1463443200000,
                    "doc_count": 3747
                },
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 1326
                            },
                            {
                                "avg": {
                                    "value": 92.26876475216335
                                },
                                "key": "rep-wpstaging1.somecompany.com",
                                "doc_count": 1271
                            },
                            {
                                "avg": {
                                    "value": 90.4
                                },
                                "key": "autosuggestb2.somecompany.com",
                                "doc_count": 1
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-18T00:00:00.000Z",
                    "key": 1463529600000,
                    "doc_count": 2598
                },
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 91.1960269865068
                                },
                                "key": "rep-wpstaging1.somecompany.com",
                                "doc_count": 1334
                            },
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 1334
                            },
                            {
                                "avg": {
                                    "value": 90.16666666666667
                                },
                                "key": "autosuggestb2.somecompany.com",
                                "doc_count": 3
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-19T00:00:00.000Z",
                    "key": 1463616000000,
                    "doc_count": 2671
                },
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 1334
                            },
                            {
                                "avg": {
                                    "value": 92.56889908256882
                                },
                                "key": "rep-wpstaging1.somecompany.com",
                                "doc_count": 1090
                            },
                            {
                                "avg": {
                                    "value": 90.5888888888889
                                },
                                "key": "autosuggestb2.somecompany.com",
                                "doc_count": 9
                            },
                            {
                                "avg": {
                                    "value": 90.3
                                },
                                "key": "queryserviceb2.somecompany.com",
                                "doc_count": 3
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-20T00:00:00.000Z",
                    "key": 1463702400000,
                    "doc_count": 2436
                },
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 1338
                            },
                            {
                                "avg": {
                                    "value": 91.78739903069456
                                },
                                "key": "queryserviceb2.somecompany.com",
                                "doc_count": 619
                            },
                            {
                                "avg": {
                                    "value": 90.56511627906976
                                },
                                "key": "autosuggestb2.somecompany.com",
                                "doc_count": 43
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-21T00:00:00.000Z",
                    "key": 1463788800000,
                    "doc_count": 2000
                },
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 1338
                            },
                            {
                                "avg": {
                                    "value": 90.36691842900312
                                },
                                "key": "autosuggestb2.somecompany.com",
                                "doc_count": 1324
                            },
                            {
                                "avg": {
                                    "value": 91.82961309523799
                                },
                                "key": "queryserviceb2.somecompany.com",
                                "doc_count": 672
                            },
                            {
                                "avg": {
                                    "value": 90.1
                                },
                                "key": "autosuggestb1.somecompany.com",
                                "doc_count": 1
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-22T00:00:00.000Z",
                    "key": 1463875200000,
                    "doc_count": 3335
                },
                {
                    "terms": {
                        "buckets": [
                            {
                                "avg": {
                                    "value": 90.86129943502814
                                },
                                "key": "autosuggestb2.somecompany.com",
                                "doc_count": 708
                            },
                            {
                                "avg": {
                                    "value": 93.5
                                },
                                "key": "stage-queryserviceb2.somecompany.com",
                                "doc_count": 708
                            },
                            {
                                "avg": {
                                    "value": 90.85
                                },
                                "key": "autosuggestb1.somecompany.com",
                                "doc_count": 2
                            }
                        ],
                        "sum_other_doc_count": 0,
                        "doc_count_error_upper_bound": 0
                    },
                    "key_as_string": "2016-05-23T00:00:00.000Z",
                    "key": 1463961600000,
                    "doc_count": 1418
                }
            ]
        }
    },
    "timed_out": false
}
"""
