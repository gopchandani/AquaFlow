from scapy.all import Packet, XStrFixedLenField, StrFixedLenField, XByteField, IntField, ShortField
from scapy.all import FieldLenField, PacketListField

from switch_stats_hdr import SwitchStatsHdr

class CodingHdr(Packet):
    fields_desc = [ 
                    #FieldLenField("num_switch_stats", None, fmt="B", length_of="switch_stats", adjust=lambda pkt,l:l*2+4),
                    #PacketListField("switch_stats", [], SwitchStatsHdr,count_from=lambda pkt:(pkt.num_switch_stats*1)),
                    XByteField("num_switch_stats", 0x01),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_seqnum", 0),
                    StrFixedLenField("packet_payload", ' '*100, length=100)]


class CodingHdrR(Packet):
    fields_desc = [ 
                    #FieldLenField("num_switch_stats", None, fmt="B", length_of="switch_stats", adjust=lambda pkt,l:l*2+4),
                    #PacketListField("switch_stats", [], SwitchStatsHdr,count_from=lambda pkt:(pkt.num_switch_stats*1)),
                    XByteField("num_switch_stats", 0x01),
                    IntField("swid1", 0),
                    XStrFixedLenField("igt1", "      ", length=6),
                    IntField("swid2", 0),
                    XStrFixedLenField("igt2", "      ", length=6),
                    IntField("swid3", 0),
                    XStrFixedLenField("igt3", "      ", length=6),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_seqnum", 0),
                    StrFixedLenField("packet_payload", ' '*100, length=100)]


