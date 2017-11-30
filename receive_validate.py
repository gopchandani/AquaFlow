from scapy.all import *

from coding_packet import CodingPacket
bind_layers(Ether, CodingPacket, type=0x1234)
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
    
    if pkt[CodingPacket].packet_contents == 'A':
        a += 1
        if a_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            a_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

    elif pkt[CodingPacket].packet_contents == 'B':
        b += 1
        if b_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            b_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

    elif pkt[CodingPacket].packet_contents == 'X':
        x += 1
        if x_max_seqnum < int(pkt[CodingPacket].coded_packets_seqnum):
            x_max_seqnum = int(pkt[CodingPacket].coded_packets_seqnum)

        if pkt[CodingPacket].packet_payload[0] == 'A':
            x_with_a += 1
        elif pkt[CodingPacket].packet_payload[0] == 'B':
            x_with_b += 1
        elif pkt[CodingPacket].packet_payload[0] == 'X':
            x_with_x += 1

    return "total: {}, a: {}, b: {}, x: {}, a_max_seqnum: {}, b_max_seqnum: {}, x_max_seqnum: {}, x_with_a: {}, x_with_b: {}, x_with_x: {}".format(total, a, b, x, a_max_seqnum, b_max_seqnum, x_max_seqnum, x_with_a, x_with_b, x_with_x)

def main():

    iface = sys.argv[1]
    sniff(iface=iface, filter="ether proto 0x1234", prn=print_status)

if __name__ == '__main__':
    main()
