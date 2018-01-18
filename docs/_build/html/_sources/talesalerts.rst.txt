Alert Types
======================

Frequency
---------
Frequency alerts occur when a certain number of events ( as defined by ``relation`` and ``qty``) occur within a certain period of time.  

Here are some examples:

* "20 or more failed login events with in the past 1 hour"
Example
::
    name: "Too many login failures"
    tql_query: "\*failed login\*"
    index: "secure-log-*"
    timeperiod:
        start: "now-1h"
        end: "now"
    alert:
        type: "frequency"
        qty: 20
        relation: ">="

* "300 or more Nginx logs with an error code of 502 in the last 1 minute"
Example
::
    name: "NGINX 502 errors"
    tql_query: "status:502 | terms field=hostname"
    index: "nginx-access-*"
    timeperiod:
        start: "now-1m"
        end: "now"
    alert:
        type: "frequency"
        qty: 300
        relation: ">="

* "Less than 1000 events on all of our NGINX logs for the past 1 hour"
Example
::
    name: "Low event count on NGINX, possible log outage"
    tql_query: "*"
    index: "nginx-access-*"
    timeperiod:
        start: "now-1h"
        end: "now"
    alert:
        type: "frequency"
        qty: 1000
        relation: "le"


Regex Match
--------
Match alerts are useful for aggregation alerts.  Often times the result of an aggregtion query will result in a ``value``.  This type of alert type can use a regular expression to match the value and compare it to our ``qty`` and ``relation`` fields


