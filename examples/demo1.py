#! /usr/bin/env python
#
# Script to send SMS's through SMPP protocol
#

import sys, select
from pySMPP import SMPP, SMPPError, SMS

smpp = SMPP(log=sys.stderr)

smpp.connect('127.1', 10000)
smpp.bind_transmitter('user','pass')

try:
  sys.stdout.write("Enter SMS text here: ")
  sys.stdout.flush()
  while 1:
    a,b,c = select.select([sys.stdin],[],[],20)
    if len(a) > 0:
        s = raw_input()
        if s:
            sms = SMS(s)
            smpp.submit_sm(sms)
            sys.stdout.write("Enter SMS text here: ")
            sys.stdout.flush()
    else:
        smpp.enquire_link()

except KeyboardInterrupt:
    print "\nFinalizing...",
    smpp.close()
    print "Done!"
except:
    smpp.close()
    raise
