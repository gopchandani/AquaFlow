#!/usr/bin/sudo python

import numpy as np

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


a_coding_times = []
a_fwd_times = []
a_decoding_times = []

b_coding_times = []
b_fwd_times = []
b_decoding_times = []

def collect_stats(pkt):

    global a_coding_times, a_fwd_times, a_decoding_times
    global b_coding_times, b_fwd_times, b_decoding_times

    coding_time, fwd_time, decoding_time = None, None, None

    if pkt[CodingHdrR].packet_payload[0] == 'A':

        coding_time = int(pkt[CodingHdrR].enqt1.encode('hex'), 16) - int(pkt[CodingHdrR].igt1.encode('hex'), 16)
        fwd_time = int(pkt[CodingHdrR].enqt2.encode('hex'), 16) - int(pkt[CodingHdrR].igt2.encode('hex'), 16)
        decoding_time = int(pkt[CodingHdrR].enqt3.encode('hex'), 16) - int(pkt[CodingHdrR].igt3.encode('hex'), 16)

        a_coding_times.append(coding_time)
        a_fwd_times.append(fwd_time)
        a_decoding_times.append(decoding_time)

    elif pkt[CodingHdrR].packet_payload[0] == 'B':
        coding_time = int(pkt[CodingHdrR].enqt1.encode('hex'), 16) - int(pkt[CodingHdrR].igt1.encode('hex'), 16)
        fwd_time = int(pkt[CodingHdrR].enqt2.encode('hex'), 16) - int(pkt[CodingHdrR].igt2.encode('hex'), 16)
        decoding_time = int(pkt[CodingHdrR].enqt3.encode('hex'), 16) - int(pkt[CodingHdrR].igt3.encode('hex'), 16)

        b_coding_times.append(coding_time)
        b_fwd_times.append(fwd_time)
        b_decoding_times.append(decoding_time)


def main():

    iface = sys.argv[1]

    sniff(iface=iface, filter="ether proto 0x1234", prn=collect_stats, count=int(sys.argv[2]))

    print "A"
    print np.mean(a_coding_times), np.std(a_coding_times)
    print np.mean(a_fwd_times), np.std(a_fwd_times)
    print np.mean(a_decoding_times), np.std(a_decoding_times)

    print "B"
    print np.mean(b_coding_times), np.std(b_coding_times)
    print np.mean(b_fwd_times), np.std(b_fwd_times)
    print np.mean(b_decoding_times), np.std(b_decoding_times)


if __name__ == '__main__':
    main()
