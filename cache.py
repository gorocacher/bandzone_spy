# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Methods for manipulating the data cache storage.
The data being stored:
    Geocodes for addresses found by the client (GeocodeItem).
    Addresses not found by the client (NotFoundItem).
"""

__author__ = 'Keznikl'

from google.appengine.ext.db import GeoPt
from google.appengine.ext import db
from google.appengine.api import users, memcache

class GeocodeItem(db.Model):
    """A single Geocode cache entry.

    Attributes:
        address (str): The actual address.
        location (GeoPt): The geocode of the address.
        date (DateTime): The date of the last change, automatically updated.
    """
    address = db.StringProperty()
    location = db.GeoPtProperty()
    date = db.DateTimeProperty(auto_now=True)

class NotFoundItem(db.Model):
    """A single not-found address.

    Attributes:
        address (str): The actual address.
        date (DateTime): The date of the last change, automatically updated.
    """
    address = db.StringProperty()
    date = db.DateTimeProperty(auto_now=True)


def store_geocode(address, lat, lng):
    """Stores the given address latitude and longitude (if not present).

    Args:
        address (str): The address to be stored.
        lat (float): The latitude of the address.
        lng (float): The longitude of the address.
    """
    item = GeocodeItem.all().filter("address =", address).get()
    if item is None:
        item = GeocodeItem()
        item.address = address
        item.location = GeoPt(lat=lat, lon=lng)
        item.put()

def store_notfound_address(address):
    """Stores the given address latitude and longitude (if not present).

    Args:
        address (str): The address to be stored.
    """
    item = NotFoundItem.all().filter("address =", address).get()
    if item is None:
        item = NotFoundItem()
        item.address = address
        item.put()

def load_geo_from_cache(address):
    """Loads  the stored (found/not-found) address.

    Uses memcache to store previously found entries.

    Args:
        address (str): The address to be loaded.

    Returns:
        A map containing both indication of found/not-found and latitude and longitude in the positive case.
        Example = {
                'lat': 1.435435,
                'lng': -1.432432,
                'found': True
            }
        If not in cache, all the fields are set to None.
    """
    result = memcache.get(address)
    if result is not None:
        return result

    item = GeocodeItem.all().filter("address =", address).get()
    if item is None:
        item = NotFoundItem.all().filter("address =", address).get()
        if item is None:
            return {
                'lat': None,
                'lng': None,
                'found': None
            }
        else:
            result = {
                'lat': None,
                'lng': None,
                'found': False
            }
    else:
        result = {
            'lat': item.location.lat,
            'lng': item.location.lon,
            'found': True
        }
    memcache.add(address, result, 30*60)
    return result

def get_geocodes():
    """ Returns map of {address: {lat: number, lng: number}}

    DEPRECATED
    """
    ret = {}
    for i in GeocodeItem.all():
        ret[i.address] = {
            'lat': i.location.lat,
            'lng': i.location.lon
        }

def get_notfound_addresses():
    """ Returns the list of not-found addresses.

    DEPRECATED
    """
    return [i.address for i in NotFoundItem.all()]

