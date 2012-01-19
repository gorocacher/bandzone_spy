# !/usr/bin/env python
# -*- coding: utf-8 -*-
import math

__author__ = 'Keznikl'

from __builtin__ import delattr


class AddressInfo():
    def __init__(self, address=None, tooltip='', count=0, lat = None, lng = None):
        self.address = address
        self.tooltip = tooltip
        self.count = count
        self.lat = lat
        self.lng = lng
        self.fans = []


def nth_root(x,n):
# function to return the n-th root of x
    return x**(1.0/n)

def compute_scale_factors(max_count, min_scale, max_scale):
    root = (max_scale / min_scale) - 1
    # scale_factor = 3th root (max_count^3 * (max_count + 1) / 2^3)
    scale_factor = nth_root(math.pow(max_count, root) * (max_count + 1) / math.pow(2.0, max_scale/min_scale), root)
    # logarith_base = (2scale_factor / max_count)^2)
    logarith_base= math.pow(2*scale_factor / max_count, 1/min_scale)
    return (scale_factor, logarith_base)

def aggregate_by_address(fans):
    infos = {}
    for fan in fans:
        if fan.address is None:
            continue
        if not infos.has_key(fan.address):
            infos[fan.address] = AddressInfo(address = fan.address)
        info = infos[fan.address]
        info.fans.append(fan)
        info.count += 1

    result = {}
    maxcount = 0
    for address in infos.keys():
        info = infos[address]
        tooltipSnippets = ["<a href=\"http://www.bandzone.cz%s\" >%s</a></td></tr>\n" % ( fan.profileUrl, fan.fullName) \
                           for fan in info.fans]
        info.tooltip = "<div>%s (%d)</div>" % (address, info.count) + "<table>" + ", ".join(tooltipSnippets) + "</table>"
        delattr(info, 'fans')
        if info.count > maxcount:
            maxcount = info.count
        result[address] = info

    min_scale = 0.5
    max_scale = 2
    (scale_factor, logarith_base) = compute_scale_factors(maxcount, min_scale, max_scale)

    for info in result.values():
        info.proportion = math.log(scale_factor * (1 + float(info.count)) / float(maxcount), logarith_base)
        info.zindex = maxcount - info.count
    return result