import sys
import os
import datetime
import time
import calendar
import dateutil
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch
import tattle
import tattle.config
from tattle.exceptions import ConfigException
import re
import json
import operator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader 
import urllib
import arrow
import simplejson

tcfg = tattle.config.load_configs().get('tattle')

from pprint import pprint

import requests
from requests.exceptions import RequestException

logger = tattle.get_logger('alert')

TATTLE_HOME = os.environ['TATTLE_HOME']

class AlertException(Exception):
    pass

class AlertBase(object):
    """ 
        Base class for types of alerts
    """
    def __init__(self, **kwargs):
        self.event_queue = None
        self.title = None
        for k,v in kwargs.items():
            setattr(self, k, v)
        if not self.event_queue:
            raise AlertException("Alerts require an EventQueue")
        self.eq = self.event_queue
        self.matches = self.eq.matches
        self.intentions = self.eq.intentions
        self.alert = self.eq.alert
        self.set_title()

        self.client_url = kwargs.get('client_url') 
        self.url = kwargs.get('url')
        # Create a link to a kibana dashboard with the times for our alert
        self.kibana4_dashboard = kwargs.get('kibana4_dashboard') or kwargs.get('kibana_dashboard')
        if self.kibana4_dashboard is not None:
            dash = self.kibana4_dashboard 
            dash_time_settings = "(refreshInterval:(display:Off,pause:!f,value:0),time:(from:'{start_time}',mode:absolute,to:'{end_time}'))".format(start_time=self.intentions['_start_time_iso_str'], end_time=self.intentions['_end_time_iso_str'])
            dash_time_settings = urllib.quote(dash_time_settings)
            self.kibana_dashboard = "{dash}?_g={time_settings}".format(dash=dash, time_settings=dash_time_settings) 
        else:
            self.kibana_dashboard = None

        self.trigger_reason = self.set_trigger_reason()

        self.firemsg = 'FireMSG Not Set for {}'.format(self.alert.get('name'))


    def fire(self, **kwargs):
        raise NotImplementedError()

    def fire_per_match(self, **kwargs):
        raise NotImplementedError()
               
    def set_title(self):
        if self.title:
            self.title = self.title
        #elif self.alert['alert'].has_key('title'):
        if 'title' in self.alert['alert']:
            self.title = self.alert['alert']['title']
        #elif self.alert.has_key('name'):
        elif 'name' in self.alert:
            self.title = self.alert['name']
        else:
            self.title = "Not Defined"

    def set_trigger_reason(self):
        if self.alert['alert'].get('type') == 'agg_match':
            reason = 'Because {} field {} was {} to {}'.format(self.alert['alert']['type'], self.alert['alert']['field'], self.alert['alert'].get('relation').upper(), self.alert['alert'].get('qty'))
        else:
            reason = 'Because {} was {} to {}'.format(self.alert['alert'].get('type'), self.alert['alert'].get('relation').upper(), self.alert['alert'].get('qty'))
        return reason
    
    def create_alert_body(self, matches):
        body = '\n----------------------------------------\n'
        for match in matches:
            body += match
        body += '\n---------------------------------------\n'
        return body

 
    def __repr__(self):
       return "<AlertClass: %s - Name: %s>" % ( self.__class__.__name__,  self.alert['name'] )
            
    
class PprintAlert(AlertBase):
    def __init__(self, **kwargs):
        super(PprintAlert, self).__init__(**kwargs)
    
    def fire(self):
        self.run()

    def run(self):
        tattle.pprint(vars(self.eq))
        print("\n\n")
        print("-======= PPRINTED ALERT: =======-")
        print("TITLE: {}".format(self.title))
        print("alert defiition:")
        tattle.pprint(self.eq.alert)
        print("alert matches:")
        tattle.pprint(self.matches)
        print("results total:")
        print(self.eq.count('matches'))
        print("event queue:")
        print(tattle.pprint(vars(self.eq)))
        print("-====== END ALERT ======-")
        print("\n\n")

        self.firemsg = """msg="{}", tale_name="{}", title="{}" """.format("PPrint Alert Fired", self.alert.get('name'), self.title)


