# !/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

__author__ = 'Keznikl'

import re
from BeautifulSoup import BeautifulSoup

class AddressInfo():
    def __init__(self, address=None, tooltip='', count=0, lat = None, lng = None):
        self.address = address
        self.tooltip = tooltip
        self.count = count
        self.lat = lat
        self.lng = lng
        self.fans = []

def aggregate_by_address(fans):
    infos = {}
    for fan in fans:
        if fan.address is None:
            continue;
        if not infos.has_key(fan.address):
            infos[fan.address] = AddressInfo(address = fan.address)
        info = infos[fan.address]
        info.fans.append(fan)
        info.count += 1;

    result = {}
    for address in infos.keys():
        info = infos[address]
        tooltipSnippets = ["<tr><td><a href=\"http://www.bandzone.cz%s\" ><img src=\"%s\" /></a></td>" % (fan.profileUrl, fan.avatarUrl) +\
                           "<td><a href=\"http://www.bandzone.cz%s\" >%s</a></td></tr>\n" % ( fan.profileUrl, fan.fullName)\
                           for fan in info.fans]
        info.tooltip = "<div>%s (%d)</div>" % (address, info.count) + "<table>" + reduce(lambda x,y: x + y, tooltipSnippets) + "</table>"
        delattr(info, 'fans')
        result[address] = info
    return result