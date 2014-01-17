#!/usr/bin/python
"""
See README.md

Compatible with python 2.4+
"""

import urllib2
import logging
import simplejson as json
import sys
import os
from optparse import OptionParser
from operator import itemgetter

try:
    import pygmaps
except ImportError:
    pass

""" Edit these items: """
#spot_id = "0Vn4kA4MiPgNSYD52NgPjuVJDpUCSUlGW"
spot_id = "0W8hq7UcGlKSuEszhPnJXzPMTlgRJgFhP"
last_latlon_cache = "/Users/charlie/lastspotlocation.txt"
json_cache = "/Users/charlie/spotlocations.json"
xml_cache = "/Users/charlie/spotlocations.xml"
map_output = "/Users/charlie/mymap.html"

url = "https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/%s/message" % spot_id


def merge_tracks(a, b):
    """ merges tracks (b) into (a), skipping those with the same timestamp.
    Sorts by unixTime key.
    """
    if a is None:  # there were no tracks in the file
        a = []
        a_times = []
    else:
        a_times = [track['unixTime'] for track in a]

    return sorted(a + [track for track in b
                       if track['unixTime'] not in a_times
                      ],
                  key=itemgetter('unixTime'), reverse=True
                 )

def do_map(json_output, options):
    """ Creates a google map HTML page with points plotted for every point in known,
    and draws a line between each.
    """
    gmap = pygmaps.maps(json_output[0]['latitude'], json_output[0]['longitude'], options.map_zoom)
    for track in json_output:
        gmap.addpoint(track['latitude'], track['longitude'], "#0000FF")

    logging.debug("All points: %s" % [(track['latitude'], track['longitude']) for track in json_output])
    gmap.addpath([(track['latitude'], track['longitude']) for track in json_output])
    gmap.draw(map_output)

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-d", "--debug", help="print debug messages", action="store_true")
    parser.add_option("-k", "--keep-json-tracks", help="keep all tracks until file is moved",
                      action="store_true")
    parser.add_option("-m", "--map", help="generates a google map with all points (and draws a line between them)",
                      action="store_true")
    parser.add_option("--map-zoom", help="zoom level for map", default=12)
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

    if os.path.exists(json_cache):
        fh = open(json_cache, 'r')
        try:
            tracks = json.load(fh)
            logging.debug("Got %s tracks from JSON cache file." % len(tracks))
        except ValueError, err:
            logging.debug(err)
            tracks = None
        fh.close()
    else:
        tracks = []

    if options.keep_json_tracks:
        json_output = merge_tracks(tracks, api_tracks)
        logging.debug("Merged API and cache tracks into %s tracks." % len(json_output))
    else:
        json_output = api_tracks
        logging.debug("Writing %s API tracks into cache." % len(json_output))
    fh = open(json_cache, 'w')
    json.dump(json_output, fh)
    fh.close()

    # draw the google map:
    if options.map:
        do_map(json_output, options)

    # write all messages returned from spot API as XML:
    fh = open(xml_cache, 'w')
    fh.write(str(xml_response))
    fh.close()


