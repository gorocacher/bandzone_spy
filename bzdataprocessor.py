# !/usr/bin/env python
# -*- coding: utf-8 -*-
from __builtin__ import float

__author__ = 'Keznikl'

import math

"""
Methods for transforming list of fans to a list of addresses with aggregated data (AddressInfo).
"""

class AddressInfo():
    """Aggregated data for a single address.

    Can contain only partial data, specific for a part of the band fans currently processed.
    The partial data is completed on the client side.

    Attributes:
        address (str): The address.
        tooltip (str): The names and profile URLs of the (subset of) fans with this address.
        count (int): The number of the (subset of) fans with this address.
        lat (float): Latitude of the address.
        lng (float): Longitude of the address.
        found (bool): True if the position of the address address was found by a Geocode service and was in the
            geocode cache, False if not found by the Geocode service but in cache, None otherwise.
        fans (list[bzparser.BandzoneFan]): A list of the (subset of) fans with this address.
        zindex (int): The z-index of the marker for this address (based on the count).
        proportion (float): The proportion of the marker (based on the count).
    """
    def __init__(self, address=None, tooltip='', count=0, lat = None, lng = None, found = False):
        self.address = address
        self.tooltip = tooltip
        self.count = count
        self.lat = lat
        self.lng = lng
        self.found = found
        self.fans = []
        self.zindex = 0
        self.proportion = 1


def nth_root(x,n):
# function to return the n-th root of x
    return x**(1.0/n)

def compute_scale_factors(max_count, min_scale, max_scale):
    root = (max_scale / min_scale) - 1
    # scale_factor = 3th root (max_count^3 * (max_count + 1) / 2^3)
    scale_factor = nth_root(float(math.pow(max_count, root) * (max_count + 1) / math.pow(2.0, max_scale/min_scale)), root)
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
    return infos

def fillScaleAndTooltip(addressInfoMap, maxcount):
    for info in addressInfoMap.values():
        tooltipSnippets = ["<a href=\"http://www.bandzone.cz%s\" >%s</a>\n" % ( fan.profileUrl, fan.fullName) \
                           for fan in info.fans]
        info.tooltip = ", ".join(tooltipSnippets)
        #delattr(info, 'fans')
        if info.count > maxcount:
            maxcount = info.count

    min_scale = 0.4
    max_scale = 2
    (scale_factor, logarithm_base) = compute_scale_factors(maxcount, min_scale, max_scale)


    for info in addressInfoMap.values():
        if logarithm_base == 1:
            info.proportion = 1
        else:
            info.proportion = math.log(scale_factor * (1 + float(info.count)) / float(maxcount), logarithm_base)
        info.zindex = maxcount - info.count
    return maxcount