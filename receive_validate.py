from scapy.all import *

from coding_packet import CodingPacket
bind_layers(Ether, CodingPacket, type=0x1234)
total= 0
a_pkts = 0
b_pkts = 0
x_pkts = 0
a_max_seqnum = 0
b_max_seqnum = 0
x_max_seqnum = 0

def print_status(pkt):
    global total, a_pkts, b_pkts, x_pkts, a_max_seqnum, b_max_seqnum, x_max_seqnum
    total += 1
    
    if pkt[CodingPacket].packet_contents == 'A':
        a_pkts += 1
        if a_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            a_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

    elif pkt[CodingPacket].packet_contents == 'B':
        b_pkts += 1
        if b_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            b_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

    elif pkt[CodingPacket].packet_contents == 'X':
        x_pkts += 1
        if x_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            x_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

    return "total: {}, a_pkts: {}, b_pkts: {}, x_pkts: {}, a_max_seqnum: {}, b_max_seqnum: {}, x_max_seqnum: {}".format(total, a_pkts, b_pkts, x_pkts, a_max_seqnum, b_max_seqnum, x_max_seqnum)

def main():

    iface = sys.argv[1]
    sniff(iface=iface, filter="ether proto 0x1234", prn=print_status)

if __name__ == '__main__':
    main()
