#! /usr/bin/env python
#
# Script to send SMS's through SMPP protocol
# uses threads, queue and conditions

from pySMPP import SMPP, SMPPError, SMS
import threading, Queue

class worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = Queue.Queue()
        self.cv = threading.Condition()
        self.ev = threading.Event()
        self.smpp = SMPP(log=sys.stderr)

    def run(self):
        self.smpp.connect('127.1', 10000)
        self.smpp.bind_transmitter('user','pass')
        self.cv.acquire()
        try:
          while not self.ev.isSet():
            self.process()
        finally:
            self.cv.release()
            self.smpp.close()

    def process(self):
        self.cv.wait(20)
        try:
            sms = self.q.get(0)
            if sms: self.smpp.submit_sm(sms)
        except Queue.Empty:
            self.smpp.enquire_link()

    def stop(self):
        self.ev.set()
        self.sendmessage(None)
        self.join()

    def sendmessage(self, sms):
        self.cv.acquire()
        self.q.put(sms)
        self.cv.notify()
        self.cv.release()

raw_input("Press ENTER to start...")
w = worker()
w.start()

try:
  while 1:
    s = raw_input('Enter SMS text here: ')
    sms = SMS(s)
    w.sendmessage(sms)
except KeyboardInterrupt:
    print "\nFinalizing...",
    w.stop()
    print "Done!"
except:
    w.stop()
    raise
