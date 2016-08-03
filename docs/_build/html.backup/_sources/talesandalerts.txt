
Tales & Alerts
----------------
Tales are the heart and soul of what makes Tattle work.  Tales are definitions for what should qualify the alert, and what actions to take once we have a true positive.  

Here is an example Tale

Example
::
    name: "Disk Usage over 90 %"
    description: "Disk Usage High on a host or series of hosts"
    severity: "High"
    tql_query: "summary.fullest_disk:>=90 | terms name=server, field=host.raw | avg name=fullest_disk, field=summary.fullest_disk"
    index: "system-metrics-*"
    disabled: 0
    timeperiod:
        start: "now-1h"
        end: "now"
    alert:
        type: "frequency"
        relation: "gt"
        qty: 0
        realert: "10s"
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
            to: 'my_email@company.com'

In the above example, you will notice the ``tql_query`` config option.  This is a short hand query syntax that Tattle uses to create the Elasticsearch DSL Query with Aggregation support.  The first part (before the first ``|``) is straight Lucene syntax.  You are probably familiar with this if you have ever used Kibana or worked with Lucene before.  The parts after the first ``|`` are aggregations in shorthand.
You will notice there are two aggregations in this query.  The ``|``'s denote these will be nested aggregations.  The ``terms`` query will run before the ``avg`` query.  

Next you will notice the timeperiod section.  This section denotes the start and end time for the 'rolling' windows this alert will utilize.  In this case, the window for this search will be whatever time 'now' is, minus 1 hour, and the end time for the query will be 'now'.
Then we have the alert type.  In this case it is ``freqeuency`` which means that if we have a 'number_of_events' beyond our threshold, then we will use this to trigger our ``action`` below.  The thresholds in this case are a 'number_of_events' that are ``greater than or equal to`` to ``10`` in the last ``1 hour`` ( ``now-1h`` ).
Next up is the ``action``.  If our alert has triggered has met its threshold, the next thing to do is do something about it.  In this case we have two actions, one is to send the alert to PagerDuty, the second is to email us.
For more information about the setup of an alert, please see the alerts section.

Please be sure to check out the Tales & Alerts section for more information on creating and configuring Tales.
