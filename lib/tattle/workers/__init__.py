import sys
import os
import datetime
import tattle
from tattle.search import Search
from tattle.utils import FlattenDict, EventQueue
import tattle.filter
import tattle.alert
import json
from tattle.result import results_to_df
import random
from tattle.alert import EmailAlert, PPrintAlert, PagerDutyAlert
from datemath import dm, datemath

TATTLE_HOME = os.environ.get('TATTLE_HOME')

s = Search()

logger = tattle.get_logger('tattle.workers')

def es_search(es, *args, **kwargs):
    results = es.search(request_timeout=10, **kwargs) 
    return results

def tnd(es, alert):
    s = Search()
    global logger

    should_alert = False
    matches = None

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
            #print "ESQuery1:"
            #tattle.pprint(esq['esquery'])
            #tattle.pprint(esq)
            #print "\n\n"
            #results = es.search(index=esq['search_indexes'], body=esq['esquery'], request_timeout=10) 
            esargs = dict(
                    index=esq['search_indexes'],
                    body=esq['esquery']
                )
            results = es_search(es, **esargs) 
        except Exception as e:
            logger.exception("Unable to run TQL ES query from worker - alert: %s,  reason: %s" % (alert['name'], e))
            return
    elif alert.get('es_query'):
        try:
            esq = s.es_query(alert['es_query']['json_string'], index=alert.get('index'), **alert['es_query'])
            results = es.search(index=esq['search_indexes'], body=esq['esquery'], request_timeout=10)
        except Exception as e:
            logger.exception('Unable to run ESQuery from worker - alert: %s, reason: %s' % (alert['name'], e))
            return 

    
    if not results: return

    q = EventQueue(alert=alert, results=results, intentions=esq['intentions'])

    results_hits = q.results_hits
    results_aggs = q.results_aggs
    results_total = q.results_total

    if results_aggs and len(results_aggs) > 0:
        if tattle.find_in_dict(results_aggs, 'buckets'):
            ourkey = results_aggs.keys()[0]
            results = results_to_df(results_aggs[ourkey]['buckets'])
        else:
            results = [results_aggs]
    elif len(results_hits) > 0:
        results = results_to_df([x['_source'] for x in results_hits])
    elif len(results_hits) == 0:
        results = [ {'message': 'no results found'} ]

    if not isinstance(results, list):
        results = results.to_dict('records')

    alert_type = alert['alert'].get('type')

    if '_field_' in alert_type:
        fd = FlattenDict()
        flat = fd.flatten_dict(results)
        filtered = tattle.filter.find_in_dict(fd, alert['alert'].get('field_name'))
        if filtered:
            matches = tattle.filter.meets_threshold(filtered, alert['alert']['relation'], alert['alert']['qty'])
            if matches:
                should_alert = True
    elif 'agg_match' in alert_type:
        matches = tattle.filter.meets_in_field(results, alert['alert']['field'], alert['alert']['relation'], alert['alert']['qty'])
        if matches:
            should_alert = True
    elif '_number_of_events' in alert_type:
        matches = tattle.filter.meets_total(results, results_total, alert['alert']['relation'], alert['alert']['qty'])
        if matches:
            total, results = matches
            if alert['alert'].has_key('return_matches'):
                # todo:  move this logic somewhere more robust
                amatch = alert['alert']['return_matches']
                matchlen = amatch.get('length', 10)
                return_random = amatch.get('random', False)
                if return_random:
                    if matchlen >= len(results):
                        matches = results
                    else:
                        matches = random.sample(results, matchlen)
                else:
                    matches = results[0:matchlen]
            else:
                matches = "<br />I have found a total of <b>{}</b> matches. <br /> Note: Matches not returned because 'return_matches' was false.".format(total)
            should_alert = True
    elif '_event_spike' in alert_type:
        start_ts = esq['intentions']['_start_time_iso_str']
        end_ts = esq['intentions']['_end_time_iso_str']

        start = "%s||%s" % ( start_ts, alert['alert']['window']['start'])
        end = "%s||%s" % ( end_ts, alert['alert']['window']['end'])

        print start_ts, start
        print end_ts, end
        esq = s.tql_query(alert['tql_query'], exclude=alert.get('exclude', ''), start=start, end=end, index=alert.get('index', 'logstash-*'))

        print "ESQuery2:"
        tattle.pprint(esq['esquery'])

        search_args = dict(index=esq['search_indexes'], body=esq['esquery'])
        r1 = results
        r2 = es_search(es, **search_args)

        q2 = EventQueue(alert=alert, results=r2, intentions=esq['intentions'])

        print q.results_total
        print q2.results_total

    else:
        logger.error("Alert type not found, please specify a valid alert type. Alert: {}, reason: {} is what I got".format(alert['name'], alert_type))
        return

    if matches:
        q.matches = matches

    if should_alert:
            es.index(index='tattle-int', doc_type='alert_trigger', id=alert['name'], body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time': tattle.get_current_utc(), 'matches': q.matches})
            # log the alert in tattle-int
            es.index(index='tattle-int', doc_type='alert-fired', id=tattle.md5hash("{0}{1}".format(alert['name'], tattle.get_current_utc())), body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time_unix': tattle.get_current_utc(), 'alert-matches': q.matches, 'alert-args': alert})

            if alert['action'].has_key('email'):
                should_email = tattle.normalize_boolean(alert['action']['email']['enabled'])
                if should_email:
                    if alert['action']['email'].has_key('once_per_match'):
                        for m in q.matches:
                            mq = EventQueue(alert=alert, results=results, matches=m, intentions=esq['intentions'])
                            email_alert = EmailAlert(event_queue=mq)
                            email_alert.subject = "{} - {}".format(alert['name'], m[alert['action']['email']['once_per_match'].get('match_key', 'key')])
                            email_alert.fire()
                            email_it = True
                            if email_it:
                                logger.info("""msg="{0}", email_to="{1}", name="{2}", subject="{3}" """.format( "Email Sent", email_alert.to, alert['name'], email_alert.subject ))
                    else: 
                        email_alert = EmailAlert(event_queue=q)
                        email_alert.fire()
                        email_it = True
                        if email_it:
                            logger.info("""msg="{0}", email_to="{1}", name="{2}", subject="{3}" """.format( "Email Sent", email_alert.to, alert['name'], email_alert.subject ))

            if alert['action'].has_key('pprint'):
                if tattle.normalize_boolean(alert['action']['pprint']['enabled']) == True:
                    pp_alert = PPrintAlert(event_queue=q)
                    pp_alert.fire()
                
            if alert['action'].has_key('pagerduty'):
                if tattle.normalize_boolean(alert['action']['pagerduty']['enabled']) == True:
                    service_name = alert['action']['pagerduty'].get('service_name') or alert['action']['pagerduty'].get('service_key')
                    if not service_name:
                        logger.error('Service name was not set for pagerduty alert, cannot continue with this alert method. ')
                        return
                    if alert['action']['pagerduty'].has_key('once_per_match'):
                        for m in q.matches:
                            mq = EventQueue(alert=alert, results=results, matches=m, intention=esq['intentions'])
                            pdalert = PagerDutyAlert(service_name, event_queue=mq)
                            pdalert.title = "{} - {}".format(alert['name'], m[alert['action']['email']['once_per_match'].get('match_key', 'key')])
                            pdalert.fire()
                            logger.info("""msg="{}", name="{}" """.format("PagetDuty Alert Sent", pdalert.title))
                    else:
                        pdalert = PagerDutyAlert(service_name, event_queue=q)
                        pdalert.fire()
                        logger.info("""msg="{}", name="{}" """.format("PagetDuty Alert Sent", alert['name']))
                    
            if alert['action'].has_key('script'):
                SCRIPT_DIRS = tattle.get_bindirs(TATTLE_HOME)
                print tattle.run_script(alert['alert']['action']['script']['filename'], matches)
    else:
        logger.info("Nope, i would not alert. Alert: {} Reason: {} was not {} {}".format(alert['name'], alert['alert']['type'], alert['alert']['relation'], alert['alert']['qty']))

    return True

