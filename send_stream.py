#!/usr/bin/env python

import sys

from scapy.all import bind_layers
from scapy.all import Ether
from scapy.all import sendp
from coding_hdr import CodingHdr, payload_size
bind_layers(Ether, CodingHdr, type=0x1234)


def main():

    iface = 'h1-eth0'
    num_pkts = int(sys.argv[1])

    pktA = Ether(dst='00:00:00:00:05:02', type=0x1234) / CodingHdr(num_switch_stats=0,
                                                                   packet_contents="A",
                                                                   packet_payload="A" * (payload_size/8))
    pktA = pktA/' '

    pktB = Ether(dst='00:00:00:00:05:02', type=0x1234) / CodingHdr(num_switch_stats=0,
                                                                   packet_contents="B",
                                                                   packet_payload="B" * (payload_size/8))
    pktB = pktB/' '

    for i in range(num_pkts/2):
        sendp(pktA, iface=iface)
        sendp(pktB, iface=iface)


if __name__ == '__main__':
    main()
