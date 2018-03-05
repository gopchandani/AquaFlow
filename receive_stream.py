#!/usr/bin/sudo python

import numpy as np
import json

from scapy.all import *
#from coding_hdr import CodingHdrR
import argparse
from scapy.all import Packet, XStrFixedLenField, StrFixedLenField, XByteField, IntField, ShortField
from scapy.all import FieldLenField, PacketListField

from switch_stats_hdr import SwitchStatsHdr




parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--log_file', dest="log_file", help='Path to log-file',
                    type=str, action="store", required=True)
parser.add_argument('--iface', dest="iface", help='Interface name',
                    type=str, action="store", default="h2-eth0")
parser.add_argument('--npackets', dest="npackets", help='number of packets to receive', action="store", required=True)

parser.add_argument('--payload', dest="payload", help='recv payload size', action="store", required=True)
args = parser.parse_args()




total= 0
a = 0
b = 0
x = 0
a_max_batch_num = 0
b_max_batch_num = 0
x_max_batch_num = 0
x_with_a = 0
x_with_b = 0
x_with_x = 0

payload_size = int(args.payload)


rcvd_pkt_metrics_dict = {'A': {'coding': [], 'forwarding': [], 'decoding': []},
                         'B': {'coding': [], 'forwarding': [], 'decoding': []}
                         }


class Coding_swid_hdr(Packet):
    fields_desc = [ 
                    IntField("swid", 0),
                    XStrFixedLenField("igt", "      ", length=6),
                    XStrFixedLenField("enqt", "    ", length=4),
                    XStrFixedLenField("delt", "    ", length=4),

                  ]
    def extract_padding(self, p):
        return "", p


class CodingHdrR(Packet):
    global payload_size
    fields_desc = [ 
                    XByteField("num_switch_stats", 0x0),
                    PacketListField("swtraces",
                                   [],
                                   Coding_swid_hdr,
                                   count_from=lambda pkt:(pkt.num_switch_stats*1)) ,
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_batch_num", 0),
                    StrFixedLenField("packet_payload", ' '*(payload_size/8), length=payload_size/8)]


bind_layers(Ether, CodingHdrR, type=0x1234)


def collect_stats(pkt):

    global total, a, b, x, a_max_batch_num, b_max_batch_num, x_max_batch_num
    global x_with_a, x_with_b, x_with_x
    global rcvd_pkt_metrics_dict


    coding_times = []
    forwarding_times = []
    decoding_times = []


    
    total += 1

    num_switch_stats = int(pkt[CodingHdrR].num_switch_stats)


    """
    print "num_switch_stats = ", num_switch_stats, len(pkt[CodingHdrR].swtraces[0])
    print "Switch ids: ", pkt[CodingHdrR].swtraces[0].swid, pkt[CodingHdrR].swtraces[1].swid, pkt[CodingHdrR].swtraces[2].swid, "\n"  
    print "Enqt: ", int(pkt[CodingHdrR].swtraces[0].enqt.encode('hex'),16), int(pkt[CodingHdrR].swtraces[1].enqt.encode('hex'),16), int(pkt[CodingHdrR].swtraces[2].enqt.encode('hex'), 16)
    print "igt: ", int(pkt[CodingHdrR].swtraces[0].igt.encode('hex'),16), int(pkt[CodingHdrR].swtraces[1].igt.encode('hex'), 16), int(pkt[CodingHdrR].swtraces[2].igt.encode('hex'), 16)
    print pkt[CodingHdrR].packet_contents, pkt[CodingHdrR].P, pkt[CodingHdrR].Four, pkt[CodingHdrR].version, pkt[CodingHdrR].packet_todo, pkt[CodingHdrR].packet_payload
    """


    for i in xrange(0, num_switch_stats) :
        if i == 0 :
            coding_times.append(int(pkt[CodingHdrR].swtraces[i].enqt.encode('hex'), 16) - int(pkt[CodingHdrR].swtraces[i].igt.encode('hex'), 16))
        elif i == num_switch_stats - 1 :
            decoding_times.append(int(pkt[CodingHdrR].swtraces[i].enqt.encode('hex'), 16) - int(pkt[CodingHdrR].swtraces[i].igt.encode('hex'), 16))
        else:    
            forwarding_times.append(int(pkt[CodingHdrR].swtraces[i].enqt.encode('hex'), 16) - int(pkt[CodingHdrR].swtraces[i].igt.encode('hex'), 16))



    
    rcvd_pkt_metrics_dict[pkt[CodingHdrR].packet_payload[0]]['coding'].extend(coding_times)
    rcvd_pkt_metrics_dict[pkt[CodingHdrR].packet_payload[0]]['forwarding'].extend(forwarding_times)
    rcvd_pkt_metrics_dict[pkt[CodingHdrR].packet_payload[0]]['decoding'].extend(decoding_times)

    if pkt[CodingHdrR].packet_contents == 'A':
        a += 1
        if a_max_batch_num < int(pkt[CodingHdrR].coded_packets_batch_num):
            a_max_batch_num = int(pkt[CodingHdrR].coded_packets_batch_num)

    elif pkt[CodingHdrR].packet_contents == 'B':
        b += 1
        if b_max_batch_num < int(pkt[CodingHdrR].coded_packets_batch_num):
            b_max_batch_num = int(pkt[CodingHdrR].coded_packets_batch_num)

    elif pkt[CodingHdrR].packet_contents == 'X':
        x += 1
        if x_max_batch_num < int(pkt[CodingHdrR].coded_packets_batch_num):
            x_max_batch_num = int(pkt[CodingHdrR].coded_packets_batch_num)

        if pkt[CodingHdrR].packet_payload[0] == 'A':
            x_with_a += 1
        elif pkt[CodingHdrR].packet_payload[0] == 'B':
            x_with_b += 1
        elif pkt[CodingHdrR].packet_payload[0] == 'X':
            x_with_x += 1
    


