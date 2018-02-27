from scapy.all import Packet, StrFixedLenField, XByteField, IntField

class CodingHdr(Packet):
    fields_desc = [ XByteField("count", 0x01),
                    StrFixedLenField("P", "P", length=1),
                    StrFixedLenField("Four", "4", length=1),
                    XByteField("version", 0x01),
                    XByteField("packet_todo", 0x01),
                    StrFixedLenField("packet_contents", ' ', length=1),
                    IntField("coded_packets_seqnum", 0),
                    StrFixedLenField("packet_payload", ' '*100, length=100)]


