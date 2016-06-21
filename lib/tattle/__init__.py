import sys
import os
import datetime
import calendar
import time
import glob
import imp
import datetime
import arrow
import socket
import platform
import commands
import logging
import logging.handlers as logging_handler
from autocast import autocast
import random
import re
import collections
import subprocess
import json
import simplejson

from pprint import pprint 

''' returns a unix timestamp of the current time in UTC '''
def get_current_utc():
    return calendar.timegm(datetime.datetime.utcnow().utctimetuple())

''' returns a unix timestamp of the current time localy to host '''
def get_current_time_local():
    return time.time()

''' finds items in a list, can optionally take a list as the needle '''
def find_in_list(needle, lst):
    if isinstance(needle, list):
        for n in needle:
            find_in_list(n, lst)
    else:         
        for l in lst:
            if needle in l:
                return l
            else: 
                continue
        return
    
''' gets a list of confs from a directory '''
def get_confs(PATH):
    confs = []
    for conf in glob.glob("%s/*.conf" % (PATH)):
        confs.append(conf)
    return confs

''' returns back a unix timestamp to a ISO format '''
def epoch2iso(epoch_ts):
    if epoch_ts is not None:
        return datetime.datetime.fromtimestamp(float(epoch_ts)).strftime("%Y-%m-%dT%H:%M:%S.%f%Z")


def clean_keys(string): 
    escape_these = ',\=\n\r\\'
    for char in escape_these:
        string = string.replace(char, '__')
    return string

''' returns a list of dicts into a html table '''
def dict_to_html_table(ourl):
    #print "List: {0}".format(ourl)
    try:
        headers = ourl[0].keys()

        table = []
        theaders = []
        for h in headers:
            theaders.append("<th>%s</th>" % h)

        table.append("<table border='1' cellpadding='1' cellspacing='1'>")
        table.append("<thead>")
        table.append("<tr>")
        for h in headers:
            table.append("<th>%s</th>" % h)
        table.append("</tr>")
        table.append("</thead>")

        table.append("<tbody>")
        tblst = []
        for l in ourl:
            table.append("<tr>")
            for h in headers:
                table.append("<td><pre> %s </pre></td>" % (str(l[h])))
            table.append("</tr>")
        table.append("</tbody>")
        table.append("</table>")

        return ''.join(table)
    except Exception, e:
        return e


def datatable(ourl):
    try:
        theaders = ourl['_results'][0].keys()
        table = []
        table.append('<table id="datatable" class="table table-striped table-bordered table-hover dataTable no-footer">')
        table.append('<thead>')
        table.append('<tr>')
        for h in theaders:
            table.append("<th>%s</th>" % h)
        table.append("</tr>")
        table.append("</thead>")

        table.append("<tbody>")
        tblst = []
        for l in ourl['_results']:
            table.append("<tr>")
            for h in theaders:
                table.append("<td> %s </td>" % (str(l[h])))
            table.append("</tr>")
        table.append("</tbody>")
        table.append("</table>")
        htmltable =  ''.join(table)
    except:
        theaders = ['Results']
        htmltable = '<p>No results found</p>'

    return { 'query_intentions': ourl.get('query_intentions'), 'theaders': theaders, 'html': htmltable}    

''' returns a logger instance
    this can be used from other classes/modules like so:
    import tattle 
    logger = tattle.get_logger(__name__)
    logger.info("Some log msg")
    logger.error("An error has happened: %s" % (error))
'''
def get_logger(name='tattle', type='default'):
    import tattle.log as bnlog

    logger = bnlog.logger()
    logobj = logger.get_logger(name)
    return logobj

''' gets the val for a key in a multi dimensional dict '''
def _get(dct, default, *keys):
    sentry = object()
    def getter(level, key):
        return default if level is sentry else level.get(key, sentry)
    return reduce(getter, keys, dct)


def dm_convert(timestr):
    from datemath import dm
    return dm(timestr).timestamp

def relative_time_to_seconds(timestr):
    try:
        m = re.match("^(?P<interval>\-\d+|\d+)(?P<period>\w+)", timestr) 
        if m:
            interval = m.group('interval')
            interval = int(interval.lstrip('-'))
            period = m.group('period')
    except Exception, e:
        print "unable to parse relative time string: %s" % e
        return

    if 's' in period:
        time_multiplier = 0
    elif 'm' in period:
        time_multiplier = 60
    elif 'h' in period:
        time_multiplier = 3600
    elif 'd' in period:
        time_multiplier = 86400
    elif 'w' in period:
        time_multiplier = 604800
    elif 'M' in period:
        time_multiplier = 18144000
    elif 'Y' in period:
        time_multiplier = 217780000

    return interval * time_multiplier

