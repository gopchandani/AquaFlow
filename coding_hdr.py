from scapy.all import Packet, XStrFixedLenField, StrFixedLenField, XByteField, IntField, ShortField
from scapy.all import FieldLenField, PacketListField

from switch_stats_hdr import SwitchStatsHdr

payload_size = 1600


class CodingHdr(Packet):
    fields_desc = [ 
                    XByteField("num_switch_stats", 0x01),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_batch_num", 0),
                    StrFixedLenField("packet_payload", ' '*(payload_size/8), length=payload_size/8)]


class CodingHdrR(Packet):
    fields_desc = [ 
                    XByteField("num_switch_stats", 0x01),
                    IntField("swid1", 0),
                    XStrFixedLenField("igt1", "      ", length=6),
                    XStrFixedLenField("enqt1", "      ", length=4),
                    XStrFixedLenField("delt1", "      ", length=4),
                    IntField("swid2", 0),
                    XStrFixedLenField("igt2", "      ", length=6),
                    XStrFixedLenField("enqt2", "      ", length=4),
                    XStrFixedLenField("delt2", "      ", length=4),
                    IntField("swid3", 0),
                    XStrFixedLenField("igt3", "      ", length=6),
                    XStrFixedLenField("enqt3", "      ", length=4),
                    XStrFixedLenField("delt3", "      ", length=4),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_batch_num", 0),
                    StrFixedLenField("packet_payload", ' '*(payload_size/8), length=payload_size/8)]