class EmailAlert(AlertBase):
    
    def __init__(self, **kwargs):
        super(EmailAlert, self).__init__(**kwargs)

        self.mailcfg = tattle.config.load_configs().get('email')

        if self.mailcfg is None:
            raise ConfigException("Unable to load the email config.  Does it exist at $TATTLE_HOME/etc/tattle/email.yml?")

        #self.subject = None
        self.subject = self.title
        self.cc = None
        self.bcc = None

        for k,v in self.alert['action']['email'].items():
            if k == 'enabled': continue
            setattr(self, k, v)

        self.sender = kwargs.get('sender', self.mailcfg['default_sender'])
        # sets our email subject

        #self.subject_prefix = self.mailcfg.get('subject_prefix', '')

        #if not self.subject:
        #    self.set_subject(**kwargs)

        self.client_url = self.kibana_dashboard or self.client_url or self.url

    def connect(self):
        try:
            self.server = smtplib.SMTP(self.mailcfg.get('host','localhost'), self.mailcfg.get('port', 25))
        except Exception as e:
            logger.exception("Unable to connect to SMTP server: reason: %s, mailcfg: %s" % (e,self.mailcfg))

    def build_msg(self):
        self.email_body = self.make_email_body()

        self.msg = MIMEText(self.email_body, 'html')
        self.msg['Subject'] = self.subject
        self.msg['From'] = self.sender
        if not isinstance(self.to, list):
            self.to = [self.to]
        self.msg['To'] = ','.join(self.to)
        if self.cc:
            self.msg['cc'] = self.cc
        if self.bcc:
            self.msg['bcc'] = self.bcc


    def fire(self):
        self.connect()
        #self.subject = "{prefix}{subject}".format(prefix=self.subject_prefix, subject=self.subject)
        self.subject = self.title
        self.build_msg()
        self.send_email()
        self.firemsg = """msg="{0}", email_to="{1}", tale_name="{2}", subject="{3}" """.format("Email Sent", self.to, self.alert.get('name'), self.subject)

    def send_email(self):
            try: 
                self.server.sendmail(self.sender, self.to, self.msg.as_string())
                self.server.quit()
            except Exception as e:
                logger.exception("Unable to send email, reason: {}".format(e))

    def set_subject(self, **kwargs):
        if 'subject' in self.alert['action']['email']:
            self.subject = self.alert['alert']['email']['subject']
        else: 
            self.subject = self.title

    def make_email_body(self):
        template_dir = os.path.join(TATTLE_HOME, 'usr', 'share', 'templates', 'html')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('email.html')

        # convert a single dict into a list, so it can be built with dict_to_html_table()
        if isinstance(self.matches, dict):
            self.matches = [ self.matches ]

        if isinstance(self.matches, list):
            results_table = tattle.dict_to_html_table(self.matches)
        elif isinstance(self.matches, str):
            results_table = self.matches
        else:
            results_table = "No results found"

        try:
            rendered_html = template.render(ainfo=self.alert, results=self.matches, intentions=self.intentions, results_table=results_table, eq=self.eq, client_url=self.client_url)
            return rendered_html
        except Exception as e:
            log_msg = "Unable to render email template. <br /><b>Reason: </b>{}</br />".format(e)
            logger.exception(log_msg)
            return log_msg


class IntentionsJSONEncoder(json.JSONEncoder):
   
    import elasticsearch_dsl
    import arrow 
    def default(self, obj):
        if isinstance(obj, arrow.Arrow):
            return obj.format('YYYY-MM-DD HH:mm:ss ZZ')
        elif isinstance(obj, object):
            return 'cant_serialize_object'
        return json.JSONEncoder.default(self, obj)

class ScriptAlert(AlertBase):

    def __init__(self, **kwargs):
        super(ScriptAlert, self).__init__(**kwargs)
        self.script_name = kwargs.get('filename') or kwargs.get('script_name') or kwargs.get('name')

        if not self.script_name:
            logger.error("Not able to find script name, please specify it with 'filename' in the action arguments")
            return

    def fire(self):
        try:
            tattle.run_script(self.script_name, json.dumps(self.matches), json.dumps(self.alert), json.dumps(self.intentions, cls=IntentionsJSONEncoder)) 
        except Exception as e:
            logger.exception('Unable to run script: %s, reason: %s'.format(self.script_name, e))

        self.firemsg = """msg="{}", tale_name="{}", script_name="{}" """.format("Script Alert Fired", self.alert.get('name'), self.script_name)
        
        
