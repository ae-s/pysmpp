# This file is part of pySMPP
# Copyright (C) 2003 Damjan Georgievski
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

"""This module provides the class SMPP wich is used for low-level SMPP
access.

Example:
    import smpp
    sm = smpp.SMPP()
    sm.connect(ip,port)
    sm.bind_receiver(user,paswd)
    sm.submit_sm(pdu1)
    sm.enquire_link
    sm.submit_sm(pdu2)
    sm.unbind()
    sm.close()

supported SMPP commands:
 + bind_receiver
 + bind_transmiter
 + unbind
 + enquire_link
 + submit_sm

TODO:
 - deliver_sm (issued by SMSC)
 - query_sm
 - generic_nack
 - cancel_sm
 - sequence_number - property - done!
 - Logging
 - Better documentation

unsupported (maybe):
 - bind_transciever
 - replace_sm
 - submit_multi
 - data_sm
 - outbind (issued by SMSC)
 - alert_notification (issued by SMSC)
Doesn't support optional parameters (no v3.4)
It works syncronously.
"""
import struct
import socket, select
import pdu

COMMAND_ID = {
    'generic_nack' :        0x80000000,
    'bind_receiver' :       0x00000001,
    'bind_receiver_resp' :  0x80000001,
    'bind_transmitter' :    0x00000002,
    'bind_transmitter_resp':0x80000002,
    'query_sm' :            0x00000003,
    'query_sm_resp' :       0x80000003,
    'submit_sm' :           0x00000004,
    'submit_sm_resp' :      0x80000004,
    'deliver_sm' :          0x00000005,
    'deliver_sm_resp' :     0x80000005,
    'unbind' :              0x00000006,
    'unbind_resp' :         0x80000006,
    'replace_sm' :          0x00000007,
    'replace_sm_resp' :     0x80000007,
    'cancel_sm' :           0x00000008,
    'cancel_sm_resp' :      0x80000008,
    'bind_tranceiver' :     0x00000009,
    'bind_tranceiver_resp': 0x80000009,
    'outbind' :             0x0000000B,
    'submit_multi' :        0x00000021,
    'submit_multi_resp' :   0x80000021,
    'alert_notification' :  0x00000102,
    'data_sm' :             0x00000103,
    'data_sm_resp' :        0x80000103,
    'enquire_link' :        0x00000015,
    'enquire_link_resp' :   0x80000015,
}

STATE = {
    'CLOSED'    : -1,
    'OPEN'      :  0,
    'BOUND_RX'  :  1,
    'BOUND_TX'  :  2,
    'BOUND_TRX' :  9
}
BOUND = [ STATE["BOUND_TX"], STATE["BOUND_RX"], STATE["BOUND_TRX"] ]

class SMPPError(Exception):
    def __init__(self, value='Unknown SMPP error.'):
        self.value = value
    def __str__(self):
        if isinstance(self.value, pdu.PDU):
            return 'Command_id: 0x%08x; Command_status: 0x%08x.' % (
                self.value.command_id, self.value.command_status)
        else:
            return str(self.value)

class SMPP(object):
    def __init__(self, log=None):
        self.__state = STATE["CLOSED"]
        self.__sock = None
        self.__log = log
        self.__sequence = 0
        self.system_type = ''
        self.addr_ton = 0
        self.addr_npi = 0
        self.addr_range = ''
        self.smpp_version = 0
        return

    def getseq(self):
        self.__sequence += 1
        return self.__sequence
        
    sequence = property(getseq, doc="SMPP pdu sequence number. autoincrements each time it is requested")

    def unbind(self):
        if self.__state not in BOUND:
            return
        unbind = pdu.PDU()
        unbind.command_id = COMMAND_ID['unbind']
        unbind.sequence_number = self.sequence
        self.__writePdu(unbind)
        resp = self.__readPdu()
        if not self.__checkResponse(unbind, resp):
            raise SMPPError, "Error in unbind command. State still OPEN"
        self.__state = STATE['OPEN']
        return

    def __checkResponse(self, pdu, resp):
        return (pdu.command_id + 0x80000000 == resp.command_id) and \
            (pdu.sequence_number == resp.sequence_number) and \
             (resp.command_status == 0)

    def bind_receiver(self, user, pasw):
        if self.__state != STATE['OPEN']:
            raise SMPPError, "State is not OPEN"
        bind = pdu.BIND_RX(user,pasw)
        bind.sequence_number = self.sequence
        self.__writePdu(bind)
        resp = self.__readPdu()
        if not self.__checkResponse(bind,resp):
            raise SMPPError, resp
        self.__state = STATE['BOUND_RX']
        self.system_name = resp.body[:-1]
        return

    def bind_transmitter(self, user, pasw):
        if self.__state != STATE['OPEN']:
            raise SMPPError, "State is not OPEN"
        bind = pdu.BIND_TX(user,pasw)
        bind.sequence_number = self.sequence
        self.__writePdu(bind)
        resp = self.__readPdu()
        if not self.__checkResponse(bind,resp):
            raise SMPPError, resp
        self.__state = STATE['BOUND_TX']
        self.system_name = resp.body[:-1]
        return

    def enquire_link(self):
        enquire = pdu.PDU()
        enquire.command_id = COMMAND_ID['enquire_link']
        enquire.sequence_number = self.sequence
        self.__writePdu(enquire)
        resp = self.__readPdu()
        if not self.__checkResponse(enquire,resp):
            raise SMPPError, resp
        return

    def submit_sm(self, sms):
        sms.sequence_number = self.sequence
        sms.command_id = COMMAND_ID['submit_sm']
        self.__writePdu(sms)
        
