# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Keznikl'

import unittest
import os
from bzparser import BandzoneBandParser

from bulkloader import fix_sys_path

fix_sys_path()
from google.appengine.ext import testbed

class ParseTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        self.testPage = os.path.join(os.path.dirname(__file__), 'coders.html')
        f = open(self.testPage, 'r')
        self.testContent = f.read()
        self.parser = BandzoneBandParser()

    def tearDown(self):
        self.testbed.deactivate()

    def testParsePageCount(self):
        self.assertEqual(39, self.parser.parseFanPageCount(self.testContent))

    def testParseFans(self):
        expected = [u'/fan/mahulenapastelkova', u'/fan/irko', u'/fan/zuz9339', u'/fan/kruto1', u'/fan/maxxiok',
                    u'/fan/mattes2012', u'/fan/vintager', u'/fan/marajoo', u'/fan/fabolos', u'/fan/rumiczek',]
        self.assertEqual(expected, self.parser.parseFans(self.testContent))