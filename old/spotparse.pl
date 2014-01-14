#!/usr/bin/perl
# Script to fetch the latest GPS location from SPOT's API, and save it (because they don't),
# and then generate a javascript file that will write out the html needed to provide a linked 
# static google maps image. This is to avoid forcing joomla/wordpress/etc to execute php code -
# as long as you can include the generated js file via javascript, it'll work.
# Author: Charlie Schluting <charlie@schluting.com> (c) 2011
#
use XML::Simple;
#use strict.. heh, no, this barely works.

# update these:
$CACHEFILE = "/home/charlie/lastspotlocation.txt";
$JS = "/stash/www/charlierides.com/files/map.js";
$XML = "/home/charlie/spot.xml";

# fetch the XLM from your URL (latest tracks) -- UPDATE THIS TO YOUR URL
`wget -q -O $XML http://share.findmespot.com/messageService/guestlinkservlet?glId=0Vn4kA4MiPgNSYD52NgPjuVJDpUCSUlGW`;

# create object
$xml = new XML::Simple;
# read XML file
$data = $xml->XMLin("$XML");

# this is how we overcome spot's API not keeping >30 days. If they've aged out, do nothing (i.e. keep using the old data).
print "totalCount of messages is $data->{totalCount}";
exit 0 unless $data->{totalCount} > 0;
#die("No messages found, totalCount is 0, ABORTING LIKE AN UGLY KID") unless $data->{totalCount} > 0;

# the first object is always the most recent:
$lat = $data->{message}->[0]->{latitude};
$long = $data->{message}->[0]->{longitude};

# just because (hey, what if something else wants to use this?)
open(FILE, ">$CACHEFILE");
print FILE $lat . "," . $long . "\n";
close(FILE);

# STOP here. You probably simply want to write out an html snippet with a google URL, that you can include via an iframe.
# continue below to do crazy JS-that-creates-HTML dance (actually this is useful if you use joomla)

# ugly shit that writes out javascript to write out html, to include a linked static google maps image
$googleoptions = "&zoom=8&size=140x152&sensor=false&maptype=hybrid";
$googlelink = "<a target=\"blank\" href=\"http://maps.google.com/maps?q=" . $lat . "," . $long . "+(charlie)&z=8&t=h\"\>";
$header = "<p>Current location (since the last GPS update):</p>";
$js = 'document.write(\''. $header .'\');' . ' 
document.write(\''. $googlelink .'\');' . ' 
document.write(\'<img src="http://maps.googleapis.com/maps/api/staticmap?center=' . $lat .
        ',' . $long . $googleoptions . '" />\');
document.write(\'</a>\');
document.write(\'<p>Or <a href="http://share.findmespot.com/shared/faces/viewspots.jsp?glId=0Vn4kA4MiPgNSYD52NgPjuVJDpUCSUlGW" target=blank>view all recent tracks.</a></p> \');
';
open(FILE, ">$JS");
print FILE $js;
close(FILE);

