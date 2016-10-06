# Changelog

### v1.0.7 - 2016-10-06
* Better logic for handling script style in TQL. For example `percentile field=status percents=[85,99, 99.9]` should be evaluated correctly.  

### v1.0.6 - 2016.09.21
* Slack alerting/intergration.  There is not an alert action for alerting to a Slack channel
* Kibana Dashboards.  If you use Kibana 4 for dashbaord, you can link your dashboard certain alert actions ( email, pagerduty and slack for now ), and Tattle will provide a link to the dashboard with a timefilter based on the times the alert was triggers

### v1.0.5 - 2016.09.12
* Support for Environment variables in setting $TATTLE_TALES and $TATTLE_CONFIG_DIR directories. More information available in documentation at tattle.io

### v1.0.4 - 2016.09.5
* Added a schedule, in cron format.  Just like the exclude_schedule in v1.0.3, but specifies when the Tale should run instead
* Adjusted better logging for debug events in tattle.workers.tnd
* Code cleanup ( removed, older commented code no longer needed ) 

### v1.0.3 - 2016.08.29
* Added exclude_schedule to exclude a Tale during a specified cron window.  For example, if you dont want a Tale to run between the hours of 2am and 8am every saturday, you could specify this cron string:  '* 2-8 * sat *'

### v1.0.2 - 2016.08.18
* Added index patterns.  Allows user to speicfy interval and index pattern for Tattle to search against.  See Tales section of the documentation for more details

### v1.0.1 - 2016.08.17
* Added support for python 3.3+

### v1.0 
* First version deployed

