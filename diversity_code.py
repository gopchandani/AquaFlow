#!/usr/bin/env python

import argparse
import sys
import socket
import random
import struct
import re

from scapy.all import Packet, hexdump, bind_layers
from scapy.all import Ether, StrFixedLenField, XByteField, IntField
from scapy.all import sendp, sniff, srp1
import readline

class CodingPacket(Packet):
    fields_desc = [ StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_status", 0x01),
                    IntField("packet_payload", 0xDEADBABE)]

bind_layers(Ether, CodingPacket, type=0x1234)

def main():

    iface = 'h1-eth0'
    data1 = 30

    pkt = Ether(dst='00:00:00:00:05:02', type=0x1234) / CodingPacket(packet_payload=data1)
    pkt = pkt/' '

    for i in range(2):
        print "Sending packet #", i+1
        sendp(pkt, iface=iface)

if __name__ == '__main__':
    main()
