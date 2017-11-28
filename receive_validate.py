from scapy.all import *

from coding_packet import CodingPacket
bind_layers(Ether, CodingPacket, type=0x1234)
a_counter = 0
b_counter = 0
a_max_seqnum = 0
b_max_seqnum = 0

def print_status(pkt):
    global a_counter, b_counter, a_max_seqnum, b_max_seqnum
    
    if pkt[CodingPacket].packet_contents == 'A':
        a_counter += 1
        if a_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            a_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

    elif pkt[CodingPacket].packet_contents == 'B':
        b_counter += 1
        if b_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            b_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

    return "a_counter: {}, b_counter: {}, a_max_seqnum: {}, b_max_seqnum: {}".format(a_counter, b_counter, a_max_seqnum, b_max_seqnum)

def main():

    iface = sys.argv[1]
    num_pkts = int(sys.argv[2])
    sniff(iface=iface, filter="ether proto 0x1234", prn=print_status)

if __name__ == '__main__':
    main()