def main():

    n_recv_packets = int(args.npackets)
    iface = args.iface
    log_file = args.log_file

    try:
        sniff(iface=iface, filter="ether proto 0x1234", prn=collect_stats, count=n_recv_packets)
    except:
        pass
    
    for payload in rcvd_pkt_metrics_dict:
        rcvd_pkt_metrics_dict[payload]['coding_mean'] = np.mean(rcvd_pkt_metrics_dict[payload]['coding'])
        rcvd_pkt_metrics_dict[payload]['coding_sd'] = np.std(rcvd_pkt_metrics_dict[payload]['coding'])
        rcvd_pkt_metrics_dict[payload]['forwarding_mean'] = np.mean(rcvd_pkt_metrics_dict[payload]['forwarding'])
        rcvd_pkt_metrics_dict[payload]['forwarding_sd'] = np.std(rcvd_pkt_metrics_dict[payload]['forwarding'])
        rcvd_pkt_metrics_dict[payload]['decoding_mean'] = np.mean(rcvd_pkt_metrics_dict[payload]['decoding'])
        rcvd_pkt_metrics_dict[payload]['decoding_sd'] = np.std(rcvd_pkt_metrics_dict[payload]['decoding'])

    print rcvd_pkt_metrics_dict
    print "Total packets received:", total
    print "Total a packets:", a
    print "Total b pakcets:", b
    print "Total x packets:", x
    print "a_max_batch_num:", a_max_batch_num
    print "b_max_batch_num:", b_max_batch_num
    print "x_max_batch_num:", x_max_batch_num

    with open(log_file, 'w') as outfile:
        json.dump(rcvd_pkt_metrics_dict, outfile)

    time.sleep(2)
    

def print_data():
    for filename in ['no_failure.json', 's1_s2_failure.json', 's1_s3_failure.json', 's1_s3_failure.json',]:
        with open(filename, 'r') as infile:
            print filename
            rcvd_pkt_metrics_dict = json.load(infile)

            for payload in ['A', 'B']:
                print payload
                print "Coding:", rcvd_pkt_metrics_dict[payload]['coding_mean'], \
                    rcvd_pkt_metrics_dict[payload]['coding_sd']
                print "Forwarding:", rcvd_pkt_metrics_dict[payload]['forwarding_mean'], \
                    rcvd_pkt_metrics_dict[payload]['forwarding_sd']
                print "Decoding:", rcvd_pkt_metrics_dict[payload]['decoding_mean'], \
                    rcvd_pkt_metrics_dict[payload]['decoding_sd']


if __name__ == '__main__':
    main()
