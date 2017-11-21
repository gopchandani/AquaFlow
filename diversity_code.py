#!/usr/bin/env python

import argparse
import sys
import socket
import random
import struct
import re
import random
import string

from scapy.all import Packet, hexdump, bind_layers
from scapy.all import Ether, StrFixedLenField, XByteField, IntField
from scapy.all import sendp, sniff, srp1
import readline

class CodingPacket(Packet):
    fields_desc = [ StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_status", 0x01),
                    StrFixedLenField("packet_payload", ' '*100, length=100)]

bind_layers(Ether, CodingPacket, type=0x1234)

def main():

    iface = 'h1-eth0'
    num_pkts = int(sys.argv[1])

    pktA = Ether(dst='00:00:00:00:05:02', type=0x1234) / CodingPacket(packet_payload="A" * 100)
    pktA = pktA/' '

    pktB = Ether(dst='00:00:00:00:05:02', type=0x1234) / CodingPacket(packet_payload="B" * 100)
    pktB = pktB/' '

    for i in range(num_pkts/2):
        sendp(pktA, iface=iface)
        sendp(pktB, iface=iface)

if __name__ == '__main__':
    main()
