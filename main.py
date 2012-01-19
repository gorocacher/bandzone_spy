# !/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import os

from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from bzparser import BandzoneBandParser
from bzdataprocessor import aggregate_by_address
from cache import get_geocodes, store_geocode
from google.appengine.api import urlfetch, memcache

from google.appengine.ext.webapp import template
from cache import get_geocodes


template.register_template_library('templatetags.verbatim_templatetag')

def template_path(name):
    return os.path.join(os.path.dirname(__file__), 'templates/' + name)

class MainPage(webapp.RequestHandler):
    """ Renders the main template."""
    def get(self):
        template_values = { 'title':'Bandzone SPY', }
        self.response.out.write(template.render(template_path("index.html"), template_values))


class RPCHandler(webapp.RequestHandler):
    """ Allows the functions defined in the RPCMethods class to be RPCed."""
    def __init__(self):
        webapp.RequestHandler.__init__(self)
        self.methods = RPCMethods()

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


class AsyncFanDownloader():


    def handle_result(self, rpc, page, storage):
        result = rpc.get_result()
        parser = BandzoneBandParser()
        results = parser.parseFans(result.content)
        storage[page] = results
        logging.debug("Parsed fans for page %d:" % (page))
        logging.debug([f.fullName for f in storage[page]])

    def create_callback(self, rpc, page, storage):
        return lambda: self.handle_result(rpc, page, storage)

    def asyncDonwload(self, url_template, total_pages):
        chunks_dict = {}
        rpcs = []
        for page in range(1, total_pages + 1):
            url = url_template % page

            data = memcache.get(url)
            if data is not None:
                logging.debug("Using cache for '%s'. *********************" % url)
                chunks_dict[page] = data
            else:
                rpc = urlfetch.create_rpc(deadline = 10)
                rpc.callback = self.create_callback(rpc, page, chunks_dict)
                urlfetch.make_fetch_call(rpc, url)
                rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()

        page_keys = chunks_dict.keys()
        logging.debug("keys: ***************************")
        logging.debug(page_keys)
        data_list = []
        for key in page_keys:
            data_list= data_list + chunks_dict[key]
            memcache.add(url_template % key, chunks_dict[key], 30*60)

        logging.debug("data_list: ***************************")
        logging.debug([[i.fullName, i.address] for i in data_list])
        return data_list


class RPCMethods:
    """ Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    """

    def Search(self, *args):
        # The JSON encoding may have encoded integers as strings.
        # Be sure to convert args to any mandatory type(s).
        bandid = args[0]
        url = "http://bandzone.cz/%s?fls=0&flp=%s" % (bandid, "%s")
        totalPages = BandzoneBandParser().parseFanPageCount(urlfetch.fetch(url).content)
        fans = AsyncFanDownloader().asyncDonwload(url, 1)

        resultMap = aggregate_by_address(fans)
        cache = get_geocodes()
        #Now merge the parsed address data and the geocode cache
        for c in cache:
            address = c['address']
            if resultMap.has_key(address):
                resultMap[address].lat = c['lat']
                resultMap[address].lng = c['lng']
        return [r.__dict__ for r in resultMap.values()]

    def StoreCache(self, *args):
        cache = args[0]
        logging.debug("Cache received:")
        logging.debug(cache)
        for i in cache:
            store_geocode(i['address'], i['lat'], i['lng'])
        logging.debug('Cache stored.')


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    app = webapp.WSGIApplication([
        ('/', MainPage),
        ('/rpc', RPCHandler),
    ], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()