# !/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Keznikl'


from bulkloader import fix_sys_path
fix_sys_path()

import unittest
import os
from bzparser import BandzoneFan, parseFanCount, parseFanPageCount, parseFans
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


    def tearDown(self):
        self.testbed.deactivate()

    def testParsePageCount(self):
        self.assertEqual(39, parseFanPageCount(self.testContent))

    def testParseFanCount(self):
        self.assertEqual(387, parseFanCount(self.testContent))

    def testParseFansOverview(self):
        expected = [u'/fan/mahulenapastelkova', u'/fan/irko', u'/fan/zuz9339', u'/fan/kruto1', u'/fan/maxxiok',
                    u'/fan/mattes2012', u'/fan/vintager', u'/fan/marajoo', u'/fan/fabolos', u'/fan/rumiczek',]
        self.assertEqual(expected, [f.profileUrl for f in parseFans(self.testContent)])

    def testParseFansFullInfo(self):
        html = open(os.path.join(os.path.dirname(__file__), 'fullFanTest.html'), 'r')
        expected = BandzoneFan(
            profileUrl='/fan/kruto1',
            nickName='kruto1',
            fullName='kruto1 veliky',
            address='Bratislava',
            avatarUrl='http://usr.bandzone.cz/fan/ab/36/95b1/7a/99/791e/qG2NbrjmxX8Oyahbjg1GrGfBu_VFld-G.jpg')
        self.assertEquals(expected.__dict__, parseFans(html)[0].__dict__)
