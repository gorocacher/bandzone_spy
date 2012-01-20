# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Keznikl'

from bulkloader import fix_sys_path
fix_sys_path()

import unittest
import math
from google.appengine.ext import testbed
from bzdataprocessor import compute_scale_factors

class ProcessTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()

    def tearDown(self):
        self.testbed.deactivate()

    def testScaleFactors(self):
        min_scale = 0.5
        max_scale = 2
        max_count = 2
        (scale_factor, logarith_base) = compute_scale_factors(max_count, min_scale, max_scale)
        self.assertAlmostEqual(min_scale, math.log(scale_factor  * 2.0 / max_count, logarith_base))
        self.assertAlmostEqual(max_scale, math.log(scale_factor  * (max_count + 1.0) / float(max_count), logarith_base))

    def testScaleFactors(self):
        min_scale = 0.5
        max_scale = 2
        max_count = 1
        (scale_factor, logarith_base) = compute_scale_factors(max_count, min_scale, max_scale)
        self.assertNotEqual(0, scale_factor)
        self.assertNotEqual(1, logarith_base)
        self.assertAlmostEqual(min_scale, math.log(scale_factor  * 2.0 / max_count, logarith_base))