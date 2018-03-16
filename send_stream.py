#!/usr/bin/env python

import sys

from scapy.all import bind_layers
from scapy.all import Ether
from scapy.all import sendp
#from coding_hdr import CodingHdr
import time
import argparse
from scapy.all import Packet, XStrFixedLenField, StrFixedLenField, XByteField, IntField, ShortField
from scapy.all import FieldLenField, PacketListField

from switch_stats_hdr import SwitchStatsHdr




parser = argparse.ArgumentParser(description='send stream')
parser.add_argument('--npackets',dest="npackets", help='n_packets td send',
                    type=int, action="store", required=True)
parser.add_argument('--type', dest="type", help='topology_name',
                    type=str, action="store", default="diversity")
parser.add_argument('--payload', dest="payload", help='payload size', action="store", required=True)

args = parser.parse_args()

num_pkts = int(args.npackets)
exp_type = args.type
payload_size = int(args.payload)




class CodingHdr(Packet):
    fields_desc = [ 
                    XByteField("num_switch_stats", 0x01),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_batch_num", 0),
                    StrFixedLenField("packet_payload", ' '*(payload_size/8), length=payload_size/8)]

bind_layers(Ether, CodingHdr, type=0x1234)


def main():

    iface = 'h1-eth0'
    
    dst_mac = None

    global payload_size, exp_type, num_pkts

    if payload_size <= 0 :
        payload_size = 1

    if exp_type == "butterfly":
        dst_mac = "01:0C:CD:01:00:00"
    elif exp_type == "diversity":
        dst_mac = "00:00:00:00:05:02"
    else:
        print "Incorrect experiment type"
        sys.exit(0)


    pktA = Ether(dst=dst_mac, type=0x1234) / CodingHdr(num_switch_stats=0, packet_contents='A', packet_payload="A" * (payload_size/8))
    pktA = pktA/' '

    pktB = Ether(dst=dst_mac, type=0x1234) / CodingHdr(num_switch_stats=0, packet_contents='B', packet_payload="B" * (payload_size/8))
    pktB = pktB/' '

    time.sleep(2)

    for i in range(num_pkts/2):
        sendp(pktA, iface=iface)
        sendp(pktB, iface=iface)


if __name__ == '__main__':
    main()
