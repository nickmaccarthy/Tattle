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


class TestBuildIndexes(unittest.TestCase):
    
    def testFromDictOne(self):
        index_info = {'pattern': 'YYYY.MM.DD', 'interval': 'day', 'name': 'some-index-'} 
        expected = 'some-index-2015.12.29,some-index-2015.12.30,some-index-2015.12.31,some-index-2016.01.01'
        built_indexes = tattle.get_indexes(index_info, datemath('2016-01-01||-3d'), datemath('2016-01-01'))
        self.assertEqual(built_indexes, expected)

    def testFromDictDefaultPatternAndDay(self):
        index_info = {'name': 'some-index-'}
        expected = 'some-index-2015.12.29,some-index-2015.12.30,some-index-2015.12.31,some-index-2016.01.01'
        built_indexes = tattle.get_indexes(index_info, datemath('2016-01-01||-3d'), datemath('2016-01-01'))
        self.assertEqual(built_indexes, expected)

    def testStarIndexNames(self):
        index_info = 'some-index-*'
        expected = 'some-index-2015.12.29,some-index-2015.12.30,some-index-2015.12.31,some-index-2016.01.01'
        built_indexes = tattle.get_indexes(index_info, datemath('2016-01-01||-3d'), datemath('2016-01-01'))
        self.assertEqual(built_indexes, expected)

    def testIndexPatternInString(self):
        index_info = 'some-index-%{+YYYY.MM.DD}'
        expected = 'some-index-2015.12.29,some-index-2015.12.30,some-index-2015.12.31,some-index-2016.01.01'
        built_indexes = tattle.get_indexes(index_info, datemath('2016-01-01||-3d'), datemath('2016-01-01'))
        self.assertEqual(built_indexes, expected)
       
    def testIndexPatternInStringWithInterval(self):
       
        index_info = 'some-index-%{+YYYY.MM.DD.HH}:hour' 
        expected = 'some-index-2015.12.29.00,some-index-2015.12.29.01,some-index-2015.12.29.02,some-index-2015.12.29.03,some-index-2015.12.29.04,some-index-2015.12.29.05,some-index-2015.12.29.06,some-index-2015.12.29.07,some-index-2015.12.29.08,some-index-2015.12.29.09,some-index-2015.12.29.10,some-index-2015.12.29.11,some-index-2015.12.29.12,some-index-2015.12.29.13,some-index-2015.12.29.14,some-index-2015.12.29.15,some-index-2015.12.29.16,some-index-2015.12.29.17,some-index-2015.12.29.18,some-index-2015.12.29.19,some-index-2015.12.29.20,some-index-2015.12.29.21,some-index-2015.12.29.22,some-index-2015.12.29.23,some-index-2015.12.30.00,some-index-2015.12.30.01,some-index-2015.12.30.02,some-index-2015.12.30.03,some-index-2015.12.30.04,some-index-2015.12.30.05,some-index-2015.12.30.06,some-index-2015.12.30.07,some-index-2015.12.30.08,some-index-2015.12.30.09,some-index-2015.12.30.10,some-index-2015.12.30.11,some-index-2015.12.30.12,some-index-2015.12.30.13,some-index-2015.12.30.14,some-index-2015.12.30.15,some-index-2015.12.30.16,some-index-2015.12.30.17,some-index-2015.12.30.18,some-index-2015.12.30.19,some-index-2015.12.30.20,some-index-2015.12.30.21,some-index-2015.12.30.22,some-index-2015.12.30.23,some-index-2015.12.31.00,some-index-2015.12.31.01,some-index-2015.12.31.02,some-index-2015.12.31.03,some-index-2015.12.31.04,some-index-2015.12.31.05,some-index-2015.12.31.06,some-index-2015.12.31.07,some-index-2015.12.31.08,some-index-2015.12.31.09,some-index-2015.12.31.10,some-index-2015.12.31.11,some-index-2015.12.31.12,some-index-2015.12.31.13,some-index-2015.12.31.14,some-index-2015.12.31.15,some-index-2015.12.31.16,some-index-2015.12.31.17,some-index-2015.12.31.18,some-index-2015.12.31.19,some-index-2015.12.31.20,some-index-2015.12.31.21,some-index-2015.12.31.22,some-index-2015.12.31.23,some-index-2016.01.01.00' 
        built_indexes = tattle.get_indexes(index_info, datemath('2016-01-01||-3d'), datemath('2016-01-01'))
        self.assertEqual(built_indexes, expected)


        index_info = 'some-index-%{+YYYY.MM.DD.HH}:day' 
        expected = 'some-index-2015.12.29.00,some-index-2015.12.30.00,some-index-2015.12.31.00,some-index-2016.01.01.00'
        built_indexes = tattle.get_indexes(index_info, datemath('2016-01-01||-3d'), datemath('2016-01-01'))
        self.assertEqual(built_indexes, expected)

