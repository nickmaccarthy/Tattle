import sys
import os
import datetime
import tattle
from tattle.search import Search
from tattle.search.query import Query
from tattle.utils import FlattenDict
import tattle.filter
import tattle.alert
import json

TATTLE_HOME = os.environ.get('TATTLE_HOME')


s = Search()

logger = tattle.get_logger('tattle.workers')
def tnd(es, alert):
    global logger

    should_alert = False

    if tattle.normalize_boolean(alert.get('disabled')) == True: 
        logger.info('Alert: {} is disabled.  Moving on...'.format(alert.get('name')))
        return

    realert_threshold = tattle.relative_time_to_seconds(alert['alert']['realert'])

    logger.info('last alert for %s was %s' % ( alert['name'], tattle.epoch2iso(tattle.alert.last_run(es, alert['name']))))

    if tattle.alert.last_run(es, alert['name']) > 0:
        last_run = tattle.alert.last_run(es, alert['name'])
        time_since = ( tattle.get_current_time_local() - tattle.alert.last_run(es, alert['name']))
        if time_since <= realert_threshold: 
            # No need to go any further, we havent hit our threshold yet
            logger.info("Alert is within re-alert threshold.  Name: {}, re-alert threshold: {}, last run: {}, human: {}".format(alert['name'], alert['alert']['realert'], last_run, tattle.humanize_ts(last_run)))
            return

    if alert.get('tql_query'):
        try:
            esq = s.tql_query(alert['tql_query'], exclude=alert.get('exclude', ''), start=alert['timeperiod'].get('start', '-1m'), end=alert['timeperiod'].get('end', 'now'), index=alert.get('index', 'logstash-*'))
            results = es.search(index=esq['search_indexes'], body=esq['esquery'], request_timeout=10) 
        except Exception as e:
            logger.exception("Unable to run TQL ES query from worker - alert: %s,  reason: %s" % (alert['name'], e))
            return
    elif alert.get('es_query'):
        try:
            esq = s.es_query(alert['es_query']['json_string'], index=alert.get('index'), **alert['es_query'])
            results = es.search(index=esq['search_indexes'], body=esq['esquery'], request_timeout=10)
            #tattle.pprint(results)
        except Exception as e:
            logger.exception('Unable to run ESQuery from worker - alert: %s, reason: %s' % (alert['name'], e))
            return 

    if not results: return

    alert_type = alert['alert'].get('type')

    if '_field' in alert_type:
        fd = FlattenDict()
        flat = fd.flatten_dict(results)
        filtered = tattle.filter.find_in_dict(fd, alert['alert'].get('field_name'))
        tattle.pprint(filtered)
        if filtered:
            matches = tattle.filter.meets_threshold(filtered, alert['alert']['relation'], alert['alert']['qty'])
            if matches:
                should_alert = True
    elif '_number_of_events' in alert_type:
        matches = tattle.filter.meets_total(results, alert['alert']['relation'], alert['alert']['qty'])
        fd = FlattenDict()
        #tattle.pprint(matches)
        if matches:
            total, results = matches
            if alert['alert'].has_key('return_matches') and tattle.normalize_boolean(alert['alert']['return_matches']) == True:
                matches = fd.flatten_hits(results['hits']['hits'])
            else:
                matches = "I have found Total: {} matches <br /> Matches not returned because 'return_matches' was false.".format(total)
            should_alert = True
    else:
        logger.error("Alert type not found, please specify a valid alert type. Alert: {}, reason: {} is what I got".format(alert['name'], alert_type))
        return

    if should_alert:
            # update the alert_triggers
            es.index(index='tattle-int', doc_type='alert_trigger', id=alert['name'], body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time': tattle.get_current_utc(), 'results': results})
            # log the alert in tattle-int
            es.index(index='tattle-int', doc_type='alert-fired', id=tattle.md5hash("{0}{1}".format(alert['name'], tattle.get_current_utc())), body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time_unix': tattle.get_current_utc(), 'alert-results': results})

            if alert['action'].has_key('email'):
                should_email = tattle.normalize_boolean(alert['action']['email']['enabled'])
                if should_email:
                    # Todo, make the email subject come from tattle.yml
                    email_subject = '{0}'.format(alert['name'])
                    email_it = tattle.alert.email( alert['action']['email']['to'], {'results': matches, 'intentions': esq['intentions']}, alert, subject=email_subject ) 
                    email_it = True
                    if email_it:
                        logger.info("""msg="{0}", email_to="{1}", name="{2}", subject="{3}" """.format( "Email Sent", alert['action']['email']['to'], alert['name'], email_subject ))

            if alert['action'].has_key('script'):
                SCRIPT_DIRS = tattle.get_bindirs(TATTLE_HOME)
                print tattle.run_script(alert['alert']['action']['script']['filename'], alert_results)
    else:
        logger.info("Nope, i would not alert. Alert: {} Reason: {} was not {} {}".format(alert['name'], alert['alert']['type'], alert['alert']['relation'], alert['alert']['qty']))

    return True

