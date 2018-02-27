from scapy.all import *

from coding_hdr import CodingHdr

bind_layers(Ether, CodingHdr, type=0x1234)
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

    print pkt[CodingHdr].num_switch_stats
    print len(pkt[CodingHdr].switch_stats)
    print type(pkt[CodingHdr].switch_stats)

    for i in range(pkt[CodingHdr].num_switch_stats):
        print "Switch ID:,", i, "is:", pkt[CodingHdr].switch_stats[i].swid
        print "Timestamp:,", i, "is:", pkt[CodingHdr].switch_stats[i].igt
    
    if pkt[CodingHdr].packet_contents == 'A':
        a += 1
        if a_max_seqnum < int(pkt[CodingHdr].coded_packets_seqnum):
            a_max_seqnum = int(pkt[CodingHdr].coded_packets_seqnum)

    elif pkt[CodingHdr].packet_contents == 'B':
        b += 1
        if b_max_seqnum < int(pkt[CodingHdr].coded_packets_seqnum):
            b_max_seqnum = int(pkt[CodingHdr].coded_packets_seqnum)

    elif pkt[CodingHdr].packet_contents == 'X':
        x += 1
        if x_max_seqnum < int(pkt[CodingHdr].coded_packets_seqnum):
            x_max_seqnum = int(pkt[CodingHdr].coded_packets_seqnum)

        if pkt[CodingHdr].packet_payload[0] == 'A':
            x_with_a += 1
        elif pkt[CodingHdr].packet_payload[0] == 'B':
            x_with_b += 1
        elif pkt[CodingHdr].packet_payload[0] == 'X':
            x_with_x += 1

    return "total: {}, a: {}, b: {}, x: {}, a_max_seqnum: {}, b_max_seqnum: {}, x_max_seqnum: {}, x_with_a: {}, x_with_b: {}, x_with_x: {}".format(total, a, b, x, a_max_seqnum, b_max_seqnum, x_max_seqnum, x_with_a, x_with_b, x_with_x)

def main():

    iface = sys.argv[1]
    num_pkts = int(sys.argv[2])

    sniff(iface=iface, filter="ether proto 0x1234", prn=print_status)

if __name__ == '__main__':
    main()
