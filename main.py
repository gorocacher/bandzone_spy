# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from BeautifulSoup import BeautifulSoup
from google.appengine.api import urlfetch
import re

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

    def parse_fans(self, html):
        soup = BeautifulSoup(html)
        results = soup.find(id="snippet-fanList-fanList")
        links = results.findAll(attrs={'title' : re.compile(u"Přejít na profil.*")})
        items = []
        for link in links:
            item = link['href']
            items.append(item)
        return items

    def handle_result(self, rpc, page, storage):
        result = rpc.get_result()
        storage[page] = self.parse_fans(result.content)

    def create_callback(self, rpc, page, storage):
        return lambda: self.handle_result(rpc, page, storage)



    def asyncDonwload(self, url_template, total_pages):
        chunks_dict = {}
        rpcs = []
        for page in range(1, total_pages):
            rpc = urlfetch.create_rpc(deadline = 10)
            rpc.callback = self.create_callback(rpc, page, chunks_dict)
            urlfetch.make_fetch_call(rpc, url_template % page)
            rpcs.append(rpc)
            if page > total_pages:
                break
            else:
                page = page +1
        for rpc in rpcs:
            rpc.wait()

        page_keys = chunks_dict.keys()
        page_keys.sort()
        data_list = []
        for key in page_keys:
            data_list= data_list + chunks_dict[key]
        return data_list


class RPCMethods:
    """ Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    """

    def Search(self, *args):
        # The JSON encoding may have encoded integers as strings.
        # Be sure to convert args to any mandatory type(s).
        bandid = args[0]
        url = "http://bandzone.cz/%s?fls=%s" % (bandid, "%s")

        items = AsyncFanDownloader().asyncDonwload(url, 10)

        return items.__str__()


def main():
    app = webapp.WSGIApplication([
        ('/', MainPage),
        ('/rpc', RPCHandler),
    ], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()