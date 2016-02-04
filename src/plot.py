#!/usr/bin/python
# -*- coding: utf-8 -*-

import archas
import sys, getopt, datetime

# https://docs.python.org/3.3/library/argparse.html

def usage():
    print '%s -u <url> -p <plot.pdf>' % sys.argv[0]
    print '%s -i <logfile> -p <plot.pdf>' % sys.argv[0]
    print '%s -d -t -v' % sys.argv[0]
    sys.exit(2)

try:
    opts, args = getopt.getopt(sys.argv[1:],"du:i:p:vt",["url=","infile=", "pdf="])
except getopt.GetoptError as e:
    usage()
    
url = None
infile = None
pdf = None
view = False
prange = datetime.timedelta(hours=24*2)
pend = datetime.datetime.now()

for opt, arg in opts:
    if opt in ("-u", "--url"):
        url = arg
    elif opt in ("-i", "--infile"):
        infile = arg
    elif opt in ("-p", "--pdf"):
        pdf = arg
    elif opt in ("-d"):
        url = 'http://nerdtalk.ddns.info/temperature.txt'
        print "using default URL:", url
    elif opt in ("-v"):
        view = True
    elif opt in ("-t"):
        pdf = "%s.pdf" % datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d_%H:%M")

if (url is None and infile is None):
    usage()

if pdf is None:
    import tempfile
    _pdf = tempfile.NamedTemporaryFile(suffix=".pdf")
    pdf = _pdf.name

if url:
    import urllib2
    import tempfile

    response = urllib2.urlopen(url)
    lines = response.read()

    f = tempfile.NamedTemporaryFile(suffix=".log")
    f.write(lines)
    f.flush()
    infile = f.name
    # not closing f -- will be closed on program exit

archas.temperature.graph(infile,
                         {0:u"Server", 1:u"Waschküche", 2:u"Heizraum", 3:u"Draussen"},
                         pdf,
                         plotStartDate=pend,
                         plotRange=prange)

if view:
    import commands
    s, o = commands.getstatusoutput("evince %s" % (pdf))

