from google.appengine.ext import deferred
from google.appengine.runtime import DeadlineExceededError
from google.appengine.api import channel, urlfetch, memcache
from django.utils import simplejson
import logging
from bzdataprocessor import aggregate_by_address, fillScaleAndTooltip
from bzparser import BandzoneBandParser
from cache import load_geo_from_cache


class AsyncFanDownloader():
    def handle_result(self, rpc, page, storage):
        result = rpc.get_result()
        parser = BandzoneBandParser()
        results = parser.parseFans(result.content)
        storage[page] = results


    def create_callback(self, rpc, page, storage):
        return lambda: self.handle_result(rpc, page, storage)

    def asyncDonwload(self, url_template, start_page, num_pages):
        chunks_dict = {}
        rpcs = []
        for page in range(0, num_pages):
            page += start_page + 1 # pages on  bz are numbered from 1
            url = url_template % page

            data = memcache.get(url)
            if data is not None:
                chunks_dict[page] = data
            else:
                rpc = urlfetch.create_rpc(deadline = 10)
                rpc.callback = self.create_callback(rpc, page, chunks_dict)
                urlfetch.make_fetch_call(rpc, url)
                rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()

        data_list = []
        for key in chunks_dict.keys():
            data_list= data_list + chunks_dict[key]
            memcache.add(url_template % key, chunks_dict[key], 30*60)
        return data_list

    def total_pages(self, url):
        return BandzoneBandParser().parseFanPageCount(urlfetch.fetch(url).content)



class AsyncFanHandler():
    def __init__(self, url_template, client_id):
        self.url_template = url_template
        self.client_id = client_id
        self.completeAddressMap = {}
        self.currentAddressMap = {}
        self.maxcount = 1
        self.downloader = AsyncFanDownloader()
        self.total_pages = 0


    def _update_fan_list_and_count(self):
        for k in self.currentAddressMap.keys():
            if self.completeAddressMap.has_key(k):
                #update both maps
                self.completeAddressMap[k].count += self.currentAddressMap[k].count
                self.completeAddressMap[k].fans.append(self.currentAddressMap[k].fans)
                self.currentAddressMap[k].count = self.completeAddressMap[k].count
                self.currentAddressMap[k].fans = self.completeAddressMap[k].fans


    def _add_geocodes(self):
        for addr in self.currentAddressMap.keys():
            cur = self.currentAddressMap[addr]
            if self.completeAddressMap.has_key(addr):
                cur.lat = self.completeAddressMap[addr].lat
                cur.lng = self.completeAddressMap[addr].lng
                cur.found = self.completeAddressMap[addr].found
            else:
                cachedGeo = load_geo_from_cache(addr)
                if cachedGeo is not None:
                    cur.lat = cachedGeo['lat']
                    cur.lng = cachedGeo['lng']
                    cur.found = cachedGeo['found']
                else:
                    cur.found = False

    def _update_complete_map(self):
        for k in self.currentAddressMap.keys():
            if not self.completeAddressMap.has_key(k):
                self.completeAddressMap[k] = self.currentAddressMap[k]

    def _get_message(self):
        msg = {
            'locations': [r.__dict__ for r in self.currentAddressMap.values()],
            'finished': False
        }
        return simplejson.dumps(msg)

    def _batch_write(self):
        msg = self._get_message()
        channel.send_message(self.client_id, msg)
        self.currentAddressMap = {}

    def finish(self):
        """Called when the mapper has finished, to allow for any final work to be done."""
        msg = {'finished': True}
        msg = simplejson.dumps(msg)
        channel.send_message(self.client_id, msg)

    def run(self, batch_size=1):
        """Starts the mapper running."""
        self.total_pages = AsyncFanDownloader().total_pages(self.url_template)
        logging.debug('Total pages: %d' % self.total_pages)
        self._continue(0, batch_size)

    def _continue(self, start_page, batch_size):
        to_be_processed = start_page
        try:
            for page in range(start_page, self.total_pages):
                logging.debug("Processing page: %d ------------------------" % page)
                fans = AsyncFanDownloader().asyncDonwload(self.url_template, start_page, batch_size)

                # The mapUpdate object is sent to the client to render the map.
                self.currentAddressMap = aggregate_by_address(fans)
                # add geocode either from complete map or from geo cache
                self._add_geocodes()
                # update fan list and count  in both maps
                self._update_fan_list_and_count()
                # add the new values to the complete map
                self._update_complete_map()
                # fill scale and tooltip
                self.maxcount = fillScaleAndTooltip(self.currentAddressMap, self.maxcount)

                self._batch_write()
                to_be_processed = page
                logging.debug("Processing finished for: %d ------------------------" % page)

        except DeadlineExceededError:
            # sand any unfinished updates to the client.
            self._batch_write()
            # Queue a new task to pick up where we left off.
            deferred.defer(self._continue, to_be_processed, batch_size)
            return
        self.finish()



