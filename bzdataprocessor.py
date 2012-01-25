# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Methods for transforming list of fans to a list of addresses with aggregated data (AddressInfo).
"""

__author__ = 'Keznikl'

from __builtin__ import float
import math

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
    """Returns the n-th root of x"""
    return x**(1.0/n)

def compute_scale_factors(max_count, min_scale, max_scale):
    """Determines the scale factor and logarithm base for computing AddressInfo.proportion.

    The proportion is computed as follows:
            proportion = log( scale_factor * (1+count)/maxcount, logarithm_base)

    The goal is to find logarithmic scaling factors that assign to the count 1 the min_scale and to max_count
    the max_scale. Therefore, havind the previous formula for computing proportion, the following holds:

        log(scale_factor * (1+1)/max_count) = min_scale            # +1 serves to avoid logarithms of 1.
        log(scale_factor * (max_count+1)/max_count) = max_scale

    Args:
        max_count (int): The maximal count value of all AddressInfo objects currently processed.
        min_scale (float): The minimum scale value.
        max_scale (float): The maximum scale value.

    Returns:
        A pair of (scale_factor, logarithm_base) for computing AddressInfo.proportion.
        The actual values are result of curve fitting.
    """
    root = (max_scale / min_scale) - 1  # grade of the employed root

    # scale_factor = root-th root of (max_count^root * (max_count + 1) / 2^(root+1))
    scale_factor = nth_root(
        math.pow(max_count, root) * (max_count + 1.0) / math.pow(2.0, root+1),
        root
    )

    logarith_base= (2*scale_factor / max_count)**(1/min_scale)
    return (scale_factor, logarith_base)

def aggregate_by_address(fans):
    """Aggregates fans according to their address.

    Fans without address are skipped.

    Args:
        fans (list[bzparser.BandzoneFan]): The fans to be aggregated.

    Returns:
        Map of AddressInfo objects, with filled attributes address, fans, and count, where the key is the address.
    """
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

def fillScaleAndTooltip(addressInfoMap, max_count):
    """Fills the tooltip, proportion, and zindex attributes of the given AddressInfo objects.

    Uses fixed min_scale and max_scale values.

    Args:
        addressInfoMap (map{address: AddressInfo}): The AddressInfo to be processed.
        max_count (int): The max_count so far encountered (if the data are processed in batches), 1 initially.

    Returns:
        The current max_count which also considers the processed AddressInfo objects.
    """
    for info in addressInfoMap.values():
        tooltipSnippets = ["<a href=\"http://www.bandzone.cz%s\" >%s</a>\n" % ( fan.profileUrl, fan.fullName) \
                           for fan in info.fans]
        info.tooltip = ", ".join(tooltipSnippets)
        # update the max_count if necessary
        if info.count > max_count:
            max_count = info.count

    # employed scale parameters
    min_scale = 0.4
    max_scale = 2

    (scale_factor, logarithm_base) = compute_scale_factors(max_count, min_scale, max_scale)
    for info in addressInfoMap.values():
        if logarithm_base == 1:
            info.proportion = 1
        else:
            info.proportion = math.log(scale_factor * (1 + float(info.count)) / float(max_count), logarithm_base)
        # the greater count, the lower z-index (smaller markers will be in front of the bigger ones)
        info.zindex = max_count - info.count
    return max_count