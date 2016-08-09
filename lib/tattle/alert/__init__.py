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
import re
import json
import operator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader 

tcfg = tattle.config.load_tattle_config()
#mailcfg = tcfg['Mail']

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
        #self.matches, self.intentions = self.matches
        self.matches = self.eq.matches
        self.intentions = self.eq.intentions
        self.alert = self.eq.alert
        self.set_title()

    def fire(self, **kwargs):
        raise NotImplementedError()

    def fire_per_match(self, **kwargs):
        raise NotImplementedError()
               
    def set_title(self):
        if self.title:
            self.title = self.title
        elif self.alert['alert'].has_key('title'):
            self.title = self.alert['alert']['title']
        elif self.alert.has_key('name'):
            self.title = self.alert['name']
        else:
            self.title = "Not Defined"

    def create_alert_body(self, matches):
        body = '\n----------------------------------------\n'
        for match in matches:
           # body += unicode(BasicMatchString(self.rule, match))
            # Separate text of aggregated alerts with dashes
            body += match
        body += '\n---------------------------------------\n'
        return body

 
    def __repr__(self,):
       return "<AlertClass: %s - Name: %s>" % ( self.__class__.__name__,  self.alert['name'] )
            
    
class PPrintAlert(AlertBase):
    def __init__(self, **kwargs):
        super(PPrintAlert, self).__init__(**kwargs)
    
    def fire(self):
        self.run()

    def run(self):
        tattle.pprint(vars(self.eq))
        print("\n\n")
        print("-==== PPRINTED ALERT: ====-")
        print("TITLE: {}".format(self.title))
        print("alert defiition:")
        tattle.pprint(self.eq.alert)
        print("alert matches:")
        tattle.pprint(self.matches)
        print("results total:")
        print(self.eq.count('matches'))
        print("event queue:")
        print(tattle.pprint(vars(self.eq)))
        print("-==== END ALERT ====-")
        print("\n\n")


class EmailAlert(AlertBase):
    
    def __init__(self, **kwargs):
        super(EmailAlert, self).__init__(**kwargs)

        mailcfg = tattle.load_email_config()
        self.subject = None
        self.cc = None
        self.bcc = None

        for k,v in self.alert['action']['email'].items():
            if k == 'enabled': continue
            setattr(self, k, v)

        self.sender = kwargs.get('sender', mailcfg['default_sender'])
        # sets our email subject

        self.subject_prefix = mailcfg.get('subject_prefix', '')

        if not self.subject:
            self.set_subject(**kwargs)


    def connect(self):
        try:
            self.server = smtplib.SMTP(mailcfg.get('host','localhost'), mailcfg.get('port', 25))
        except Exception as e:
            logger.exception("Unable to connect to SMTP server: reason: %s, mailcfg: %s" % (e,mailcfg))

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
        self.subject = "{prefix}{subject}".format(prefix=self.subject_prefix, subject=self.subject)
        self.build_msg()
        self.send_email()

    def send_email(self,):
            try: 
                self.server.sendmail(self.sender, self.to, self.msg.as_string())
                self.server.quit()
            except Exception as e:
                logger.exception("Unable to send email, reason: {}".format(e))

    def set_subject(self, **kwargs):
        if self.alert['action']['email'].has_key('subject'):
            self.subject = self.alert['alert']['email']['subject']
        else: 
            self.subject = self.title

    def make_email_body(self, ):
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
            rendered_html = template.render(ainfo=self.alert, results=self.matches, intentions=self.intentions, results_table=results_table, eq=self.eq)
            return rendered_html
        except Exception as e:
            log_msg = "Unable to render email template. <br /><b>Reason: </b>{}</br />".format(e)
            logger.exception(log_msg)
            return log_msg



class ScriptAlert(AlertBase):

    def __init__(self, script_name, **kwargs):
        super(ScriptAlert, self).__init__(**kwargs)
        self.script_name = script_name

    def fire(self):
        try:
            tattle.run_script(self.script_name, json.dumps(self.matches), json.dumps(self.alert), json.dumps(self.intentions)) 
        except Exception as e:
            logger.exception('Unable to run script: %s, reason: %s'.format(self.script_name, e))
        
        
class PagerDutyAlert(AlertBase):
    
    def __init__(self, service_name, **kwargs):
        super(PagerDutyAlert, self).__init__(**kwargs)
        pdcfg = tattle.config.load_pd_config() 

        # Find our config options based on our service name
        cfg = self.get_service_args(service_name, pdcfg)

        if not cfg:
            msg = "Unable to find PagerDuty config for: {}, cannot continue.".format(service_name)
            logger.exception(msg)   
            raise Exception(msg)
       
        self.pagerduty_service_key = cfg.get('service_key')
        self.pagerduty_client_name = cfg.get('client_name', 'Tattle')

        self.url = 'https://events.pagerduty.com/generic/2010-04-15/create_event.json'

        self.title = "Tattle - {}".format(self.title)


    def get_service_args(self, key, pdcfg):
        for k,args in pdcfg.items():
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
            logger.error('Error posting to pagerduty: %s' % e)



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
        res = es.search(index='tattle-int', doc_type='alert_trigger', q='alert-name:%s' % (alert_name), sort='time:desc')
    except:
        res = None

    if res:
        for h in res['hits']['hits']:
            return float(h['_source']['time'])
    else:
        return 0