#        nack = pdu.PDU()
#        nack.command_id = COMMAND_ID['generic_nack']
#        nack.sequence_number = self.sequence
#        self.__writePdu(nack)

        resp = self.__readPdu()
        if not self.__checkResponse(sms,resp):
            raise SMPPError, resp
        return resp.body[:-1]

    def deliver_sm(self, pdu):
        """deliver_sm(self, pdu) -> PDU()\nOverride this method."""
        resp = pdu.response(body="\0")
        return resp

    def data_sm(self, pdu):
        """data_sm(self, pdu) -> PDU()\nOverride this method."""
        resp = pdu.response(body="\0")
        return resp

    # more SMPP commands ???

    def dispatch(self):
        sms = self.__readPdu()
        cid = sms.command_id
        if cid == COMMAND_ID['enquire_link']:
            cb = lambda pdu: pdu.response()
        elif cid == COMMAND_ID['deliver_sm']:
            cb = self.deliver_sm
        elif cid == COMMAND_ID['data_sm']:
            cb = self.data_sm
        else:
            cb = lambda pdu: pdu.response(cid=0x80000000)
#        try:
        resp = cb(sms)
#        except:
#            resp.command_status, resp.body = 0x0B, None
#            self.__writePdu(resp)
#            raise
#        else:
        self.__writePdu(resp)
        return

    def log_info(self, s):
        log = self.__log
        if log: print >>log, s
        log.flush()

    def log_debug(self, s):
        log = self.__log
        if log: print >>log, s
        log.flush()

    def process(self, timeout=None):
        a,b,c = select.select([self], [], [self], timeout)
        if len(c) > 0: # ako ima specialen efekt?FIXME?
            print "ERROR?!?"
        elif len(a) > 0: # ako ima za citanje -> dispatch
            self.dispatch()

    def connect(self, addr, port):
        if self.__state != STATE["CLOSED"]:
            return
        self.__sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.__sock.connect((addr,int(port)))
        self.__state = STATE["OPEN"]
        return

    def fileno(self):
        return self.__sock.fileno()

    def close(self):
        if self.__state in BOUND:
            self.unbind()
        if self.__state != STATE["OPEN"]:
            return
        self.__sock.close()
        self.__state = STATE["CLOSED"]
        return

    def __writePdu(self, p):
        self.log_debug(p.dump())
        msg = str(p)
        totalsent = 0
        while totalsent < len(msg):
            sent = self.__sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError, "socket connection broken"
            totalsent = totalsent + sent
        return

    def __readPdu(self):
        msg = ''
        # get the first 4 bytes (PDU length)
        length = 4
        while length > 0:
            chunk = self.__sock.recv(length)
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk
            length = length - len(chunk)
        (length,) = struct.unpack('>i', msg)
        if length < 16 or length > 254:
            raise pdu.PDUError("Illegal PDU length! length=%x." % length)
        # get the rest of the PDU
        length = length - 4
        while length > 0:
            chunk = self.__sock.recv(length)
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk
            length = length - len(chunk)
        p = pdu.PDU(msg)
        self.log_debug(p.dump())
        return p
