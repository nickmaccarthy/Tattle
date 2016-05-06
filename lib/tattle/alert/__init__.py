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
from tattle.search.query import Query
import re
import json
import operator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader 

tcfg = tattle.config.load_tattle_config()
mailcfg = tcfg['Mail']

from pprint import pprint
import requests

logger = tattle.get_logger('alert')

TATTLE_HOME = os.environ['TATTLE_HOME']

def make_email_body(results, ainfo):
    template_dir = os.path.join(TATTLE_HOME, 'usr', 'share', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('email.html')
    print type(results['results'])
    if isinstance(results['results'], list):
        results_table = tattle.dict_to_html_table(results['results'])
    elif isinstance(results['results'], str):
        results_table = results['results']
    else:
        results_table = "No results found"

    try:
        rendered_html = template.render(ainfo=ainfo, results=results, results_table=results_table)
        return rendered_html
    except Exception as e:
        log_msg = "Unable to render email template. <br /><b>Reason: </b>{}</br />".format(e)
        logger.exception(log_msg)
        return log_msg

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
        server = smtplib.SMTP(mailcfg.get('host','localhost'), mailcfg.get('port', 2525))
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
    res = es.search(index='tattle-int', doc_type='alert_trigger', q='alert-name:%s' % (alert_name), sort='time:desc')
    if res:
        for h in res['hits']['hits']:
            return float(h['_source']['time'])
    else:
        return 0

