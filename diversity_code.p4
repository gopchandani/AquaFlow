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
const bit<8>  CODING_A     = 0x41;   // 'A'
const bit<8>  CODING_B     = 0x42;   // 'B'
const bit<8>  CODING_X     = 0x58;   // 'X'
const bit<8>  CODING_VER   = 0x01;   // v0.1

const bit<8>  CODING_PACKET_TO_CODE     = 0x01;
const bit<8>  CODING_PACKET_TO_FORWARD  = 0x02;
const bit<8>  CODING_PACKET_TO_DECODE   = 0x03;

const bit<8> DONT_CLONE = 0;
const bit<8> DO_CLONE = 1;
const bit<8> POST_CLONE = 2;

const bit<32> CODING_PAYLOAD_DECODING_BUFFER_LENGTH = 128;
const bit<32> INIT_CODED_PACKETS_SEQNUM = 1;

typedef bit<800> payload_t;

header coding_hdr_t {
    bit<8>  p;
    bit<8>  four;
    bit<8>  ver;
    bit<8>  packet_todo;
    bit<8>  packet_contents;
    bit<32>  coded_packets_seq_num;
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
struct coding_metadata_t { 
    bit<16> clone_number;
    bit<16> operand_index;
    bit<8>  clone_status;
    bit<32> coded_packets_seq_num;
}

struct decoding_metadata_t {
    bit<8>  is_clone;
}

struct metadata {
    intrinsic_metadata_t intrinsic_metadata;
    coding_metadata_t coding_metadata;
    decoding_metadata_t decoding_metadata;
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
    register<bit<32>>(1) reg_coded_packets_seq_num;

    action _nop () { 
    }

    action send_from_ingress(bit<9> egress_port, bit<8> packet_contents, bit<32> packet_coded_packets_seq_num) {
        hdr.p4calc.coded_packets_seq_num = packet_coded_packets_seq_num;
        hdr.p4calc.packet_contents = packet_contents;
        standard_metadata.egress_spec = egress_port;
        meta.coding_metadata.clone_status = POST_CLONE;
    }

    action mac_forward_from_ingress(bit<9> egress_port) {
        standard_metadata.egress_spec = egress_port;
    }

    action ingress_index_1 () {
        reg_operands.write(1, hdr.p4calc.packet_payload);
        send_from_ingress(3, CODING_B, meta.coding_metadata.coded_packets_seq_num);
    }

    action ingress_index_2 () {
        payload_t operand1;
        payload_t operand2;
        reg_operands.read(operand1, 0);
        reg_operands.read(operand2, 1);
        hdr.p4calc.packet_payload = operand1 ^ operand2;
        send_from_ingress(4, CODING_X, meta.coding_metadata.coded_packets_seq_num);
    }

    table table_ingress_code {
        key = {    
               meta.coding_metadata.operand_index: exact;
              }

        actions = {_nop; ingress_index_1; ingress_index_2;}
        size = 10;
        default_action = _nop;
    }

    action ingress_cloned_packets_loop () { 
        // This causes the packet to be not cloned at egress 
        meta.coding_metadata.clone_status = DONT_CLONE;
    }

    table table_ingress_clone {
        key = {    
               meta.coding_metadata.clone_number: exact;
              }

        actions = {_nop; ingress_cloned_packets_loop; send_from_ingress;}
        size = 10;
        default_action = _nop;
    }

    table table_mac_fwd {
        key = {
                hdr.ethernet.dstAddr: exact;
              }

        actions = {_nop; mac_forward_from_ingress;}
        size = 10;
        default_action = _nop;
    }

    apply 
    {
        if (hdr.p4calc.isValid()) {

            //Logic for Coding

            if (hdr.p4calc.packet_todo == CODING_PACKET_TO_CODE) {
                bit<32> operand_index;
                reg_operand_index.read(operand_index, 0);

                bit<32> curr_coded_packets_seq_num;
                reg_coded_packets_seq_num.read(curr_coded_packets_seq_num, 0);
                if (curr_coded_packets_seq_num == 0) {
                    curr_coded_packets_seq_num = INIT_CODED_PACKETS_SEQNUM;
                    reg_coded_packets_seq_num.write(0, curr_coded_packets_seq_num);
                }

                // If it is first of two packets AND not a cloned packet, send it out
                if (operand_index == 0 && meta.coding_metadata.clone_number == 0)
                {
                    reg_operands.write(0, hdr.p4calc.packet_payload);
                    send_from_ingress(2, CODING_A, curr_coded_packets_seq_num);
                    reg_operand_index.write(0, 1);
                } 

                // If it is second of two packets AND not a cloned packet, don't send it out
                // but keep track of it 
                else if (operand_index == 1 && meta.coding_metadata.clone_number == 0) 
                {
                    meta.coding_metadata.clone_status = DO_CLONE;
                    reg_operand_index.write(0, 0);
 
                    // Put the sequence number in the packet metadata so it is maintained
                    meta.coding_metadata.coded_packets_seq_num = curr_coded_packets_seq_num;

                    // Increase the coded sequence number, this happens every two packets
                    reg_coded_packets_seq_num.write(0, curr_coded_packets_seq_num + 1);
                }

                // If it is a cloned packet, do the coding and then send them out via table_ingress_code
                if (meta.coding_metadata.clone_number > 0) 
                {
                    switch(table_ingress_clone.apply().action_run) 
                    {
                        ingress_cloned_packets_loop: 
                        {
                            table_ingress_code.apply();
                        }
                    }
                }
            }
            //Logic for forwarding
            else if (hdr.p4calc.packet_todo == CODING_PACKET_TO_FORWARD) {
                table_mac_fwd.apply();
            }
            //Logic for decoding
            else if (hdr.p4calc.packet_todo == CODING_PACKET_TO_DECODE) {
                table_mac_fwd.apply();
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

    register<payload_t>(CODING_PAYLOAD_DECODING_BUFFER_LENGTH) reg_payload_decoding_buffer_a;
    register<payload_t>(CODING_PAYLOAD_DECODING_BUFFER_LENGTH) reg_payload_decoding_buffer_b;
    register<payload_t>(CODING_PAYLOAD_DECODING_BUFFER_LENGTH) reg_payload_decoding_buffer_x;
    register<bit<32>>(1) reg_a_index;
    register<bit<32>>(1) reg_b_index;
    register<bit<32>>(1) reg_x_index;
    register<bit<32>>(CODING_PAYLOAD_DECODING_BUFFER_LENGTH) reg_num_sent_per_index;
    register<bit<32>>(CODING_PAYLOAD_DECODING_BUFFER_LENGTH) reg_num_recv_per_index;
    register<bit<32>>(CODING_PAYLOAD_DECODING_BUFFER_LENGTH) reg_xor_received_per_index;
    register<bit<32>>(CODING_PAYLOAD_DECODING_BUFFER_LENGTH) reg_rcv_seq_num_per_index;

    bit<32> rcv_seq_num_per_index;
    bit<32> this_pkt_index;
    bit<32> a_index;
    bit<32> b_index;
    bit<32> x_index;
    bit<32> num_sent_per_index;
    bit<32> num_recv_per_index;
    bit<32> xor_received_per_index;

    action _nop () { 
    }

    action egress_cloning_step() {
        meta.coding_metadata.clone_number = meta.coding_metadata.clone_number + 1;
        meta.coding_metadata.operand_index = meta.coding_metadata.clone_number;
        standard_metadata.clone_spec = 250;
        clone3(CloneType.E2E, standard_metadata.clone_spec, {meta.intrinsic_metadata, meta.coding_metadata, standard_metadata});
        recirculate({meta.intrinsic_metadata, meta.coding_metadata, standard_metadata});
    }
    action egress_cloning_stop() {
        mark_to_drop();
    }
    action egress_coded_packets_processing() {
        hdr.p4calc.packet_todo = CODING_PACKET_TO_FORWARD;
    }

    table table_egress_clone {
        key = {    
               meta.coding_metadata.clone_status: exact;
               meta.coding_metadata.clone_number: exact;
              }
        actions = {_nop; egress_cloning_step; egress_cloning_stop; egress_coded_packets_processing;}
        size = 10;
        default_action = _nop;
    }
    apply { 
        if (hdr.p4calc.isValid()) {
            // Logic for coding
            if (hdr.p4calc.packet_todo == CODING_PACKET_TO_CODE) {
                table_egress_clone.apply();
            }
            // Logic to forward
            else if (hdr.p4calc.packet_todo == CODING_PACKET_TO_FORWARD) {
                hdr.p4calc.packet_todo = CODING_PACKET_TO_DECODE;
            }
            // Logic for decoding
            else if (hdr.p4calc.packet_todo == CODING_PACKET_TO_DECODE) {

                this_pkt_index = hdr.p4calc.coded_packets_seq_num % CODING_PAYLOAD_DECODING_BUFFER_LENGTH;

                // Get the number of pkts received for this seq num
                reg_num_recv_per_index.read(num_recv_per_index, this_pkt_index);

                // Get the number of sent out for this seq num
                reg_num_sent_per_index.read(num_sent_per_index, this_pkt_index);

                // Get the status of received packets for this index
                reg_xor_received_per_index.read(xor_received_per_index, this_pkt_index);

                //Get the current occupant seq_num of this index
                reg_rcv_seq_num_per_index.read(rcv_seq_num_per_index, this_pkt_index);

                //If it is zero, then set this current pkt as the occupant
                if (rcv_seq_num_per_index == 0)
                {
                    reg_rcv_seq_num_per_index.write(this_pkt_index, hdr.p4calc.coded_packets_seq_num);
                }

                if (meta.decoding_metadata.is_clone == 1)  {
                    //fill up the clone with other payload by using the XOR coded payload in buffer
                    payload_t coded_payload;
                    reg_payload_decoding_buffer_x.read(coded_payload, this_pkt_index);
                    hdr.p4calc.packet_payload = hdr.p4calc.packet_payload ^ coded_payload;
                    hdr.p4calc.packet_contents = CODING_X;

                    // Update here
                    reg_num_sent_per_index.write(this_pkt_index, num_sent_per_index + 1);
                }
                else
                if (meta.decoding_metadata.is_clone == 0)
                {
                    // if the sequence number of the packet(s) in the buffer is different than this packet then rollover has occured, reset everything.
                    if (hdr.p4calc.coded_packets_seq_num != rcv_seq_num_per_index) 
                    {
                        reg_xor_received_per_index.write(this_pkt_index, 0);
                        reg_num_sent_per_index.write(this_pkt_index, 0);
                        reg_num_recv_per_index.write(this_pkt_index, 0);
                        
                        xor_received_per_index = 0;
                        num_sent_per_index = 0;
                        num_recv_per_index = 0;
    
                        // And put the new seq_num in the buffer
                        reg_rcv_seq_num_per_index.write(this_pkt_index, hdr.p4calc.coded_packets_seq_num);
                    }

                    if (num_sent_per_index < 2)
                    {
                        // Update for all non-cloned packets
                        reg_num_recv_per_index.write(this_pkt_index, num_recv_per_index + 1);

                        // Copy the packet payload in appropriate buffer and update the index
                        if (hdr.p4calc.packet_contents == CODING_A) {
                            reg_payload_decoding_buffer_a.write(this_pkt_index, hdr.p4calc.packet_payload);
                            reg_a_index.write(0, this_pkt_index);
                        }
                        else
                        if (hdr.p4calc.packet_contents == CODING_B) {
                            reg_payload_decoding_buffer_b.write(this_pkt_index, hdr.p4calc.packet_payload);
                            reg_b_index.write(0, this_pkt_index);
                        }
                        else 
                        if (hdr.p4calc.packet_contents == CODING_X) {
                            reg_payload_decoding_buffer_x.write(this_pkt_index, hdr.p4calc.packet_payload);
                            reg_x_index.write(0, this_pkt_index);
                        }

                        reg_a_index.read(a_index, 0);
                        reg_b_index.read(b_index, 0);
                        reg_x_index.read(x_index, 0);

                        // If the packet is A or B
                        if (hdr.p4calc.packet_contents == CODING_A || hdr.p4calc.packet_contents == CODING_B) {


                            // If two packets have not been sent yet
                            if (num_sent_per_index == 0 || num_sent_per_index == 1) {
                                // If XOR was already received, then clone/deocde it and send, otherwise simply send it
                                if (xor_received_per_index == 1)
                                {
                                    //Clone this packet and send it along
                                    meta.decoding_metadata.is_clone = 1;
                                    standard_metadata.clone_spec = 450;
                                    clone3(CloneType.E2E, standard_metadata.clone_spec, {meta.intrinsic_metadata, meta.decoding_metadata, standard_metadata});

                                    // Update here
                                    reg_num_sent_per_index.write(this_pkt_index, num_sent_per_index + 1);
                                    }
                                else
                                if (xor_received_per_index == 0)
                                {
                                    // Update here
                                    reg_num_sent_per_index.write(this_pkt_index, num_sent_per_index + 1);
     
                                }
                            }
                        }
                        // If the packet is X
                        else if (hdr.p4calc.packet_contents == CODING_X) {

                            reg_xor_received_per_index.write(this_pkt_index, 1);

                            // If one packet was previously received then decode using XOR
                            if (num_sent_per_index == 1) {
                                // Pickup the uncoded packet and xor it with this one to get the other payload
                                payload_t uncoded_payload;

                                if (a_index >= this_pkt_index) 
                                {
                                    reg_payload_decoding_buffer_a.read(uncoded_payload, this_pkt_index);
                                    payload_t a_payload;
                                    a_payload = hdr.p4calc.packet_payload ^ uncoded_payload;
                                    hdr.p4calc.packet_payload = a_payload;
                                }
                                else
                                if (b_index >= this_pkt_index) 
                                {
                                    reg_payload_decoding_buffer_b.read(uncoded_payload, this_pkt_index);
                                    payload_t b_payload;
                                    b_payload = hdr.p4calc.packet_payload ^ uncoded_payload;
                                    hdr.p4calc.packet_payload = b_payload;
                                }
                                // Update here
                                reg_num_sent_per_index.write(this_pkt_index, num_sent_per_index + 1);
     
                            } 
                            else 
                            // If XOR was the first packet that arrived, then drop and wait for one of the others
                            if (num_sent_per_index == 0) {
                                mark_to_drop();
                            }
                        } 
                    }   
                    else
                    {
                        // Update for all non-cloned packets
                        reg_num_recv_per_index.write(this_pkt_index, num_recv_per_index + 1);

                        mark_to_drop();
                    } 

                }
            }
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
