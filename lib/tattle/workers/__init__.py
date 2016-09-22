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
#from tattle.alert import EmailAlert, PPrintAlert, PagerDutyAlert, ScriptAlert, SlackAlert
from tattle.alert import *
from datemath import dm, datemath
from elasticsearch.exceptions import NotFoundError
import importlib


TATTLE_HOME = os.environ.get('TATTLE_HOME')

s = Search()

logger = tattle.get_logger('tattle.workers')

def es_search(es, *args, **kwargs):
    try:
        results = es.search(request_timeout=10, **kwargs) 
    except NotFoundError:
        logger.debug('Index not found: args: {}, kwargs: {}'.format(args, kwargs))
        return

    return results

def tnd(es, alert):
    s = Search()
    global logger

    should_alert = False
    matches = None

    if tattle.normalize_boolean(alert.get('enabled')) == False or tattle.normalize_boolean(alert.get('disabled')) == True: 
        logger.debug('Alert: {} is disabled.  Moving on...'.format(alert.get('name')))
        return

            
    # If we are in an exclude schedule, then we dont need to go any futher 
    if 'exclude_schedule' in alert:
        if tattle.check_cron_schedule(alert.get('exclude_schedule')) == True:
            logger.debug('Exclude Schedule - Alert: {} is currently in an exclude schdule. Moving on...'.format(alert.get('name')))
            return

    # If we have a schedule, then lets check it, otherwise we assume the tale should be run/checked everytime Tattle runs
    if 'schedule' in alert:
        schedule = alert.get('schedule')
        if tattle.check_cron_schedule(schedule) == False:
            logger.debug('Schedule - Alert: "{}" has a schedule, but it not currently scheduled run.  schedule: "{}", next_run: {} seconds. Moving on...'.format(alert.get('name'), schedule, tattle.cron_check(schedule)))
            return


    realert_threshold = tattle.relative_time_to_seconds(alert['alert']['realert'])

    logger.debug('last alert for %s was %s' % ( alert['name'], tattle.epoch2iso(tattle.alert.last_run(es, alert['name']))))
    
    last_run = tattle.alert.last_run(es, alert['name']) 
    if last_run is None:
        logger.info("Last run was 'None; for: %s.  This is the first time we have seen it." % (alert['name']))
        last_run = 100000000
    
    if last_run > 0:
        time_since = ( tattle.get_current_time_local() - last_run )
        if time_since <= realert_threshold: 
            # No need to go any further, we havent hit our threshold yet
            logger.debug("Alert is within re-alert threshold.  Name: {}, re-alert threshold: {}, last run: {}, human: {}".format(alert['name'], alert['alert']['realert'], last_run, tattle.humanize_ts(last_run)))
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
            ourkey = list(results_aggs.keys())[0]
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
    elif alert_type in ('agg_match', 'regex_match'):
        matches = tattle.filter.meets_in_field(results, alert['alert']['field'], alert['alert']['relation'], alert['alert']['qty'])
        if matches:
            should_alert = True
    elif alert_type in ('frequency', 'number_of_events', '_number_of_events_', '_number_of_events'):
        matches = tattle.filter.meets_total(results, results_total, alert['alert']['relation'], alert['alert']['qty'])
        if matches:
            total, results = matches
            if 'return_matches' in alert['alert']:
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
                #matches = "<br />I have found a total of <b>{}</b> matches. <br /> Note: Matches not returned because 'return_matches' was false.".format(total)
                matches = { 'matches': total }
            should_alert = True
    elif alert_type in ('spike', 'event_spike', '_event_spike'):
        start_ts = esq['intentions']['_start_time_iso_str']
        end_ts = esq['intentions']['_end_time_iso_str']

        start = "%s||%s" % ( start_ts, alert['alert']['window']['start'])
        end = "%s||%s" % ( end_ts, alert['alert']['window']['end'])

        print(start_ts, start)
        print(end_ts, end)
        esq = s.tql_query(alert['tql_query'], exclude=alert.get('exclude', ''), start=start, end=end, index=alert.get('index', 'logstash-*'))

        print("ESQuery2:")
        tattle.pprint(esq['esquery'])

        search_args = dict(index=esq['search_indexes'], body=esq['esquery'])
        r1 = results
        r2 = es_search(es, **search_args)

        q2 = EventQueue(alert=alert, results=r2, intentions=esq['intentions'])

        print(q.results_total)
        print(q2.results_total)

    else:
        logger.error("Alert type not found, please specify a valid alert type. Alert: {}, reason: {} is what I got".format(alert['name'], alert_type))
        return

    if matches:
        q.matches = matches

    if should_alert:
            #es.index(index='tattle-int', doc_type='alert_trigger', id=alert['name'], body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time': tattle.get_current_utc(), 'matches': q.matches})
            es.index(index='tattle-int', doc_type='alert_trigger', id=alert['name'], body={'alert-name': alert['name'], 'alert-severity': alert.get('severity', 'not_found'), '@timestamp': datetime.datetime.utcnow(), 'time': tattle.get_current_utc()})
            # log the alert in tattle-int
            #es.index(index='tattle-int', doc_type='alert-fired', id=tattle.md5hash("{0}{1}".format(alert['name'], tattle.get_current_utc())), body={'alert-name': alert['name'], '@timestamp': datetime.datetime.utcnow(), 'time_unix': tattle.get_current_utc(), 'alert-matches': q.matches, 'alert-args': alert})
            es.index(index='tattle-int', doc_type='alert-fired', id=tattle.md5hash("{0}{1}".format(alert['name'], tattle.get_current_utc())), body={'alert-name': alert['name'], 'alert-severity': alert.get('severity', 'not_found'), '@timestamp': datetime.datetime.utcnow(), 'time_unix': tattle.get_current_utc()} )

            for action, args in alert['action'].items():

                # are we enabled to run?
                if tattle.normalize_boolean(args.get('enabled', 1)) == True:
                    try:
                        ''' 
                            alert classnames always start with a capital letter
                            pagerduty == PagerdutyAlert, slack == SlackAlert, etc 
                        '''
                        class_name = "{}Alert".format(action.title())

                        if 'once_per_match' in args:
                            for m in q.matches:
                                mq = EventQueue(alert=alert, results=results, matches=m, intentions=esq['intentions'], **args)
                                alertobj = getattr(tattle.alert, class_name)(event_queue=mq, mathces=m, **args)
                                alertobj.title = "{} - {}".format(alert['name'], m[args['once_per_match'].get('match_key', 'key')])
                                alertobj.fire()
                                logger.info(alertobj.firemsg)
                        else:
                            alertobj = getattr(tattle.alert, class_name)(event_queue=q, **args)
                            alertobj.fire()
                            logger.info(alertobj.firemsg)
                    except Exception as e:
                        msg = "Unable to initialize class: {}, reason: {}".format(class_name, e)
                        logger.exception(msg)

    else:
        logger.debug("Nope, i would not alert. Alert: {} Reason: {} was not {} {}".format(alert['name'], alert['alert']['type'], alert['alert']['relation'], alert['alert']['qty']))

    return True

