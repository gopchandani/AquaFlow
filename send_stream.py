#!/usr/bin/env python

import argparse
import sys
import socket
import random
import struct
import re
import random
import string
import readline

from scapy.all import bind_layers
from scapy.all import Ether
from scapy.all import sendp, sniff, srp1
from coding_hdr import CodingHdr
bind_layers(Ether, CodingHdr, type=0x1234)


def main():

    iface = 'h1-eth0'
    num_pkts = int(sys.argv[1])

    pktA = Ether(dst='00:00:00:00:05:02', type=0x1234) / CodingHdr(num_switch_stats=0, packet_contents="A", packet_payload="A" * 100)
    pktA = pktA/' '

    pktB = Ether(dst='00:00:00:00:05:02', type=0x1234) / CodingHdr(num_switch_stats=0, packet_contents="B", packet_payload="B" * 100)
    pktB = pktB/' '

    for i in range(num_pkts/2):
        sendp(pktA, iface=iface)
        sendp(pktB, iface=iface)


if __name__ == '__main__':
    main()
