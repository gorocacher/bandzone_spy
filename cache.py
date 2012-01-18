# !/usr/bin/env python
# -*- coding: utf-8 -*-
from google.appengine.ext.db import GeoPt

__author__ = 'Keznikl'


from google.appengine.ext import db
from google.appengine.api import users


class GeocodeItem(db.Model):
    """Models an individual Geocode cache entry."""
    address = db.StringProperty()
    location = db.GeoPtProperty()
    date = db.DateTimeProperty(auto_now=True)

def store_geocode(address, lat, lng):
    item = GeocodeItem.all().filter("address =", address).get()
    if item is None:
        item = GeocodeItem()
        item.address = address
        item.location = GeoPt(lat=lat, lon=lng)
        item.put()

def get_geocodes():
    return [{
        'address': i.address,
        'lat': i.location.lat,
        'lng': i.location.lon}
    for i in GeocodeItem.all()]