class PagerdutyAlert(AlertBase):
    
    def __init__(self, **action):
        super(PagerdutyAlert, self).__init__(**action)

        self.service_name = action.get('service_name') or action.get('service_key')
        if not self.service_name:
            logger.error('Service name was not set for pagerduty alert, cannot continue with this alert method. ')
            return

        self.pdcfg = tattle.config.load_configs().get('pagerduty')
        if self.pdcfg is None:
            raise ConfigException("Unable to load the pagerduty config. Does the pagerduty.yaml exist in $TATTLE_HOME/etc/tattle/pagerduty.yml?")


        # Find our config options based on our service name
        cfg = self.get_service_args(self.service_name)

        if not cfg:
            msg = "Unable to find PagerDuty config for: {}, cannot continue.".format(service_name)
            logger.exception(msg)   
            raise Exception(msg)
       
        self.pagerduty_service_key = cfg.get('service_key')
        self.pagerduty_client_name = cfg.get('client_name', 'Tattle')

        self.url = 'https://events.pagerduty.com/generic/2010-04-15/create_event.json'

        self.title = "Tattle - {}".format(self.title)

        self.client_url = self.kibana_dashboard or action.get('client_url', '') or action.get('view_in', '')

    def get_service_args(self, key):
        for k,args in self.pdcfg.items():
            if key in k:
                #return { k:args }
                return args

    def make_body(self):
        fd = tattle.utils.FlattenDict()
        fd.kibana_nested = True
        body = [ '\n-----------------\n']
        body.append('Alert Info:\n')
        #body.append(fd.flatten_dict(self.alert))
        alertd = fd.flatten_dict(self.alert)
        tattle.pprint(alertd)
        for k,v in alertd.items():
            body.append('{}: {}'.format(k,v))
        body.append('\n')
        body.append('Matches:\n')
        matchd = fd.flatten_dict(self.matches)
        for k,v in matchd.items():
            body.append('{}: {}'.format(k,v))
        body.append('\n')
        body.append('\n-----------------\n')

        return ''.join(body)
    
    def fire(self):
        headers = {'content-type': 'application/json'}
        payload = {
            'service_key': self.pagerduty_service_key,
            'description': self.title,
            'event_type': 'trigger',
            'incident_key': tattle.make_md5(self.title),
            'client': self.pagerduty_client_name,
            'client_url': self.client_url,
            'details': {
                'alert-info': self.alert,
                'matches': self.matches
            },
        }

        try:
            response = requests.post(self.url, data=json.dumps(payload, ensure_ascii=False), headers=headers)
            response.raise_for_status()
        except RequestException as e:
            #raise RequestException("Error posting to pagerduty: %s" % e)
            logger.error('Error posting message to pagerduty: %s' % e)

        self.firemsg = """msg="{}", tale_name="{}", title="{}" """.format("PagerDuty Alert Sent", self.alert.get('name'), self.title)


