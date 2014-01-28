# !/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import os

from django.utils import simplejson
import webapp2
from google.appengine.ext import webapp, deferred
from google.appengine.ext.webapp import template
from bzhandler import AsyncFanHandler
from cache import store_geocode, store_notfound_address
from google.appengine.api import channel



template.register_template_library('templatetags.verbatim_templatetag')

def template_path(name):
    return os.path.join(os.path.dirname(__file__), 'templates/' + name)

class MainPage(webapp.RequestHandler):
    """ Renders the main template."""
    def get(self):
        template_values = { 'title':'Bandzone SPY', }
        self.response.out.write(template.render(template_path("index.html"), template_values))


class RPCMethods:
    """ Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    """

    def Search(self, *args):
        # The JSON encoding may have encoded integers as strings.
        # Be sure to convert args to any mandatory type(s).
        bandid = args[0]
        url_template = "http://bandzone.cz/%s?fls=0&flp=%s" % (bandid, "%s")

        client_id = os.urandom(16).encode('hex')
        token = channel.create_channel(client_id)
        asyncHanler = AsyncFanHandler(url_template, client_id)
        deferred.defer(asyncHanler.run)
        return {'token': token}

    def StoreCache(self, *args):
        cache = args[0]
        notfound= args[1]
        logging.debug("Cache received:")
        logging.debug(cache)
        logging.debug(notfound)
        for i in cache:
            store_geocode(i['address'], i['lat'], i['lng'])
        for i in notfound:
            store_notfound_address(i)
        logging.debug('Cache and notfound stored.')


class RPCHandler(webapp.RequestHandler):
    """ Allows the functions defined in the RPCMethods class to be RPCed."""
    methods = RPCMethods()

    def get(self):
        func = None

        action = self.request.get('action')
        if action:
            if action[0] == '_':
                self.error(403) # access denied
                return
            else:
                func = getattr(self.methods, action, None)

        if not func:
            self.error(404) # file not found
            return

        args = ()
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args += (simplejson.loads(val),)
            else:
                break
            
        result = func(*args)
        self.response.out.write(simplejson.dumps(result))

logging.getLogger().setLevel(logging.DEBUG)
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/rpc', RPCHandler),
], debug=True)

