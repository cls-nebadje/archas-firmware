#!/usr/bin/python
# -*- coding: utf-8 -*-

import archas
import sys, getopt, datetime

# https://docs.python.org/3.3/library/argparse.html

def usage(help=False):
    print """ %s <options>
 -u <url>               Input URL to file with sensor log data
 --help=
 
 -i <infile>            Input file with sensor log data
 --infile=
 
 -p <out.pdf>           Output file name.
 --pdf= 
 
 -t <start>[-<stop>]    Specify plot range. <start> and <stop> must be of
                        the following format: %%Y.%%m.%%d[;%%H:%%M:%%S]
 --time=
 
 -d                     Use default URL
 -v                     View resulting pdf with evince 
 -h --help              Print this help message
""" % sys.argv[0]
    if not help:
        exit(1)
    else:
        exit(0)

def parseTime(tstr):
    try:
        t = datetime.datetime.strptime(tstr, '%Y.%m.%d %H:%M:%S')
    except ValueError as e:
        t = datetime.datetime.strptime(tstr, '%Y.%m.%d')
    return t

try:
    opts, args = getopt.getopt(sys.argv[1:],
                               "u:i:p:t:dvh",
                               ["url=", "infile=", "pdf=", "time=", "help"])
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
    elif opt in ("h", "help"):
        usage(True)
    elif opt in ("-t", "--time"):
        arg = arg.split("-")
        start = parseTime(arg[0])
        if len(arg) == 2:
            stop = parseTime(arg[1])
        else:
            stop = datetime.datetime.now()
        prange = stop - start

if (url is None and infile is None):
    usage()

if pdf is None and view:
    import tempfile
    _pdf = tempfile.NamedTemporaryFile(suffix=".pdf")
    pdf = _pdf.name
else:
    print "Temporary output file only available with -v"
    usage()

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

