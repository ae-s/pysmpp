import struct
import pdu

# http://www.dreamfabric.com/sms
#
# protocol_id = 01000001 - rewrite
#
# DCS = 0000xxyy
#    xx = 00 - default alphabet
#    xx = 01 - 8bit
#    xx = 10 - UCS2
#    yy = 00 - FlashSMS
#    yy = 01 - SMS
#
# DCS = 1100x0yy
#    x = 0 - reset
#    x = 1 = set
#    yy = 00 - VoiceMail
#         01 - Fax
#         10 - Email

def convert8to7bit(str):
    """Convert 8bit string to compressed 7bit string of hex values.
    Returns string."""

    length = len(str)
    str = str + '\0'
    dp = ''
    j = 0
    while length > 0:
        bb = ord(str[j])
        i = 7
        while i > 0 and length > 0:
            bb = bb | ord(str[j+8-i]) << i
            dp = dp + chr(0xff & bb)
            bb = bb >> 8
            length = length - 1
            i = i - 1
        length = length - 1
        j = j + 8

    return dp


class SMS(pdu.PDU):
    """Encapsulates an SMS message. """
    def __init__(self, message=''):
        pdu.PDU.__init__(self)
        self.message = message
        self.esm_class = 0
        self.protocol = 0
        self.dcs = 0
        self.priority = 0
        self.src_addr = ""
        self.dest_addr = ""

    def __str__(self):
        self.body  = pdu.c_octet_string("");                #service type
        self.body += pdu.short(1);							#src_addr_ton
        self.body += pdu.short(1);							#src_addr_npi
        self.body += pdu.c_octet_string(self.src_addr);     #src_addr
        self.body += pdu.short(1);					    	#dest_addr_ton
        self.body += pdu.short(1);				    		#dest_addr_npi
        self.body += pdu.c_octet_string(self.dest_addr);    #dest_addr
        self.body += pdu.short(0);							#esm_class
        self.body += pdu.short(self.protocol);				#protocol_id
        self.body += pdu.short(self.priority);				#priority_flag
        self.body += pdu.c_octet_string("");		    	#schedule_time
        self.body += pdu.c_octet_string("");			    #validity_period
        self.body += pdu.short(0);			            	#registered_dlv
        self.body += pdu.short(0);							#replace_flag
        self.body += pdu.short(self.dcs);					#data_coding
        self.body += pdu.short(0);							#sm_def_msg
        self.body += pdu.short(len(self.message) );     	#sm_length
        self.body += pdu.c_octet_string(self.message);		#sms
        return pdu.PDU.__str__(self)

class DeliveryNotification(SMS):
    pass

class FlashSMS(SMS):
    pass

class RingTone(SMS):
    pass

class OperatorLogo(SMS):
    pass

class ESM(SMS):
    pass

class OTA(SMS):
    pass


