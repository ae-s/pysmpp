#! /usr/bin/env python
#
# Script that receives SMS's through SMPP protocol
#

import sys
from pySMPP import SMPP, SMPPError, SMS

def mydeliver(pdu):
    """Callback function. It receives the SMS's"""
    resp = pdu.response(status=0x00)
    resp.command_id=0x80000000
    print pdu.dump()
    print resp.dump()
    return resp

smpp = SMPP(log=sys.stderr)

smpp.connect('127.1', 10000)
smpp.bind_receiver('user','pass')

smpp.deliver_sm = mydeliver

try:
  while 1:
    print "wait..."
    smpp.process(20)
    smpp.enquire_link()
except KeyboardInterrupt:
    print "\nFinalizing...",
    smpp.close()
    print "Done!"
except:
    smpp.close()
    raise

