#!/usr/bin/sudo python

import numpy as np
import json

from scapy.all import *
from coding_hdr import CodingHdrR

bind_layers(Ether, CodingHdrR, type=0x1234)
total = 0
a = 0
b = 0
x = 0
a_max_batch_num = 0
b_max_batch_num = 0
x_max_batch_num = 0
x_with_a = 0
x_with_b = 0
x_with_x = 0


rcvd_pkt_metrics_dict = {'A': {'coding': [], 'forwarding': [], 'decoding': []},
                         'B': {'coding': [], 'forwarding': [], 'decoding': []}
                         }


def collect_stats(pkt):

    global total, a, b, x, a_max_batch_num, b_max_batch_num, x_max_batch_num
    global x_with_a, x_with_b, x_with_x
    global rcvd_pkt_metrics_dict

    total += 1
    coding_time = int(pkt[CodingHdrR].enqt1.encode('hex'), 16) - int(pkt[CodingHdrR].igt1.encode('hex'), 16)
    forwarding_time = int(pkt[CodingHdrR].enqt2.encode('hex'), 16) - int(pkt[CodingHdrR].igt2.encode('hex'), 16)
    decoding_time = int(pkt[CodingHdrR].enqt3.encode('hex'), 16) - int(pkt[CodingHdrR].igt3.encode('hex'), 16)

    rcvd_pkt_metrics_dict[pkt[CodingHdrR].packet_payload[0]]['coding'].append(coding_time)
    rcvd_pkt_metrics_dict[pkt[CodingHdrR].packet_payload[0]]['forwarding'].append(forwarding_time)
    rcvd_pkt_metrics_dict[pkt[CodingHdrR].packet_payload[0]]['decoding'].append(decoding_time)

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

    iface = sys.argv[1]

    sniff(iface=iface, filter="ether proto 0x1234", prn=collect_stats, count=int(sys.argv[2]))

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

    with open('no_failure.json', 'w') as outfile:
        json.dump(rcvd_pkt_metrics_dict, outfile)


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
