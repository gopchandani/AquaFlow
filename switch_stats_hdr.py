from scapy.all import Packet, StrFixedLenField, XByteField, IntField


class SwitchStatsHdr(Packet):
    fields_desc = [ IntField("swid", 0),
                  StrFixedLenField("igt", "igtigt", length=6)]

