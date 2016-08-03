import sys
import os
import re
import datetime
import time
import yaml
import json

TATTLE_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['TATTLE_HOME'] = str(TATTLE_HOME)

sys.path.append(os.path.join(TATTLE_HOME, 'lib'))
sys.path.append(os.path.join(TATTLE_HOME))

import unittest

from elasticsearch import Elasticsearch

import tattle
import tattle.config

class TestConfig(unittest.TestCase):

    def testPagerDuty(self):
        pdcfg = tattle.config.load_pd_config()
        tattle.pprint_as_json(pdcfg)


if __name__ == "__main__":
    unittest.main()
