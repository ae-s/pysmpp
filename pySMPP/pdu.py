# TODO: 
#   - use python properties for command_length?
# 
#
import struct

class PDUError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return `self.value`

class PDU(object):
    def __init__(self, s='\0\0\0\x10\0\0\0\0\0\0\0\0\0\0\0\0'):
        self.decompile(s)

    def decompile(self, s):
        if len(s) < 16:
            raise PDUError("Illegal PDU (length too short)")
        ( self.command_length,
          self.command_id,
          self.command_status,
          self.sequence_number )  =  struct.unpack('>iiii',s[0:16])
        l = len(s[16:])
        if l > 0:
            self.body = struct.unpack(`l`+'s',s[16:])[0]
        else:
            self.body = None
        return

    def response(self, cid=None,status=0x00,body=None):
        p = PDU()
        if cid:
            p.command_id = cid
        else:
            p.command_id = self.command_id + 0x80000000
        p.sequence_number = self.sequence_number
        p.command_status = status
        p.body=body
        return p

       
    def getcmdlen(self):
        if self.body:
            length = len(self.body)
        else:
            length = 0
        self.command_length = length + 16
        return self.command_length
        
    def __str__(self):
        self.getcmdlen()
        b = self.body
        if not b:
            b = ''
        l = len(b)
        return struct.pack('>iiii'+`l`+'s',self.command_length, self.command_id,
            self.command_status, self.sequence_number, b)

    def dump(self):
        self.getcmdlen()
        s  = "CommandLength = 0x%08x (%d)\n" % (self.command_length,self.command_length)
        s += "CommandID = 0x%08x\n" % self.command_id
        s += "CommandStatus = 0x%08x\n" % self.command_status
        s += "SequenceNumber = 0x%08x\n" % self.sequence_number
        s += "Body = %s" % repr(self.body)
        return s
 
class BIND(PDU):
    def __init__(self,user,password):
        PDU.__init__(self)
        self.user=user
        self.pasw=password
        self.system_type=''
        self.smpp_version = 0
        self.addr_ton = 0
        self.addr_npi = 0
        self.addr_range = ''
        str(self)

    def __str__(self):
        l = len(self.user)
        s = struct.pack(`l`+'s',self.user) + '\0'
        l = len(self.pasw)
        s += struct.pack(`l`+'s',self.pasw) + '\0'
        l = len(self.system_type)
        s += struct.pack(`l`+'s', self.system_type) + '\0'
        s += struct.pack('B', self.smpp_version)
        s += struct.pack('B', self.addr_ton)
        s += struct.pack('B', self.addr_npi)
        l = len(self.addr_range)
        s += struct.pack(`l`+'s', self.addr_range) + '\0'
        self.body = s
        return PDU.__str__(self)

class BIND_RX(BIND):
    def __init__(self,user,password):
        BIND.__init__(self,user,password)
        self.command_id = 0x00000001

class BIND_TX(BIND):
    def __init__(self,user,password):
        BIND.__init__(self,user,password)
        self.command_id = 0x00000002

class BIND_TRX(BIND):
    def __init__(self,user,password):
        BIND.__init__(self,user,password)
        self.command_id = 0x00000009

### Helpers #####


def c_octet_string(str):
    return str + '\0'

def short(i):
    return struct.pack('B',i)

### END OF FILE #####
