Tales, Alerts and Actions
==========================

Introduction
------------
Tales are the heart and soul of the system.  Tales are definitions for alerts and define such things as our time window for the events we seek, what query will run, thresholds, actions to take, etc. 


.. note::
    Tales are  kept in `yaml` files in ``$TATTLE_HOME/etc/tattle/tales``, ``$TATTLE_HOME/etc/tales`` or in ``$TATTLE_HOME/etc/alerts``. 

To understand `Tales`, lets take a look at an example below.  Please note, we will use this as a reference for the rest of the Tales documentation.

Example Tales
-------------

In this example, we will be finding all hosts in our environment that have a disk usage of `greater than or equal` to `90%` for the past `1 hour`.  When a match is found, it will send us an alert via Pagerduty as well as an email for each `key` ( host in this case ) that was matched.

TQL Query with multiple aggregations and multiple actions example
::
    name: "Disk Usage over 90 %"
    description: "Disk Usage High on a host or series of hosts"
    severity: "High"
    tql_query: "summary.fullest_disk:>=90 | terms name=server, field=host.raw | avg name=fullest_disk, field=summary.fullest_disk"
    index: "system-metrics-*"
    enabled: 1
    timeperiod:
        start: "now-1h"
        end: "now"
    alert:
        type: "frequency"
        relation: "gt"
        qty: 0
        realert: "4h"
        return_matches:
            length: 10
            random: true
    action:
        pagerduty:
            enabled: 1
            service_key: "TattleAlerts"
            once_per_match:
                match_key: "key"

        email:
            enabled: 1
            once_per_match: 
                match_key: "key"
            to: 
                - 'my_email@company.com'
                - 'alerts@company.com'

For more breakdown on this Tale, lets look at the :ref:`tales-definitions` section. 

.. _tales-definitions:

Tale Definitions
-----------------
name
~~~~
    * Required: `Yes`
    * Description: Name of the alert
Example:
::
    name: "Disk Usage >= 90%"``

description
~~~~~~~~~~~
    * Required: `Yes`
    * Description: A brief description of the tale.  
Example:
::
    description: "The disk usage on the server >= 90% on the root filesystem``

severity
~~~~~~~~
    * Required: `No`
    * Description: The severity of the alert.  This is a string, and can be whatever you want.  1-5, Low-Crit, etc
Example:
::
    severity: "High"

enabled
~~~~~~~~
    * Required: `Yes`
    * Description: Whteher this Tale is enabled (1)(True) or disabled (0)(False)
Example: 
::
    # This alert is enabled
    enabled: 1
    # This alert is disabled
    enabled: 0
    # You can even use strings
    enabled: "yes"
    # Or True and False Statements
    enabled: true

disabled
~~~~~~~~~~
    * Required: `Yes` but only if you didnt specify an ``enabled``
    * Description:  The same thing as as ``enabled`` above, but with opposite logic.  Tattle used to use the term ``disabled`` instead of ``enabled``, but this old method is left in for legacy support.  Please use the ``enabled`` term going forward with new Tales.
Example:
::  
    # This alert is enabled, not disabled
    disabled: 0
    # this alert is disabled
    disabled: 1


tql_query
~~~~~~~~~
    * Required: `Yes`
    * Description: The TQL query for the Tale.  See the :doc:`tql` page for more details on TQL
Example:
::    
    tql_query: "summary.fullest_disk:>=90 | terms name=server, field=host.raw | avg name=fullest_disk, field=summary.fullest_disk"

index
~~~~~
    * Required `Yes`
    * Description: The index pattern where you the events you are searching reside.  Default is ``logstash-*``
    * More information:  
        * Currently Tattle expects your indexes to be in daily format ``YYYY.MM.DD`` which is pretty standard/common.  The ``*`` at the end of the index name tells Tattle to figure out which indexes to search against based on the timeperiod.  Lets use the example of ``now-1h`` as our start time, and assume our current time is ``2016/02/02 00:01:00``; when Tattle runs it will actually search against two indexes:  ``system-metrics-2016.02.02`` and ``system-metrics-2016.02.01`` since ``-1h`` from now would have technically been yesterday.
        * If you do not specify a ``*`` Tattle will use just that index name, with no time
        * In the future we plan to add the definition of index pattern
Example:
::
    index: "system-metrics-*

timeperiod
~~~~~~~~~~
    * ``start``, ``end``
    * Required: `Yes`
    * Description: The timeperiod for events this Tale searches for.  This is a rolling window using python-datemath as our start and end times.  
    * More information:
        * More documentation on python-datemath can be found here: https://github.com/nickmaccarthy/python-datemath    
Example:
::
    timeperiod:
        # The start of our alert window
        start: 'now-1h'
        # The end of our alert window
        end: 'now'

