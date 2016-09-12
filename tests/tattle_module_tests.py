import sys
import os
import re
import datetime
import time
import yaml
import json
from pprint import pprint

TATTLE_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['TATTLE_HOME'] = str(TATTLE_HOME)

sys.path.append(os.path.join(TATTLE_HOME, 'lib'))
sys.path.append(os.path.join(TATTLE_HOME))
sys.path.append(os.path.join('.'))

import unittest

import tattle
from datemath import datemath


class TestTattleModule(unittest.TestCase):

    def testShouldCronCheck(self):

        # True Things
        tests = [
            ( '2016-01-01T00:00:00', '0 0 * * *', True ),
            ( '2016-01-01T00:00:55', '0 0 * * *', True ),
            ( '2016-01-01T00:10:00', '0 0 * * *', False ),
            ( '2016-01-01T01:20:00', '* * * * fri', True),
            ( '2016-01-01T01:20:00', '* 2-4 * * mon-thu', False),
            ( '2016-01-01T01:01:01', '* * * * fri', True),
            ( '2016-01-01T01:01:01', '* * * * thu', False)
        ]

        for test in tests:
            timestr, cronstr, boolean = test
            now = datemath(timestr)
            cron_check = tattle.check_cron_schedule(cronstr, now)
            assert cron_check == boolean


       
