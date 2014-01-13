#!/usr/bin/python
"""
Script to fetch SPOT url and:
    1) save lat,lon coordinates to a file,
    2) save all spot messages as JSON,
    3) and xml as well.
Files get re-written on every run, if there's new data.
Oh, it also writes to stderr if batteryState isn't GOOD - so if you run from cron,
you'll get email when your spot batteries need to be changed.

Compatible with python 2.4+
"""

import urllib2
import logging
import simplejson as json
import sys
from optparse import OptionParser

""" Edit these items: """
#spot_id = "0Vn4kA4MiPgNSYD52NgPjuVJDpUCSUlGW"
spot_id = "0W8hq7UcGlKSuEszhPnJXzPMTlgRJgFhP"
last_latlon_cache = "/Users/charlie/lastspotlocation.txt"
json_cache = "/Users/charlie/spotlocations.json"
xml_cache = "/Users/charlie/spotlocations.xml"

url = "https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/%s/message" % spot_id


def merge_tracks(a, b):
    """ Appends tracks in (b) into (a), skipping those with the same timestamp. """
    if a is None:  # there were no tracks in the file
        a = []
        a_times = []
    else:
        a_times = [track['unixTime'] for track in a]

    return a + [track for track in b
                if track['unixTime'] not in a_times
               ]

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-d", "--debug", help="print debug messages", action="store_true")
    parser.add_option("-k", "--keep-json-tracks", help="keep all tracks until file is moved",
                      action="store_true")
    (options, args) = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        response = urllib2.urlopen(url)
        data = json.load(response)
        xml_response = urllib2.urlopen(url + ".xml").read()
    except Exception, err:
        # the API isn't always reliable.. exit silently
        sys.stdout.write("ERROR retreiving URL: %s" % err)
        sys.exit(1)

    if 'errors' in data.get('response', {}):
        sys.stdout.write(str(data['response']['errors']))
        sys.exit(0)
    else:
        try:
            data = data['response']['feedMessageResponse']
        except KeyError:
            sys.stderr.write("ERROR: JSON received from URL contains no feedMessageResponse,"
                             " but response->errors wasn't populated. WAT.")
            sys.exit(0)

        count = int(data.get('count', 0))
        last_message = data.get('messages', {}).get('message', {})[0]

        # write to stderr (so you get cron mail) if batteryState is not GOOD.
        if 'GOOD' not in last_message.get('batteryState', 'GOOD'):
            sys.stderr.write("WARNING: spot battery is in state: %s" % last_message.get('batteryState'))

        # write the last lat,lon to a file:
        fh = open(last_latlon_cache, 'w')
        fh.write("%s,%s" % (last_message.get('latitude', 0), last_message.get('longitude', 0)))
        fh.close()

        # write all messages returned from spot API as JSON (appending to existing, if enabled):
        api_tracks = data.get('messages', {}).get('message', {})
        logging.debug("Got %s tracks from SPOT API." % len(api_tracks))

        fh = open(json_cache, 'r')
        try:
            tracks = json.load(fh)
            logging.debug("Got %s tracks from JSON cache file." % len(tracks))
        except ValueError, err:
            logging.debug(err)
            tracks = None
        fh.close()

        if options.keep_json_tracks:
            json_output = merge_tracks(tracks, api_tracks)
            logging.debug("Merged API and cache tracks into %s tracks." % len(json_output))
        else:
            json_output = api_tracks
            logging.debug("Writing %s API tracks into cache." % len(json_output))
        fh = open(json_cache, 'w')
        json.dump(json_output, fh)
        fh.close()


        # write all messages returned from spot API as XML:
        fh = open(xml_cache, 'w')
        fh.write(str(xml_response))
        fh.close()


