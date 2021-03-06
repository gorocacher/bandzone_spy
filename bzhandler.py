
from google.appengine.ext import deferred
from google.appengine.runtime import DeadlineExceededError
from google.appengine.api import channel, urlfetch, memcache
from django.utils import simplejson
import logging
import traceback
from bzdataprocessor import aggregate_by_address, fillScaleAndTooltip
from bzparser import parseFanPageCount, parseFans
from cache import load_geo_from_cache



class AsyncFanDownloader():
    def handle_result(self, rpc, page, storage):
        result = rpc.get_result()
        results = parseFans(result.content)
        storage[page] = results


    def create_callback(self, rpc, page, storage):
        return lambda: self.handle_result(rpc, page, storage)

    def asyncDonwload(self, url_template, start_page, num_pages):
        chunks_dict = {}
        rpcs = []
        for page in xrange(0, num_pages):
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
            partialResults = list(chunks_dict[key])
            data_list.extend(partialResults)
            #memcache.add((url_template % key), partialResults, 30*60)
        return data_list

    def total_pages(self, url):
        return parseFanPageCount(urlfetch.fetch(url).content)



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
                self.completeAddressMap[k].fans.extend(self.currentAddressMap[k].fans)
                self.currentAddressMap[k].count = self.completeAddressMap[k].count
                #self.currentAddressMap[k].fans = self.completeAddressMap[k].fans


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

    def _get_message(self, percent):
        locations = [
            {
                'address': r.address,
                'tooltip': r.tooltip,
                'count': r.count,
                'lat': r.lat,
                'lng': r.lng,
                'found': r.found,
                'zindex': r.zindex,
                'proportion': r.proportion
            } for r in self.currentAddressMap.values()
        ]
        msg = {
            'locations': locations,
            'finished': False,
            'error': False,
            'percent': percent
        }
        return simplejson.dumps(msg)

    def _batch_write(self, percent):
        msg = self._get_message(percent)
        channel.send_message(self.client_id, msg)
        self.currentAddressMap = {}

    def finishWithError(self):
        """Called when the mapper has finished, to allow for any final work to be done."""
        msg = {'finished': True, 'error': True}
        msg = simplejson.dumps(msg)
        channel.send_message(self.client_id, msg)

    def finish(self):
        """Called when the mapper has finished, to allow for any final work to be done."""
        msg = {'finished': True, 'error': False}
        msg = simplejson.dumps(msg)
        channel.send_message(self.client_id, msg)

    def run(self, batch_size=2):
        """Starts the mapper running."""
        self.total_pages = AsyncFanDownloader().total_pages(self.url_template)
        logging.debug('Total pages: %d' % self.total_pages)
        self._continue(0, batch_size)

    def _continue(self, start_page, batch_size):
        to_be_processed = start_page
        try:
            while to_be_processed < self.total_pages:
                logging.info("Processing page: %d ------------------------" % to_be_processed)
                to_be_downloaded = min(self.total_pages - to_be_processed, batch_size)
                fans = AsyncFanDownloader().asyncDonwload(self.url_template, to_be_processed, to_be_downloaded)
                logging.info("Donwload finished for pages %d-%d" % (to_be_processed, to_be_processed + to_be_downloaded -1))

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

                logging.info("Processing finished for: %d ------------------------" % to_be_processed)
                to_be_processed += batch_size
                self._batch_write((100*to_be_processed)/self.total_pages)



        except DeadlineExceededError:
            # sand any unfinished updates to the client.
            self._batch_write((100*to_be_processed)/self.total_pages)
            # Queue a new task to pick up where we left off.
            deferred.defer(self._continue, to_be_processed, batch_size)
            return
        except BaseException:
            logging.error(traceback.format_exc())
            self.finishWithError()
            return
        self.finish()



logging.getLogger().setLevel(logging.DEBUG)
