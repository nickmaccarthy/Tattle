Actions
=======

Actions are what is taken after the Tale has met its alert threshold.

You can also have multiple actions per Tale. In our example Tale, you can we have two actions configured, one to send Emails, and one to send the alerts to Pager Duty as well.


Email
-----

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

Pager Duty
----------

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


