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


severities = [ 
        ('critical', True), 
        ('Crit', True), 
        (5, True), 
        ('5', True),
        ('BAD', False),
        ('low', True),
        ('noworries', True),
        (1, True)
]

map_yaml = """

emoji_severity_map:
    'crit|5': ':fire:'
    'high|4': ':rage:'
    'low|noworries|1': ':sunglasses:'

"""

maps = yaml.load(map_yaml)


def testit(item):
    level,expected_return = item 
    level = str(level)

    for regex,emoji in maps.get('emoji_severity_map').items():
        if re.match(regex, level, re.I):
            return True
        
    return False
           
        

class SlackTest(unittest.TestCase):

    ''' tests regex matching of our emoji map from yaml '''
    def testEmojiMap(self):
        for item in severities:
            level,expected_return = item
            the_test = testit(item)
            assert the_test == expected_return


