from scapy.all import Packet, StrFixedLenField, XByteField, IntField, ShortField
from scapy.all import FieldLenField, PacketListField

from switch_stats_hdr import SwitchStatsHdr

class CodingHdr(Packet):
    fields_desc = [ 
                    FieldLenField("num_switch_stats", None, fmt="B", length_of="switch_stats", adjust=lambda pkt,l:l*2+4),
                    #ShortField("num_switch_stats", 0),
                    PacketListField("switch_stats", [], SwitchStatsHdr,count_from=lambda pkt:(pkt.num_switch_stats*1)),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_seqnum", 0),
                    StrFixedLenField("packet_payload", ' '*100, length=100)]