'''
    finds an item in a dictionary, works with nested dicts as well 
'''
def find_in_dict(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = find_in_dict(v, key)
            if item is not None:
                return item


def fd(d):
    def items():
        for key, value in d.items():
            if isinstance(value, dict):
                for subkey, subvalue in flatten_dict(value).items():
                    yield key + "." + subkey, subvalue
            else:
                yield key, value

    return dict(items())

def flatten_dict(d, lkey='', sep='.'):
    ret = {}
    for rkey,val in d.items():
        key = lkey+rkey
        if isinstance(val, dict):
            ret.update(flatten_dict(val, key+sep))
        #elif isinstance(val, list):
        #    for i in val:
        #        ret.update(flatten_dict(i, key+sep))
        else:
            ret[key] = val
    return ret


def run_script(script_name, std_in):
    logger = get_logger('run-script')
       
    script_bins = [ os.path.join(os.environ["BN_HOME"], 'bin', 'scripts') ]

    for bin_dir in script_bins:
        full_path = os.path.join(bin_dir, script_name)

        logger.info("will now run script: %s" % (full_path))
        try:
            proc = subprocess.Popen(full_path, stdin=subprocess.PIPE)
            proc.stdin.write(json.dumps(std_in['_results']))
        except Exception, e:
            logger.exception("Unable to run script.  Reason: %s" % (e))

'''
    Loads a python module from a file, and returns it if it has a main() method
'''
def load_module_from_file(filepath, d=None):
    class_inst = None
    expected_class = 'main'

    mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])

    if file_ext.lower() == '.py':
         py_mod = imp.load_source(mod_name, filepath)
    elif file_ext.lower() == '.pyc':
         py_mod = imp.load_compiled(mod_name, filepath)

    if hasattr(py_mod, expected_class):
        class_inst = getattr(py_mod, expected_class)(d)

    return class_inst


'''
    Finds a file in a directory
'''
def find_file(name, path):
    if isinstance(path, list):
        for p in path:
            for root, dirc, files in os.walk(p):
                if name in files:
                    return os.path.join(root, name)
    else:
        for root, dirc, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

''' finds our bin directories '''
def get_bindirs(PATH):
    bindirs = ["%s/bin" % (PATH), "%s/bin/scripts" % (PATH)]
    for dir in glob.glob("%s/*/*/*/bin" % (PATH)):
        bindirs.append(dir)
    return bindirs

''' gets a list of our apps '''
def get_apps(PATH):
    apps = []
    for app in os.listdir(PATH):
        app_info = { "name": app, "path": os.path.join(PATH, app) }
        apps.append(app_info)
    return apps

''' auto casts an input given, returns a casted version '''
@autocast
def castem(e):
    return e

def get_hostname():
    import commands
    return commands.getoutput("hostname -s")

def pprint(obj):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    return pp.pprint(obj)

def pprint_as_json(blob):
    return pprint_json(blob)

''' pretty prints into json '''
def pprint_json(blob):
    try:
        print simplejson.dumps(blob, sort_keys=False, indent=4, ensure_ascii=False)
    except UnicodeDecodeError:
        # This blob contains non-unicode, so lets pretend it's Latin-1 to show something
        print simplejson.dumps(blob, sort_keys=True, indent=4, encoding='Latin-1', ensure_ascii=False)

''' returns an md5 hash from a given input '''
def md5hash(input):
    import hashlib
    if isinstance(input, tuple):
        input = str(''.join(map(str,input)))
    input = str(input)
    m = hashlib.md5()
    m.update(input)
    return m.hexdigest()

''' alias to md5hash '''
def make_md5(input):
    return md5hash(input)

''' returns a list of indexes bases from a start and end time with a index time pattern '''
def get_indexes(index_name, start, end, interval='day', pattern='YYYY.MM.DD'):
    if '*' in index_name:
        index_name = index_name.strip('*')
    retl = []
    for r in arrow.Arrow.range(interval, start, end):
        idx_name = "%s%s" % ( index_name, r.format(pattern) )
        retl.append(idx_name)
    return ','.join(retl)

'''
    Normalized boolean variables for us
'''
def normalize_boolean(input):
    true_things = [True, 'True', 't', '1', 1, 'yes', 'y', 'on']
    false_things = [None, False, 'False', 'f', '0', 0, 'no', 'n', 'off']

    def norm(input):
        if input == True: return True
        if input == False: return False

        try:
            test = input.strip().lower()
        except:
            return input

        if test in true_things:
            return True
        elif test in false_things:
            return False
    return norm(input)


'''
    Humanizes a timestamp, i.e. a timestamp within the last half hour would become '29 minutes ago', etc
'''
def humanize_ts(timestamp):
    utcnow = arrow.utcnow()
    try:
        ts = arrow.get(timestamp)
        return ts.humanize(utcnow)
    except Exception as e:
        return "Unable to humanize timestamp, reason: {}".format(e)


def makecsvfromlist(lst, filename=None):
    import csv
    
    if filename is None:
        filename = 'no_filename_given'

    filename_full = os.path.join(os.environ.get('BN_HOME'), 'tmp', "{0}.csv".format(filename))
    
    with open(filename_full, 'w+') as fh:
        if len(lst) > 0:
            headers = lst[0].keys()
            writer = csv.DictWriter(fh, fieldnames=headers)
            writer.writeheader()
            for l in lst:
                writer.writerow(l)
        else:   
            fh.write('No results')

    return filename_full


'''
    Gets the current location of $TATTLE_HOME
'''
def get_tattlehome():
    return os.environ['TATTLE_HOME']
