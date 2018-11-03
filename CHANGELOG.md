# Changelog

### v.1.0.13 - 2018-11-03
* Added channel aliasing for MS Teams.  A user can specify team channel aliases (in msteams.yml) for differnt webhook urls.  The user can then reference these alias in a list in their msteams alert action to send the alert to multiple MS Teams Channels
* Added the abilty for the `exclude` option for queries to be a list.  This should help clean up Tales a bit for those that have lots of exclusions

### v.1.0.12 - 2018-08-22
* Fixed cron schduler/logic 

### v.1.0.11 - 2018-01-17
* Added MS Teams Support for Alerting

### v.1.0.10 - 2017-01-24
* Allows slack to have defaults ( webhook, channel, etc ) to eliniate tale clutter.  See docs for more info.

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