class SlackAlert(AlertBase):
    def __init__(self, **kwargs):
        super(SlackAlert, self).__init__(**kwargs)
  
        
        self.slackcfg = tattle.config.load_configs().get('slack', {})
        self.cfgdefaults = slackcfg.get('defaults', {})

        self.webhook_url = kwargs.get('webhook_url') or self.cfgdefaults.get('webhook_url')
        self.emoji = kwargs.get('emoji', ':squirrel:') or self.cfgdefaults.get('emoji')
        self.channel = kwargs.get('channel', '') or self.cfgdefaults.get('channel')
        self.username = kwargs.get('username', 'Tattle') or self.cfgdefaults.get('username')
        self.msg_color = kwargs.get('message_color', 'danger') or self.cfgdefaults.get('danger')
        self.parse = kwargs.get('parse', 'none')

        self.title_link = self.kibana_dashboard or kwargs.get('title_link') or kwargs.get('client_url') or kwargs.get('url')
        self.title = '{prefix} {title}'.format(self.cfgdefaults.get('title_prefix', 'Tattle -') or tcfg.get('title_prefix', 'Tattle -'),self.title)


    def escape_body(self, body):
        return body


    def make_body(self):
        template_dir = os.path.join(TATTLE_HOME, 'usr', 'share', 'templates', 'html')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('slack.html')

        # convert a single dict into a list, so it can be built with dict_to_html_table()
        if isinstance(self.matches, dict):
            self.matches = [ self.matches ]

        if isinstance(self.matches, list):
            results_table = tattle.dict_to_html_table(self.matches)
        elif isinstance(self.matches, str):
            results_table = self.matches
        else:
            results_table = "No results found"

        try:
            rendered_html = template.render(ainfo=self.alert, results=self.matches, intentions=self.intentions, results_table=results_table, eq=self.eq)
            return rendered_html
        except Exception as e:
            log_msg = "Unable to render email template. <br /><b>Reason: </b>{}</br />".format(e)
            logger.exception(log_msg)
            return log_msg

    def map_severity_emoji(self, level):
        emoji = ':question:'
        level = str(level)

        if self.slackcfg.get('emoji_severity_map'):
            for regex, emoji in self.slackcfg.get('emoji_severity_map'):
                if re.match(regex, level, re.I):
                    emoji = emoji
                    break # we found our match
        else:
            if isinstance(level, str):
                level = level.lower()
            if level in ('crit', 'critical', '5', 5):
                emoji = ':fire:'
            elif level in ('high', '4', 4):
                emoji = ':rage:'
            elif level in ('medium', '3', 3):
                emoji = ':grimacing:'
            elif level in ( 'low', '2', 2):
                emoji = ':disappointed:'
            elif level in ( 'info', 'informational', '1', 1):
                emoji = ':sunglasses:' 
            else:
                emoji = ':question:'

        return emoji




    def fire(self):
        alert_msg = []
        for k,v in self.alert.items():
            alert_msg.append(dict(title=k,value=self.alert.get(k, ''),short=True))

        severity_emoji = self.map_severity_emoji(self.alert.get('severity', ''))
        if severity_emoji != '':
            self.title = "{} {}".format(self.title, severity_emoji)

        il = []
        il.append({'title': 'Description', 'value': self.alert.get('description', '')})
        il.append({'title': 'Severity', 'value': '{} {}'.format(self.alert.get('severity', ''), severity_emoji), 'short': True}) 
        il.append({'title': 'Trigger Reason', 'value': self.trigger_reason, 'short': True})
        il.append({'title': 'Query', 'value': self.intentions.get('_query', '') })

        il.append({'title': 'Time Period', 'value':''})
        il.append({'title': 'From', 'value': '{}\n({})'.format(self.intentions['_start_time_pretty'], self.intentions['_start']), 'short': True})
        il.append({'title': 'To', 'value': '{}\n({})'.format(self.intentions['_end_time_pretty'], self.intentions['_end']), 'short': True})
      
        # convert a single dict into a list, so it can be built with dict_to_html_table()
        if isinstance(self.matches, dict):
            self.matches = [ self.matches ]

        if isinstance(self.matches, list):
            results_table = tattle.dict_to_html_table(self.matches)
        elif isinstance(self.matches, str):
            results_table = self.matches
        else:
            results_table = "No results found"

        rl = []
        for m in self.matches:
            keys = m.keys()
            cols = []
            for k in keys:
                cols.append('*{}*:  _{}_'.format(k, m[k]))
            rl.append(', '.join(cols))

        attachments = [ 
                {
                    'title': self.title, 
                    'title_link': self.title_link,
                    'pretext': self.alert.get('description', ''), 
                    'color': self.msg_color, 
                    'fields': il, 
                    'mrkdwn_in': ['value', 'fields', 'text'],
                    'fallback': self.title, 
                }, 
                {
                    'title': 'Results', 
                    'text': '\n'.join(rl), 
                    'mrkdwn_in': ['text'], 
                    'color': self.msg_color, 
                    'fallback': self.title,
                    'footer': 'Sincerely, \nYour friendly neighborhood Tattle'
                } 
            ]
        
        headers = {'content-type': 'application/json'}
        payload = {
            'username': self.username,
            'channel': self.channel,
            'icon_emoji': self.emoji,
            'parse': self.parse,
            'attachments': attachments
        }
        
        try:
            response = requests.post(self.webhook_url, data=json.dumps(payload, ensure_ascii=False), headers=headers)
            response.raise_for_status()
        except RequestException as e:
            logger.error("Error posting to slack, reaason: {}".format(e))

        self.firemsg = """msg="{}", channel="{}", name="{}" """.format("Slack Alert Sent", self.channel, self.title)

def find_in_alerts(search_id):
    for al in alerts:
        if search_id in al['name']:
            return al

def email(to, results, ainfo, **kwargs):
    if not isinstance(to, list):
        to = [to]

    sender = kwargs.get('sender', mailcfg['default_sender'])
    subject = kwargs.get('subject', "")
    subject_prefix = mailcfg.get('subject_prefix', '')
    subject = "{prefix}{subject}".format(prefix=subject_prefix, subject=subject)

    email_body = make_email_body(results, ainfo)

    msg = MIMEText(email_body, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(to)

    try:
        server = smtplib.SMTP(mailcfg.get('host','localhost'), mailcfg.get('port', 25))
        server.sendmail(sender, to, msg.as_string())
        server.quit()
    except Exception as e:
        logger.exception("Unable to send email: reason: %s, mailcfg: %s" % (e,mailcfg))

    return True

def email_basic(to, subject, body, **kwargs):
    if not isinstance(to, list):
        to = [to]

    sender = kwargs.get('sender', mailcfg['default_sender'])
    subject = kwargs.get('subject', subject)

    email_body = body

    msg = MIMEText(email_body, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(to)

    try:
        server = smtplib.SMTP()
        server = server.connect(mailcfg.get('server', 'localhost'), mailcfg.get('port'), mailcfg.get('timeout', 2))
        server.sendmail(sender, to, msg.as_string())
        server.quit()
    except Exception as e:
        logger.exception("Unable to send email: reason: %s, config: %s" % (e,mailcfg))

    return True

'''
    gets the previous run for an alert
'''
def last_run(es, alert_name):
    
    try:
        res = es.search(index='tattle-int', doc_type='alert_trigger', q='alert-name:"%s"' % (alert_name), sort='time:desc')
    except:
        res = None

    if res:
        for h in res['hits']['hits']:
            return float(h['_source']['time'])
    else:
        return 0

