#!/usr/bin/sudo python

import numpy as np
import json

from scapy.all import *
from coding_hdr import CodingHdrR

bind_layers(Ether, CodingHdrR, type=0x1234)
total= 0
a = 0
b = 0
x = 0
a_max_seqnum = 0
b_max_seqnum = 0
x_max_seqnum = 0
x_with_a = 0 
x_with_b = 0 
x_with_x = 0


def print_status(pkt):
    global total, a, b, x, a_max_seqnum, b_max_seqnum, x_max_seqnum
    global x_with_a, x_with_b, x_with_x

    total += 1

    print pkt[CodingHdrR].num_switch_stats
    print pkt[CodingHdrR].swid1
    print "igt1:", int(pkt[CodingHdrR].igt1.encode('hex'), 16)
    print "enqt1:", int(pkt[CodingHdrR].enqt1.encode('hex'), 16)
    print "enqt1 - igt1:", int(pkt[CodingHdrR].enqt1.encode('hex'), 16) - int(pkt[CodingHdrR].igt1.encode('hex'), 16)
    print "delt1:", int(pkt[CodingHdrR].delt1.encode('hex'), 16)
    print pkt[CodingHdrR].swid2
    print "igt2:", int(pkt[CodingHdrR].igt2.encode('hex'), 16)
    print "enqt2:", int(pkt[CodingHdrR].enqt2.encode('hex'), 16)
    print "enqt2 - igt2:", int(pkt[CodingHdrR].enqt2.encode('hex'), 16) - int(pkt[CodingHdrR].igt2.encode('hex'), 16)
    print "delt2:", int(pkt[CodingHdrR].delt2.encode('hex'), 16)
    print pkt[CodingHdrR].swid3
    print "igt3:", int(pkt[CodingHdrR].igt3.encode('hex'), 16)
    print "enqt3:", int(pkt[CodingHdrR].enqt3.encode('hex'), 16)
    print "enqt3 - igt3:", int(pkt[CodingHdrR].enqt3.encode('hex'), 16) - int(pkt[CodingHdrR].igt3.encode('hex'), 16)
    print "delt3:", int(pkt[CodingHdrR].delt3.encode('hex'), 16)
    
    if pkt[CodingHdrR].packet_contents == 'A':
        a += 1
        if a_max_seqnum < int(pkt[CodingHdrR].coded_packets_seqnum):
            a_max_seqnum = int(pkt[CodingHdrR].coded_packets_seqnum)

    elif pkt[CodingHdrR].packet_contents == 'B':
        b += 1
        if b_max_seqnum < int(pkt[CodingHdrR].coded_packets_seqnum):
            b_max_seqnum = int(pkt[CodingHdrR].coded_packets_seqnum)

    elif pkt[CodingHdrR].packet_contents == 'X':
        x += 1
        if x_max_seqnum < int(pkt[CodingHdrR].coded_packets_seqnum):
            x_max_seqnum = int(pkt[CodingHdrR].coded_packets_seqnum)

        if pkt[CodingHdrR].packet_payload[0] == 'A':
            x_with_a += 1
        elif pkt[CodingHdrR].packet_payload[0] == 'B':
            x_with_b += 1
        elif pkt[CodingHdrR].packet_payload[0] == 'X':
            x_with_x += 1

    return "total: {}, a: {}, b: {}, x: {}, a_max_seqnum: {}, b_max_seqnum: {}, x_max_seqnum: {}, x_with_a: {}, x_with_b: {}, x_with_x: {}".format(total, a, b, x, a_max_seqnum, b_max_seqnum, x_max_seqnum, x_with_a, x_with_b, x_with_x)


processing_time_dict = {'A': {'coding': [], 'forwarding': [], 'decoding': []},
                        'B': {'coding': [], 'forwarding': [], 'decoding': []}
                        }


def collect_stats(pkt):

    global processing_time_dict

    coding_time = int(pkt[CodingHdrR].enqt1.encode('hex'), 16) - int(pkt[CodingHdrR].igt1.encode('hex'), 16)
    forwarding_time = int(pkt[CodingHdrR].enqt2.encode('hex'), 16) - int(pkt[CodingHdrR].igt2.encode('hex'), 16)
    decoding_time = int(pkt[CodingHdrR].enqt3.encode('hex'), 16) - int(pkt[CodingHdrR].igt3.encode('hex'), 16)

    processing_time_dict[pkt[CodingHdrR].packet_payload[0]]['coding'].append(coding_time)
    processing_time_dict[pkt[CodingHdrR].packet_payload[0]]['forwarding'].append(forwarding_time)
    processing_time_dict[pkt[CodingHdrR].packet_payload[0]]['decoding'].append(decoding_time)


def main():

    iface = sys.argv[1]

    sniff(iface=iface, filter="ether proto 0x1234", prn=collect_stats, count=int(sys.argv[2]))

    for payload in processing_time_dict:
        processing_time_dict[payload]['coding_mean'] = np.mean(processing_time_dict[payload]['coding'])
        processing_time_dict[payload]['coding_sd'] = np.std(processing_time_dict[payload]['coding'])
        processing_time_dict[payload]['forwarding_mean'] = np.mean(processing_time_dict[payload]['forwarding'])
        processing_time_dict[payload]['forwarding_sd'] = np.std(processing_time_dict[payload]['forwarding'])
        processing_time_dict[payload]['decoding_mean'] = np.mean(processing_time_dict[payload]['decoding'])
        processing_time_dict[payload]['decoding_sd'] = np.std(processing_time_dict[payload]['decoding'])

    print processing_time_dict

    with open('no_failure.json', 'w') as outfile:
        json.dump(processing_time_dict, outfile)


def print_data():
    for filename in ['no_failure.json', 's1_s2_failure.json', 's1_s3_failure.json', 's1_s3_failure.json',]:
        with open(filename, 'r') as infile:
            print filename
            processing_time_dict = json.load(infile)

            for payload in ['A', 'B']:
                print payload
                print "Coding:", processing_time_dict[payload]['coding_mean'], \
                    processing_time_dict[payload]['coding_sd']
                print "Forwarding:", processing_time_dict[payload]['forwarding_mean'], \
                    processing_time_dict[payload]['forwarding_sd']
                print "Decoding:", processing_time_dict[payload]['decoding_mean'], \
                    processing_time_dict[payload]['decoding_sd']


if __name__ == '__main__':
    #main()
    print_data()
