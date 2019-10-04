#!/usr/bin/env python

import sys
import time
import argparse

from scapy.all import bind_layers
from scapy.all import Ether
from scapy.all import sendp

import time

from scapy.all import Packet, XStrFixedLenField, StrFixedLenField, XByteField, IntField
import numpy as np

parser = argparse.ArgumentParser(description='send stream')
parser.add_argument('--npackets',dest="npackets", help='n_packets td send',
                    type=int, action="store", required=True)
parser.add_argument('--payload', dest="payload", help='payload size',
                    action="store", required=True)

parser.add_argument('--iface', dest="iface", help='Interface name',
                    type=str, action="store", default="h1-eth0")
parser.add_argument('--rate', dest="rate", action="store", type=float, default=0.0, help="send rate in Mbits per sec")

parser.add_argument('--type', dest="type", help='experiment type', action="store", default="diversity", required=False)

args = parser.parse_args()

num_pkts = int(args.npackets)
payload_size = int(args.payload)


class CodingHdrS(Packet):
    global payload_size
    fields_desc = [
                    XByteField("num_switch_stats", 0x01),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("stream_id", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_batch_num", 0),
                    StrFixedLenField("packet_payload", ' '*(payload_size/8), length=payload_size/8)]


bind_layers(Ether, CodingHdrS, type=0x1234)


def main():

    global payload_size, args, num_pkts

    if payload_size <= 0 :
        payload_size = 1

    time.sleep(2)
    n_bits = 2*payload_size
    if args.rate == 0.0 :
        avg_time_to_sleep = 0.0
    else:
        rate = float(args.rate)*1000000.0
        time_to_sleep = float(n_bits)/float(rate)
        avg_time_to_sleep = float(payload_size)/float(rate)

        print "Time to sleep (secs) = ", time_to_sleep

    payload_A = "A"*(payload_size/8)
    payload_B = "B"*(payload_size/8)

    pktAd = Ether(type=0x1234) / CodingHdrS(num_switch_stats=0, packet_contents='A', packet_payload=payload_A)
    pktAd = pktAd/' '

    pktBd = Ether(type=0x1234) / CodingHdrS(num_switch_stats=0, packet_contents='B', packet_payload=payload_B)
    pktBd = pktBd/' '

    curr_send_rate = float(args.rate)

    for i in range(num_pkts/2):

        if i == 0:
            curr_time = str(time.time())

            first_pkt_time = float(curr_time)
            n_chars = (payload_size/8)

            payload_A = "A"
            payload_B = "B"

            n_chars_left = n_chars - 1 - len(curr_time)

            payload_A = payload_A + ("0"* n_chars_left)
            payload_B = payload_B + ("0"* n_chars_left)

            payload_A = payload_A + curr_time
            payload_B = payload_B + curr_time

            pktA = Ether(type=0x1234) / CodingHdrS(num_switch_stats=0, packet_contents='A', packet_payload=payload_A)
            pktA = pktA/' '

            pktB = Ether(type=0x1234) / CodingHdrS(num_switch_stats=0, packet_contents='B', packet_payload=payload_B)
            pktB = pktB/' '
            start_time = float(curr_time)
            sendp(pktA, iface=args.iface)
            end_time = float(time.time())
            elapsed = end_time - start_time

            time_to_sleep = np.random.exponential(scale=avg_time_to_sleep)
            if time_to_sleep - elapsed > 0 :
                time.sleep(time_to_sleep - elapsed)


            start_time = float(time.time())
            sendp(pktB, iface=args.iface)
            end_time = float(time.time())
            elapsed = end_time - start_time

            time_to_sleep = np.random.exponential(scale=avg_time_to_sleep)
            if time_to_sleep - elapsed > 0 :
                time.sleep(time_to_sleep - elapsed)

        elif i == num_pkts/2 - 1:
            curr_send_rate_str = str(curr_send_rate)
            payload_A = "A"
            payload_B = "B"

            n_chars_left = n_chars - 1 - len(curr_send_rate_str)

            payload_A = payload_A + ("0"* n_chars_left)
            payload_B = payload_B + ("0"* n_chars_left)

            payload_A = payload_A + curr_send_rate_str
            payload_B = payload_B + curr_send_rate_str

            pktA = Ether(type=0x1234) / CodingHdrS(num_switch_stats=0, packet_contents='A', packet_payload=payload_A)
            pktA = pktA/' '

            pktB = Ether(type=0x1234) / CodingHdrS(num_switch_stats=0, packet_contents='B', packet_payload=payload_B)
            pktB = pktB/' '

            start_time = float(time.time())
            sendp(pktA, iface=args.iface)
            end_time = float(time.time())
            elapsed = end_time - start_time

            time_to_sleep = np.random.exponential(scale=avg_time_to_sleep)
            if time_to_sleep - elapsed > 0 :
                time.sleep(time_to_sleep - elapsed)


            start_time = float(time.time())
            sendp(pktB, iface=args.iface)
            end_time = float(time.time())
            elapsed = end_time - start_time
            last_pkt_time = float(end_time)

            time_to_sleep = np.random.exponential(scale=avg_time_to_sleep)
            if time_to_sleep - elapsed > 0 :
                time.sleep(time_to_sleep - elapsed)

        else:

            start_time = float(time.time())
            sendp(pktA, iface=args.iface)
            end_time = float(time.time())
            elapsed = end_time - start_time

            time_to_sleep = np.random.exponential(scale=avg_time_to_sleep)
            if time_to_sleep - elapsed > 0 :
                time.sleep(time_to_sleep - elapsed)


            start_time = float(time.time())
            sendp(pktB, iface=args.iface)
            end_time = float(time.time())
            elapsed = end_time - start_time
            last_pkt_time = float(end_time)

            time_to_sleep = np.random.exponential(scale=avg_time_to_sleep)
            if time_to_sleep - elapsed > 0 :
                time.sleep(time_to_sleep - elapsed)

            curr_send_rate = float(payload_size*2*(i+1))/float((last_pkt_time - first_pkt_time)*10**6)

        print "Pkt batch send time: ", time.time()

        #if(time_to_sleep > 0.0) :
        #    if time_to_sleep - elapsed > 0.0 :
        #        time.sleep(float(time_to_sleep) - elapsed)

    print "Send Rate (Mbits per sec): ", curr_send_rate


if __name__ == '__main__':
    main()