alert
~~~~~
type 
~~~~
    * Required: `Yes`
    * Description: The type of the alert
    * Values
        * ``frequency`` or ``number_of_events``
            * Description: If the `number of events` meets our ``relation`` and ``qty``
        * ``agg_match``
            * Description: If our value meets a regular expression match of something
relation
~~~~~~~~
    * Required: `Yes`
    * Description: If our event count meets our relation, then the alert should fire
    * Values
        * ``eq``, ``=`` - Equal To
        * ``ne``, ``!=`` - Not Equal To
        * ``lt``, ``<`` - Less Than
        * ``gt``, ``>`` - Greater Than
        * ``le``, ``<=`` - Less Than or Equal To
        * ``ge``, ``>=`` - Greater Than or Equal To

qty
~~~
    * Required: `Yes`
    * Description: What we compare our ``relation`` to
Example":
::
    ## If our number of events is greater than or equal to 10, then we should alert
    relation: ">="
    qty: 10

realert
~~~~~~~
    * Required: `Yes`
    * Description:  How long Tattle will wait before it will re-alert on this Tale.  If Tattle is still finding matches for this Tale, but we are within the re-alert threshold, then Tattle will not alert.
    * Notes: 
        * Every time Tattle fires an alert, it stores it in the Tattle index in Elasticserach ( default is ``tattle-int`` ).  When the Tale gets loaded, one of the first thing it does it check to see when the last time this Tale fired.  It then compares the last time to the realert threshold, diffs the two and if we are beyone our re-alert threshold, then Tattle will re-fire the Tale.
        * It uses simple datemath like so:
            * ``1h``
            * ``2m``
            * ``3d``
Example:
::
    # Don't alert us to this again for 1 hour
    realert: "1h"

return_matches
~~~~~~~~~~~~~~
    * Required: `Yes`
    * Description:  If Tattle should return the matches it found.  It will return those matches in whatever action you have configured
    * Notes:
        * Sometimes you can get many matches ( hundreds or thousands for example ).  With the ``random: True`` or ``length: 10`` stanzas Tattle can return a randam sample of ``10`` results
Example:
::
    # Assuming we could get hundreds of matches back
    return_matches:
        # Return back a random sample of 20 results 
        random: true
        length: 20

action
~~~~~~


Alert Types
------------
Frequency
~~~~~~~~~
Frequency alerts occur when a certain number of events ( as defined by ``relation`` and ``qty``) occur within a certain period of time.  

Here are some examples:

* "20 or more failed login events with in the past 1 hour"
Example
::
    name: "Too many login failures"
    tql_query: '"failed login"'
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


Aggregation Match
~~~~~~~~~~~~~~~~~~
Agg Match alerts are useful for aggregation based alerts where the keys and values can change depending on your data.  Often times the result of most metric based aggregtions will a field called ``value``.  This type of alert type can use a regular expression to match the value and compare it to our ``qty`` and ``relation`` fields

When you use an agg_match, Tattle will flatten the aggregation returned so it can be iterated against and matched by a regular expression.

Take this example a return 
::
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

Tattle would flatten the aggregations section this to
::
    aggregations.terms.buckets.0.avg.value = 90.8
    aggregations.terms.buckets.0.key = someserver1.somecompany.net
    aggregations.terms.buckets.1.avg.value = 93.5
    aggregations.terms.buckets.1.key = someserver2.somecompany.net


So if we wanted to look for any `values` in our aggs that are ``>= 90`` we would use the regular expression ``^.value$`` as our match key.  

Some examples

Basic example where we look for any `value` that is ``>=`` `90`
::
    alert:
        type: "agg_match"
        field: '^.*value$'
        relation: ">="
        qty: 90

Or if we wanted to only look at only the first bucket, for a value ``>= 20``
::
    alert:
        type: "agg_match"
        field: '^\.buckets\.0.*value$'
        relation: ">="
        qty: 20


Alert Actions
-------------
Actions are what is taken after the Tale has met its alert threshold.

You can also have multiple actions per Tale. In our example Tale, you can we have two actions configured, one to send Emails, and one to send the alerts to Pager Duty as well.


Email
~~~~~

Probably the most common alert action.  Tattle sends a formatted, HTML email to recipient(s)

The email server properties are stored in ``$TATTLE_HOME/etc/tattle/tattle.yaml``, so please set that up first before you proceed with email alerts

Tale Examples:
    
Example 
::
    action:
        email:
            # We can enable or disable this action with this flag
            enabled: 1
            # Who the email should go to
            to: [ 'alerts@company.com', 'manager@company.com' ]
            # If we should send a sperate email for every match.  If this is not set, then the all of the results are sent in one email
            once_per_match:
                # The match key, is the part of the result we use our primary key for sperating the results in seperate emails
                # In this case its "key" since its the key of the aggregation.  In our case this will be the hostname
                # If we had 4 hosts that matched then we would have 4 seperate emails.  Tattle will append the 'match_key' to the subject of the email as well
                match_key: "key"

