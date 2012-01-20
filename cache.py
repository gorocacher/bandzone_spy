# !/usr/bin/env python
# -*- coding: utf-8 -*-
from google.appengine.ext.db import GeoPt

__author__ = 'Keznikl'


from google.appengine.ext import db
from google.appengine.api import users, memcache


class GeocodeItem(db.Model):
    """Models an individual Geocode cache entry."""
    address = db.StringProperty()
    location = db.GeoPtProperty()
    date = db.DateTimeProperty(auto_now=True)

class NotFoundItem(db.Model):
    """Models an individual not-found addresses."""
    address = db.StringProperty()
    date = db.DateTimeProperty(auto_now=True)


def store_geocode(address, lat, lng):
    item = GeocodeItem.all().filter("address =", address).get()
    if item is None:
        item = GeocodeItem()
        item.address = address
        item.location = GeoPt(lat=lat, lon=lng)
        item.put()

def load_geo_from_cache(address):
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
    """
    Returns map of {address: {lat: number, lng: number}}
    """
    ret = {}
    for i in GeocodeItem.all():
        ret[i.address] = {
            'lat': i.location.lat,
            'lng': i.location.lon
        }

def store_notfound_address(address):
    item = NotFoundItem.all().filter("address =", address).get()
    if item is None:
        item = NotFoundItem()
        item.address = address
        item.put()

def get_notfound_addresses():
    return [i.address for i in NotFoundItem.all()]

