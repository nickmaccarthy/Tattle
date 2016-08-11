Tale Definitions
=================

name
----
name
~~~~
    * Required: `Yes`
    * Description: Name of the alert
Example:
::
    name: "Disk Usage >= 90%"``

description
-----------
description
~~~~~~~~~~~
    * Required: `Yes`
    * Description: A brief description of the tale.  
Example:
::
    description: "The disk usage on the server >= 90% on the root filesystem``

severity
--------
severity
~~~~~~~~
    * Required: `No`
    * Description: The severity of the alert.  This is a string, and can be whatever you want.  1-5, Low-Crit, etc
Example:
::
    severity: "High"

disabled
--------
disabled
~~~~~~~~
    * Required: `Yes`
    * Description: Whteher this Tale is enabled (0) or disabled (1)
Example: 
::
    # This alert is enabled, i.e. its NOT disabled
    disabled: 0
    # This alert is disabled
    disabled: 1
    # You can even use strings
    disabled: "yes"
    # Or True and False Statements
    disabled: true

tql_query
---------
tql_query
~~~~~~~~~
    * Required: `Yes`
    * Description: The TQL query for the Tale.  See the TQL section for more details
Example:
::    
    tql_query: "summary.fullest_disk:>=90 | terms name=server, field=host.raw | avg name=fullest_disk, field=summary.fullest_disk"

index
-----
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
----------
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
-----
type 
~~~~
    * Required: `Yes`
    * Description: The type of the alert
    * Values
        * ``frequency`` 
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
        * '``gt``, ``>`` - Greater Than
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

return_matches:
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
------

