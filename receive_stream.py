#!/usr/bin/sudo python

import numpy as np
import json
import argparse

from scapy.all import *
from scapy.all import FieldLenField, PacketListField
from scapy.all import Packet, XStrFixedLenField, StrFixedLenField, XByteField, IntField

import time

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--log_file', dest="log_file", help='Path to log-file',
                    type=str, action="store", required=True)
parser.add_argument('--iface', dest="iface", help='Interface name',
                    type=str, action="store", default="h2-eth0")
parser.add_argument('--npackets', dest="npackets", help='number of packets to receive', action="store", required=True)

parser.add_argument('--payload', dest="payload", help='recv payload size', action="store", required=True)
parser.add_argument('--type', dest="type", help='experiment type', action="store", default="diversity")
args = parser.parse_args()


packet_num = 0
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


class SwitchStatsHdr(Packet):
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
                                    SwitchStatsHdr,
                                    count_from=lambda pkt:(pkt.num_switch_stats*1)),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("stream_id", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_batch_num", 0),
                    StrFixedLenField("packet_payload", ' ' * (payload_size/8), length=payload_size/8)]


if args.type == "diversity" :
    rcvd_pkt_metrics_dict = {'A': {'coding': [], 'forwarding': [], 'decoding': []},
                         'B': {'coding': [], 'forwarding': [], 'decoding': []}}
else:
    rcvd_pkt_metrics_dict = {'first_pkt_time' : 0.0, 
                            'n_bits_received' : 0, 
                            'last_pkt_time' : 0.0
                            }

bind_layers(Ether, CodingHdrR, type=0x1234)

def collect_butterfly_stats(pkt) :

    global packet_num, a, b, x, a_max_batch_num, b_max_batch_num, x_max_batch_num
    global x_with_a, x_with_b, x_with_x
    global rcvd_pkt_metrics_dict

    packet_num += 1

    recv_time = time.time()

    if packet_num == 1 :
        rcvd_pkt_metrics_dict['first_pkt_time'] = float(pkt[CodingHdrR].packet_payload[1:])

    if packet_num == int(args.npackets) :
        rcvd_pkt_metrics_dict['last_pkt_time'] = recv_time
        rcvd_pkt_metrics_dict['send_rate'] = float(pkt[CodingHdrR].packet_payload[1:])
        
    rcvd_pkt_metrics_dict['n_bits_received'] += len(pkt[CodingHdrR].packet_payload)*8  



def collect_diversity_stats(pkt):

    global packet_num, a, b, x, a_max_batch_num, b_max_batch_num, x_max_batch_num
    global x_with_a, x_with_b, x_with_x
    global rcvd_pkt_metrics_dict

    coding_times = []
    forwarding_times = []
    decoding_times = []

    packet_num += 1
    num_switch_stats = int(pkt[CodingHdrR].num_switch_stats)

    # If this is the first packet, get the first switch's igt
    if packet_num == 1:
        rcvd_pkt_metrics_dict['first_switch_igt'] = int(pkt[CodingHdrR].swtraces[0].igt.encode('hex'), 16)

    # If this is the last packet, get the last switch's enqt
    if packet_num == int(args.npackets):
        rcvd_pkt_metrics_dict['last_switch_enqt'] = int(pkt[CodingHdrR].swtraces[num_switch_stats - 1].enqt.encode('hex'), 16)

    for i in xrange(0, num_switch_stats):
        if i == 0:
            coding_times.append(int(pkt[CodingHdrR].swtraces[i].enqt.encode('hex'), 16) - int(pkt[CodingHdrR].swtraces[i].igt.encode('hex'), 16))
        elif i == num_switch_stats - 1:
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


def run_diversity_experiment(iface, fn) :

    try:
        sniff(iface=iface, filter="ether proto 0x1234", prn=fn, count=int(args.npackets))
    except:
        pass

    print rcvd_pkt_metrics_dict

    for key in rcvd_pkt_metrics_dict:

        if key == 'A' or key == 'B':
            rcvd_pkt_metrics_dict[key]['coding_mean'] = np.mean(rcvd_pkt_metrics_dict[key]['coding'])
            rcvd_pkt_metrics_dict[key]['coding_sd'] = np.std(rcvd_pkt_metrics_dict[key]['coding'])
            rcvd_pkt_metrics_dict[key]['forwarding_mean'] = np.mean(rcvd_pkt_metrics_dict[key]['forwarding'])
            rcvd_pkt_metrics_dict[key]['forwarding_sd'] = np.std(rcvd_pkt_metrics_dict[key]['forwarding'])
            rcvd_pkt_metrics_dict[key]['decoding_mean'] = np.mean(rcvd_pkt_metrics_dict[key]['decoding'])
            rcvd_pkt_metrics_dict[key]['decoding_sd'] = np.std(rcvd_pkt_metrics_dict[key]['decoding'])

    print "Total packets received:", packet_num
    print "Total a packets:", a
    print "Total b pakcets:", b
    print "Total x packets:", x
    print "a_max_batch_num:", a_max_batch_num
    print "b_max_batch_num:", b_max_batch_num
    print "x_max_batch_num:", x_max_batch_num
    print "first_switch_igt:", rcvd_pkt_metrics_dict['first_switch_igt']
    print "last_switch_enqt:", rcvd_pkt_metrics_dict['last_switch_enqt']

    print "Packet duration in network:", (rcvd_pkt_metrics_dict['last_switch_enqt']) - (rcvd_pkt_metrics_dict['first_switch_igt'])


def run_butterfly_experiment(iface, fn) :

    try:
        sniff(iface=iface, filter="ether proto 0x1234", prn=fn, count=int(args.npackets))
    except:
        pass

    time_diff = rcvd_pkt_metrics_dict['last_pkt_time'] - rcvd_pkt_metrics_dict['first_pkt_time']

    print "First pkt time: ", rcvd_pkt_metrics_dict['first_pkt_time']
    print "Last pkt time: ", rcvd_pkt_metrics_dict['last_pkt_time']
    print "Time diff: ", time_diff
    print "N bits received: ", rcvd_pkt_metrics_dict['n_bits_received']

    rcvd_pkt_metrics_dict['throughput'] = float(rcvd_pkt_metrics_dict['n_bits_received'])/float(time_diff*1000000.0)
    rcvd_pkt_metrics_dict['time_diff'] = time_diff
    print "Observed Throughput : ", float(rcvd_pkt_metrics_dict['throughput'])

    sys.stdout.flush()

def main():

    iface = args.iface
    log_file = args.log_file
    exp_type = args.type



    if exp_type == "diversity" :
        run_diversity_experiment(iface, collect_diversity_stats)
    else :
        run_butterfly_experiment(iface, collect_butterfly_stats)


    with open(log_file, 'w') as outfile:
        json.dump(rcvd_pkt_metrics_dict, outfile)

    time.sleep(2)
    

if __name__ == '__main__':
    main()