If you want to change the HTML for the email, add company logos etc, you can change the templates directly in ``$TATTLE_HOME/use/share/templates/html/email.html``

Script
~~~~~~~~~~

The ``script`` alert action allows you to specify a script to run when the alert is fired/triggerd.  When Tattle fires off the script, it passes in the results from the alert, the Tale definition, and the TQL query intentions for use within the script.

When the script is called, three arguments are passed in to, each argument will contain JSON as its data.

Arguments
    * ``$1`` - The results, or matches from the alert
    * ``$2`` - The Tale details that was responsible for triggering this alert
    * ``$3`` - The TQL Query intentions

Your script must be in ``$TATTLE_HOME/bin/scripts`` and must be executable.

.. note::
    The script will run as whatever user Tattle runs as.  For example if you run Tattle under a user called `tattle`, then the script will run as the user `tattle`. 
    
Here is an example script that will echo out each of the ARGV's
::
    #!/bin/bash
    echo 'RESULTS:'
    echo $1

    echo 'TALE:'
    echo $2

    echo 'INTENTIONS:'
    echo $3


Pager Duty
~~~~~~~~~~

Another very common use for Tattle is to send its alert direclty to Pager Duty.  

Pager Duty alerts can be setup to Service Key, as defined in Pager Duty itself.  The service Key definitions can be stored in the ``$TATTLE_HOME/etc/tattle/pagerduty.yaml`` and can be referenced in the action by thier title.

Example ``$TATTLEHOME/etc/tattle/pagerduty.yaml``
::
    TattleAlerts:
        service_key: "<service key>"
    DataSystems:
        service_key: "<service_key>"
    WebSystem:
        service_key: "<service_key>"

Example Tale action
::
    action:
        pagerduty:
            # We can enable or disable this action here
            enabled: 1
            # The name of the service key to use, as defined in pagerduty.yaml
            service_key: "TattleAlerts"
            # If we should compile seperate pagerduty alerts for each match.  If this is not set, then the all of the results are sent in one PD alert
            once_per_match:
                # The match key, is the part of the result we use our primary key for sperating the results in seperate PD alerts
                # In this case its "key" since its the key of the aggregation.  In our case this will be the hostname
                # If we had 4 hosts that matched then we would have 4 seperate Pagerduty alerts.  Tattle will append the 'match_key' to the subject of the Pagerduty alert as well
                match_key: "key"

Multiple Tales
---------------

Its often useful to group Tales by their purpose.  For example, you might want to group your `Nginx Access` Tales together, your `Nginx Error` Tales sperately, and your `Securelog` Tales together.  Lets say we have 20 differnt `Nginx` Tales, and 10 different `Securelog` Tales; that would mean we would have have at least 30 seperate `Tale` ``.yaml`` files in our ``$TATTLE_HOME/etc/tales`` directory.  As you can imagine, the more you use Tattle, the more unwieldy this can get.
 

Luckily Tattle allows you to define multiple Tales in one ``.yaml`` file to alleviate this issue.  Using the example below, you can see how we grouped two `Nginx` Tales into one file.  There can be as many Tales as you want this one in one ``yaml`` file.

Syntax
~~~~~~~

multi_tale_example.yaml
::  
    tales:
        -
            <tale #1>
        -
            <tale #2>
        -
            <tale #3>


Example Multi Tale
~~~~~~~~~~~~~~~~~~~

Example for NGINX logs
::
    tales:
        # Tale 1
        -
            name: "NGINX 502 Spike"
            description: "A high number of 501's have occured in our NGINX logs"
            severity: "Criticial"
            tql_query: "status:502"
            index: "nginx-access-*"
            enabled: 1
            schedule_interval: "1m"
            timeperiod:
                start: "now-1m"
                end: "now"
            alert:
                type: "frequency"
                relation: "ge"
                qty: 10 
                realert: "15m"
                return_matches: false
            action: 
                email:
                    enabled: 1
                    to: 'alerts@mycompany.com'

        # Tale 2
        -
            name: "NGINX 404 Spike"
            description: "A high number of 404's have occured in our NGINX logs"
            severity: "Medium"
            tql_query: "status:404"
            index: "nginx-access-*"
            enabled: 1
            schedule_interval: "1m"
            timeperiod:
                start: "now-1m"
                end: "now"
            alert:
                type: "frequency"
                relation: "ge"
                qty: 400 
                realert: "15m"
                return_matches: false
            action: 
                email:
                    enabled: 1
                    to: 'alerts@mycompany.com'
                pagerduty:
                    enabled: 1
                    service_key: "TattleAlerts"
                    once_per_match:
                        match_key: "key" 


