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
from tattle.config import get_taledirs, get_configdirs

from datemath import datemath

class TestConfig(unittest.TestCase):
    
    def testTaleEnvDirs(self):
        # set an env var for tattle tales
        os.environ['TATTLE_TALES'] = '/etc/tattle_tales'
        self.assertIn('/etc/tattle_tales', get_taledirs())

    def testConfEnvDirs(self):
        os.environ['TATTLE_CONFIG_DIR'] = '/etc/tattle'
        #self.assertIn(':'.join(expected_dirs), ':'.join(get_configdirs())) 
        self.assertIn('/etc/tattle', get_configdirs())


