/* -*- P4_16 -*- */

/*
 * The Protocol header looks like this:
 *
 *        0                1                  2              3
 * +----------------+----------------+----------------+---------------+
 * |      P         |       4        |             Version            |
 * +----------------+----------------+----------------+---------------+
 * |                              Payload                             |
 * +----------------+----------------+----------------+---------------+
 * |                            Coded Payload                         |
 * +----------------+----------------+----------------+---------------+
 *
 * P is an ASCII Letter 'P' (0x50)
 * 4 is an ASCII Letter '4' (0x34)
 * Version is currently 0.1 (0x01)
 */

#include <core.p4>
#include <v1model.p4>

/*
 * Define the headers the program will recognize
 */

/*
 * Standard ethernet header 
 */
header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

const bit<16> CODING_ETYPE = 0x1234;
const bit<8>  CODING_P     = 0x50;   // 'P'
const bit<8>  CODING_4     = 0x34;   // '4'
const bit<8>  CODING_VER   = 0x01;   // v0.1

typedef bit<32> payload_t;

header coding_hdr_t {
    bit<8>  p;
    bit<8>  four;
    bit<8>  ver;
    bit<8>  packet_status;
    payload_t packet_payload;
}

/*
 * All headers, used in the program needs to be assembed into a single struct.
 * We only need to declare the type, but there is no need to instantiate it,
 * because it is done "by the architecture", i.e. outside of P4 functions
 */
struct headers {
    ethernet_t   ethernet;
    coding_hdr_t     p4calc;
}

/*
 * All metadata, globally used in the program, also  needs to be assembed 
 * into a single struct. As in the case of the headers, we only need to 
 * declare the type, but there is no need to instantiate it,
 * because it is done "by the architecture", i.e. outside of P4 functions
 */

struct intrinsic_metadata_t {
    bit<16> recirculate_flag;
}
struct extra_metadata_t { 
    bit<16> clone_number;
    bit<16> operand_index;
    bit<1> clone_at_egress;
}

struct metadata {
    intrinsic_metadata_t intrinsic_metadata;
    extra_metadata_t extra_metadata;
}


/*************************************************************************
 ***********************  P A R S E R  ***********************************
 *************************************************************************/
parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            CODING_ETYPE : check_p4calc;
            default      : accept;
        }
    }
    
    state check_p4calc {
        transition select(packet.lookahead<coding_hdr_t>().p,
        packet.lookahead<coding_hdr_t>().four,
        packet.lookahead<coding_hdr_t>().ver) {
            (CODING_P, CODING_4, CODING_VER) : parse_p4calc;
            default                          : accept;
        }
    }
    
    state parse_p4calc {
        packet.extract(hdr.p4calc);
        transition accept;
    }
}

/*************************************************************************
 ************   C H E C K S U M    V E R I F I C A T I O N   *************
 *************************************************************************/
control MyVerifyChecksum(inout headers hdr,
                         inout metadata meta) {
    apply { }
}

/*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    register<payload_t>(2) reg_operands;
    register<bit<32>>(1) reg_operand_index;

    action _nop () { 
    }

    action send_from_ingress(bit<9> egress_port, bit<8> packet_status) {
        hdr.p4calc.packet_status = packet_status;

        /* Send the packet back to the port it came from */
        standard_metadata.egress_spec = egress_port;
    }

    action send_from_ingress_2(bit<9> egress_port, bit<8> packet_status) {
        hdr.p4calc.packet_status = packet_status;

        /* Send the packet back to the port it came from */
        standard_metadata.egress_spec = egress_port;
    }



    action ingress_index_1 () {
        reg_operands.write(1, hdr.p4calc.packet_payload);
        send_from_ingress(3, 0x02);
    }

    action ingress_index_2 () {
        payload_t operand1;
        payload_t operand2;
        reg_operands.read(operand1, 0);
        reg_operands.read(operand2, 1);
        hdr.p4calc.packet_payload = operand1 ^ operand2;
        send_from_ingress(4, 0x02);
    }

    table table_code {
        key = {    
               meta.extra_metadata.operand_index: exact;
              }

        actions = {_nop; ingress_index_1; ingress_index_2;}
        size = 10;
    default_action = _nop;
    }

    action ingress_cloning_start() {
        meta.extra_metadata.clone_at_egress = 1;
    }

    action ingress_cloned_packets_loop () { 
        // This causes the packet to be not cloned at egress 
        meta.extra_metadata.clone_at_egress = 0;
    }

    table table_ingress_clone {
        key = {    
               meta.extra_metadata.clone_number: exact;
              }

        actions = {_nop; ingress_cloning_start; ingress_cloned_packets_loop; send_from_ingress;}
        size = 10;
    default_action = _nop;
    }

    table table_mac_fwd {
        key = {
                hdr.ethernet.dstAddr: exact;
              }

        actions = {_nop; send_from_ingress_2;}
        size = 10;
    default_action = _nop;
    }

    apply 
    {
        if (hdr.p4calc.isValid()) {

            //Logic for Coding

            if (hdr.p4calc.packet_status == 0x01) {
                bit<32> operand_index;
                reg_operand_index.read(operand_index, 0);
                 
                // If it is an alternate packet AND not a cloned packet, send it out
                if (operand_index == 0 && meta.extra_metadata.clone_number == 0)
                {
                    reg_operands.write(0, hdr.p4calc.packet_payload);
                    send_from_ingress(2, 0x02);
                    reg_operand_index.write(0, 1);
                } 

                // Process the cloned packets and do the coding.
                else
                {
                    switch(table_ingress_clone.apply().action_run) 
                    {
                        ingress_cloned_packets_loop: 
                        {
                            table_code.apply();
                        }
                    }
                    reg_operand_index.write(0, 0);
                }
            }

            //Logic for forwarding
            else if (hdr.p4calc.packet_status == 0x02) {
                table_mac_fwd.apply();
            }
            else
            {
                mark_to_drop();
            }

        }
        else 
        {
            mark_to_drop();
        }
    }
}

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {


    action _nop () { 
    }
    action egress_cloning_step() {
        meta.extra_metadata.clone_number = meta.extra_metadata.clone_number + 1;
        meta.extra_metadata.operand_index = meta.extra_metadata.clone_number;
        standard_metadata.clone_spec = 250;
        clone3(CloneType.E2E, standard_metadata.clone_spec, {meta.intrinsic_metadata, meta.extra_metadata, standard_metadata});
        recirculate({meta.intrinsic_metadata, meta.extra_metadata, standard_metadata});
    }
    action egress_cloning_stop() {
        mark_to_drop();
    }

    table table_egress_clone {
        key = {    
               meta.extra_metadata.clone_at_egress: exact;
               meta.extra_metadata.clone_number: exact;
              }
        actions = {_nop; egress_cloning_step; egress_cloning_stop;}
        size = 10;
    default_action = _nop;
    }
    apply { 
        if (hdr.p4calc.isValid()) {
            table_egress_clone.apply();
        }
        else {
            mark_to_drop();
        }
    }
}

/*************************************************************************
 *************   C H E C K S U M    C O M P U T A T I O N   **************
 *************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

/*************************************************************************
 ***********************  D E P A R S E R  *******************************
 *************************************************************************/
control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.p4calc);
    }
}

/*************************************************************************
 ***********************  S W I T T C H **********************************
 *************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
