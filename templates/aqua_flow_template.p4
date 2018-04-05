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

//#include <core.p4>
//#include <v1model.p4>

#include "/usr/local/share/p4c/p4include/core.p4"
#include "/usr/local/share/p4c/p4include/v1model.p4"

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

#define MAX_HOPS 9

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

const bit<1> DONT_CLONE = 0;
const bit<1> DO_CLONE = 1;
const bit<32> DECODING_BUFFER_SIZE = 1024; // This has to be a power of 2

const bit<32> CODING_INPUT_BATCH_SIZE = 2;

typedef bit<@PAYLOAD_SIZE@> payload_t;

header coding_hdr_t {
    bit<8>  p;
    bit<8>  four;
    bit<8>  ver;
    bit<8>  stream_id;
    bit<8>  next_primitive;
    bit<8>  packet_contents;
    bit<32>  coded_packets_batch_num;
    payload_t packet_payload;
}


typedef bit<32> switchID_t;
typedef bit<32> qdepth_t;
typedef bit<48> ingress_global_timestamp_t;
typedef bit<32> enq_timestamp_t;
typedef bit<32> deq_timedelta_t;

header stats_hdr_t {
    bit<8> num_switch_stats;
}

header switch_stats_t {
    switchID_t swid;
    ingress_global_timestamp_t igt;
    enq_timestamp_t enqt;
    deq_timedelta_t delt;
}

/*
 * All headers, used in the program needs to be assembed into a single struct.
 * We only need to declare the type, but there is no need to instantiate it,
 * because it is done "by the architecture", i.e. outside of P4 functions
 */
struct headers {
    ethernet_t                  ethernet;
    stats_hdr_t                 stats;
    switch_stats_t[MAX_HOPS]    switch_stats;
    coding_hdr_t                coding;
}

/*
 * All metadata, globally used in the program, also  needs to be assembed
 * into a single struct. As in the case of the headers, we only need to
 * declare the type, but there is no need to instantiate it,
 * because it is done "by the architecture", i.e. outside of P4 functions
 */

struct parser_metadata_t {
    bit<8>  remaining;
}

struct intrinsic_metadata_t {
    bit<16> recirculate_flag;
}

struct coding_metadata_t {
    bit<16> coding_loop_index;
    bit<1>  do_clone;
    bit<32> per_batch_input_packet_num;
}

struct decoding_metadata_t {
    bit<8>  is_clone;
    bit<32> batch_idx;
    bit<32> per_batch_input_packet_num;
    bit<32> per_batch_coded_received;
}

struct forwarding_metadata_t {
    bit<8>  is_bi_cast;
    bit<8>  bi_cast_todo_for_orig;
    bit<8>  bi_cast_todo_for_clone;
    bit<32> bi_cast_instance_num;
}

struct metadata {
    parser_metadata_t       parser_metadata;
    intrinsic_metadata_t    intrinsic_metadata;
    coding_metadata_t       coding_metadata;
    decoding_metadata_t     decoding_metadata;
    forwarding_metadata_t   forwarding_metadata;
}


/*************************************************************************
 ***********************  P A R S E R  ***********************************
 *************************************************************************/
parser CodingParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            CODING_ETYPE : parse_stats;
            default      : accept;
        }
    }

    state parse_stats {
        packet.extract(hdr.stats);
        meta.parser_metadata.remaining = hdr.stats.num_switch_stats;
        transition select(meta.parser_metadata.remaining) {
            0 : check_coding;
            default: parse_switch_stats;
        }
    }

    state parse_switch_stats {
        packet.extract(hdr.switch_stats.next);
        meta.parser_metadata.remaining = meta.parser_metadata.remaining  - 1;
        transition select(meta.parser_metadata.remaining) {
            0 : check_coding;
            default: parse_switch_stats;
        }
    }

    state check_coding {
        transition select(packet.lookahead<coding_hdr_t>().p, packet.lookahead<coding_hdr_t>().four, packet.lookahead<coding_hdr_t>().ver) {
            (CODING_P, CODING_4, CODING_VER) : parse_coding;
            default                          : accept;
        }
    }

    state parse_coding {
        packet.extract(hdr.coding);
        transition accept;
    }
}

/*************************************************************************
 ************   C H E C K S U M    V E R I F I C A T I O N   *************
 *************************************************************************/
control CodingVerifyChecksum(inout headers hdr,
                         inout metadata meta) {
    apply { }
}

/*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control CodingIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    register<payload_t>(2) reg_coding_payload_buffer;
    register<bit<32>>(1) reg_num_coding_input_pkts;
    bit<32> num_coding_input_pkts;


    register<payload_t>(DECODING_BUFFER_SIZE) reg_payload_decoding_buffer_uncoded;
    register<payload_t>(DECODING_BUFFER_SIZE) reg_payload_decoding_buffer_coded;
    register<bit<32>>(1) reg_uncoded_index;
    register<bit<32>>(1) reg_coded_index;
    bit<32> uncoded_index;
    bit<32> coded_index;


    // Captures how many of a given batch have we seen so far.
    register<bit<32>>(DECODING_BUFFER_SIZE) reg_per_batch_input_packet_num;

    // Captures which batch is in which index
    register<bit<32>>(DECODING_BUFFER_SIZE) reg_rcv_batch_num_per_index;
    bit<32> rcv_batch_num_per_index;


    action _nop () {
    }

    action drop () {
        mark_to_drop();
    }

    action send_from_ingress(bit<9> egress_port, bit<8> packet_contents) {
        reg_num_coding_input_pkts.read(num_coding_input_pkts, 0);
        hdr.coding.coded_packets_batch_num = (num_coding_input_pkts + 1) / CODING_INPUT_BATCH_SIZE;
        hdr.coding.packet_contents = packet_contents;
        standard_metadata.egress_spec = egress_port;
    }

    action send_from_ingress_no_batch(bit<9> egress_port, bit<8> packet_contents) {
        reg_num_coding_input_pkts.read(num_coding_input_pkts, 0);
        hdr.coding.packet_contents = packet_contents;
        standard_metadata.egress_spec = egress_port;
    }

    action uni_cast(bit<9> egress_port) {
        standard_metadata.egress_spec = egress_port;
    }

    action bi_cast(bit<9> egress_port_for_orig, bit<8> next_packet_todo_for_orig, bit<8> next_packet_todo_for_clone)
    {
        meta.forwarding_metadata.is_bi_cast = 1;
        meta.forwarding_metadata.bi_cast_todo_for_orig = next_packet_todo_for_orig;
        meta.forwarding_metadata.bi_cast_todo_for_clone = next_packet_todo_for_clone;

        uni_cast(egress_port_for_orig);
    }

    action copy () {
        reg_coding_payload_buffer.write(meta.coding_metadata.per_batch_input_packet_num, hdr.coding.packet_payload);
        mark_to_drop();
    }

    action copy_trigger () {
        reg_coding_payload_buffer.write(meta.coding_metadata.per_batch_input_packet_num, hdr.coding.packet_payload);
        mark_to_drop();
    }

    action copy_forward (bit<9> egress_port, bit<8> packet_contents) {

        reg_coding_payload_buffer.write(meta.coding_metadata.per_batch_input_packet_num, hdr.coding.packet_payload);
        send_from_ingress(egress_port, packet_contents);
    }

    action copy_forward_trigger (bit<9> egress_port, bit<8> packet_contents) {

        reg_coding_payload_buffer.write(meta.coding_metadata.per_batch_input_packet_num, hdr.coding.packet_payload);
        send_from_ingress(egress_port, packet_contents);
    }

    table table_input_splitting {
        key = {
                hdr.coding.stream_id: exact;
                meta.coding_metadata.per_batch_input_packet_num: exact;
              }

        actions = {_nop; copy; copy_trigger; copy_forward; copy_forward_trigger; }
        size = 10;
        default_action = _nop;
    }

    action copy_uncoded () {
        // Copy this packet to the correct buffer
        reg_payload_decoding_buffer_uncoded.write(meta.decoding_metadata.batch_idx, hdr.coding.packet_payload);

        // Update the register which keeps track of different types of packets received for a batch
        reg_uncoded_index.write(0, meta.decoding_metadata.batch_idx);

    }

    action copy_coded () {
        // Copy this packet to the correct buffer
        reg_payload_decoding_buffer_coded.write(meta.decoding_metadata.batch_idx, hdr.coding.packet_payload);

        // Update the register which keeps track of different types of packets received for a batch
        reg_coded_index.write(0, meta.decoding_metadata.batch_idx);
    }

    table table_input_gathering {
        key = {
                hdr.coding.stream_id: exact;
                meta.decoding_metadata.is_clone: exact;
                hdr.coding.packet_contents: exact;
                meta.decoding_metadata.per_batch_input_packet_num: exact;
              }

        actions = {_nop; copy_uncoded; copy_coded;}
        size = 10;
        default_action = _nop;
    }

    action code_forward (bit<9> egress_port, bit<1> continue_cloning) {
        payload_t operand1;
        payload_t operand2;
        reg_coding_payload_buffer.read(operand1, 0);
        reg_coding_payload_buffer.read(operand2, 1);
        hdr.coding.packet_payload = operand1 ^ operand2;
        send_from_ingress(egress_port, CODING_X);
        meta.coding_metadata.do_clone = continue_cloning;
    }

   action code_forward_passive (bit<9> egress_port, bit<1> continue_cloning) {
        payload_t operand1;
        payload_t operand2;
        reg_coding_payload_buffer.read(operand1, 0);
        reg_coding_payload_buffer.read(operand2, 1);
        hdr.coding.packet_payload = operand1 ^ operand2;
        send_from_ingress_no_batch(egress_port, CODING_X);
        meta.coding_metadata.do_clone = continue_cloning;
    }

    action cloning_start () {
        meta.coding_metadata.do_clone = DO_CLONE;
    }

    table table_ingress_code {
        key = {
                hdr.coding.stream_id: exact;
                meta.coding_metadata.coding_loop_index: exact;
                meta.coding_metadata.do_clone: exact;
              }

        actions = {_nop; cloning_start; code_forward; code_forward_passive;}
        size = 10;
        default_action = _nop;
    }

    table table_ingress_forward {
        key = {
                hdr.coding.stream_id: exact;
              }

        actions = {_nop; uni_cast; bi_cast;}
        size = 10;

    }

    action clone_uni_cast(bit<9> egress_port) {
        meta.decoding_metadata.is_clone = 2;
        uni_cast(egress_port);
    }

    action decode_using_register (bit<9> egress_port) {

        // Pickup the uncoded packet and xor it with this one to get the new payload
        payload_t uncoded_payload;
        reg_payload_decoding_buffer_uncoded.read(uncoded_payload, meta.decoding_metadata.batch_idx);
        hdr.coding.packet_payload = hdr.coding.packet_payload ^ uncoded_payload;

        uni_cast(egress_port);
    }

    action decode_using_cloned (bit<9> egress_port) {

        //fill up the clone with other payload by using the XOR coded payload in buffer
        payload_t coded_payload;
        reg_payload_decoding_buffer_coded.read(coded_payload, meta.decoding_metadata.batch_idx);
        hdr.coding.packet_payload = hdr.coding.packet_payload ^ coded_payload;
        hdr.coding.packet_contents = CODING_X;

        // To indicate that this no longer needs to be cloned/recirculated
        meta.decoding_metadata.is_clone = 0;

        uni_cast(egress_port);
    }

    table table_ingress_decode {
        key = {
                hdr.coding.stream_id: exact;
                meta.decoding_metadata.is_clone: exact;
                hdr.coding.packet_contents: exact;
                meta.decoding_metadata.per_batch_input_packet_num: exact;
                meta.decoding_metadata.per_batch_coded_received: exact;
              }

        actions = {_nop; drop; uni_cast; clone_uni_cast; decode_using_register; decode_using_cloned;}
        size = 10;
        default_action = drop;
    }

    table table_ingress_forward_contents {
        key = {
                hdr.coding.stream_id: exact;
                hdr.coding.packet_contents: exact;
              }

        actions = {_nop; uni_cast;}
        size = 10;
    }

    apply
    {
        if (hdr.coding.isValid()) {

            //Logic for Coding
            if (hdr.coding.next_primitive == CODING_PACKET_TO_CODE) {

                // Increase these counters for input packets
                if (meta.coding_metadata.coding_loop_index == 0)
                {
                    reg_num_coding_input_pkts.read(num_coding_input_pkts, 0);
                    reg_num_coding_input_pkts.write(0, num_coding_input_pkts + 1);
                    meta.coding_metadata.per_batch_input_packet_num = num_coding_input_pkts % CODING_INPUT_BATCH_SIZE;
                }

                // Hit the coding input table, it will know what to do with this packet
                switch(table_input_splitting.apply().action_run)
                {
                    copy_forward_trigger:
                    {
                        table_ingress_code.apply();
                    }
                    copy_trigger:
                    {
                        table_ingress_code.apply();
                    }
                }
            }

            //Logic for forwarding
            else if (hdr.coding.next_primitive == CODING_PACKET_TO_FORWARD) {

                if(!table_ingress_forward.apply().hit) {
                    table_ingress_forward_contents.apply();
                }

            }

            //Logic for decoding
            else if (hdr.coding.next_primitive == CODING_PACKET_TO_DECODE) {

                // First get which index the packets in this batch belong to...
                meta.decoding_metadata.batch_idx = hdr.coding.coded_packets_batch_num % DECODING_BUFFER_SIZE;

                //Get the current occupant batch_num of this index
                reg_rcv_batch_num_per_index.read(rcv_batch_num_per_index, meta.decoding_metadata.batch_idx);

                // Assume that batch numbers are never zero, then:
                // If the batch number of on the index is different than this packet then
                // Either the value in rcv_batch_num_per_index is zero (in which case, it was never used)
                // OR, rollover has occurred, reset the batch number in the buffer.
                if (hdr.coding.coded_packets_batch_num != rcv_batch_num_per_index)
                {
                    // And put the new batch_num in the buffer
                    reg_rcv_batch_num_per_index.write(meta.decoding_metadata.batch_idx, hdr.coding.coded_packets_batch_num);

                    // Reset the per-batch packet number register
                    reg_per_batch_input_packet_num.write(meta.decoding_metadata.batch_idx, 0);
                }

                // For non-cloned packets,
                // Update the register which keeps track of total number of packets received for a batch
                if (meta.decoding_metadata.is_clone == 0) {
                    reg_per_batch_input_packet_num.read(meta.decoding_metadata.per_batch_input_packet_num, meta.decoding_metadata.batch_idx);
                    meta.decoding_metadata.per_batch_input_packet_num = meta.decoding_metadata.per_batch_input_packet_num + 1;
                    reg_per_batch_input_packet_num.write(meta.decoding_metadata.batch_idx, meta.decoding_metadata.per_batch_input_packet_num);
                }

                // Do the gathering data gathering operation
                // Also, put what packet number for this batch this particular packet is, inside it.
                table_input_gathering.apply();

                // In each packet, keep track of whether a coded packet has been received for its batch...
                reg_coded_index.read(coded_index, 0);
                if (coded_index >= meta.decoding_metadata.batch_idx)
                {
                    meta.decoding_metadata.per_batch_coded_received = 1;
                }

                // Do the decoding
                table_ingress_decode.apply();

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
control CodingEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    register<bit<32>>(1) reg_num_bi_cast_forwarding_input_pkts;
    bit<32> num_bi_cast_forwarding_input_pkts;

    action _nop () {
    }

    action add_switch_stats(switchID_t swid) {
        hdr.stats.num_switch_stats = hdr.stats.num_switch_stats + 1;
        hdr.switch_stats.push_front(1);
        hdr.switch_stats[0].setValid();
        hdr.switch_stats[0].swid = swid;
        hdr.switch_stats[0].igt = (ingress_global_timestamp_t)standard_metadata.ingress_global_timestamp;
        hdr.switch_stats[0].enqt = (enq_timestamp_t)standard_metadata.enq_timestamp;
        hdr.switch_stats[0].delt = (deq_timedelta_t)standard_metadata.deq_timedelta;
    }

    action remove_switch_stats() {
        hdr.stats.num_switch_stats = hdr.stats.num_switch_stats - 1;
        hdr.switch_stats[0].setInvalid();
        hdr.switch_stats.pop_front(1);
    }

    table switch_stats {
        actions = {
        add_switch_stats;
        NoAction;
        }
        default_action = NoAction();
    }

    action egress_cloning_step(switchID_t swid) {

        // Stop cloning this so that recirculate step picks it up
        meta.coding_metadata.coding_loop_index = meta.coding_metadata.coding_loop_index + 1;

        standard_metadata.clone_spec = 250;
        clone3(CloneType.E2E, standard_metadata.clone_spec, {meta.intrinsic_metadata, meta.coding_metadata, standard_metadata});

        add_switch_stats(swid);
    }

    action egress_recirculate_step() {
        remove_switch_stats();
        recirculate({meta.intrinsic_metadata, meta.coding_metadata, standard_metadata});
    }

    table table_egress_code {
        key = {
                hdr.coding.stream_id: exact;
                meta.coding_metadata.coding_loop_index: exact;
                meta.coding_metadata.do_clone: exact;
              }
        actions = {egress_cloning_step; egress_recirculate_step;}
        size = 10;
    }


    action egress_decode_forward(switchID_t swid) {
        add_switch_stats(swid);
    }

    action egress_decode_recirculate_step() {
        remove_switch_stats();
        recirculate({meta.intrinsic_metadata, meta.decoding_metadata, standard_metadata});
    }

    action egress_decode_forward_clone(switchID_t swid) {

        // Stop recursive cloning and trigger recirculation
        meta.decoding_metadata.is_clone = 1;

        standard_metadata.clone_spec = 450;
        clone3(CloneType.E2E, standard_metadata.clone_spec, {meta.intrinsic_metadata, meta.decoding_metadata, standard_metadata});

        add_switch_stats(swid);
    }

    table table_egress_decode {
        key = {
                hdr.coding.stream_id: exact;
                meta.decoding_metadata.is_clone: exact;
              }
        actions = {egress_decode_recirculate_step; egress_decode_forward; egress_decode_forward_clone;}
        size = 10;
    }

    action forward_egress_processing_uni_cast(switchID_t swid, bit<8> next_packet_todo) {
        hdr.coding.next_primitive = next_packet_todo;
        add_switch_stats(swid);
    }

    action forward_egress_processing_bi_cast_for_orig(switchID_t swid) {
        hdr.coding.next_primitive = meta.forwarding_metadata.bi_cast_todo_for_orig;

        standard_metadata.clone_spec = 451;
        clone3(CloneType.E2E, standard_metadata.clone_spec, {meta.intrinsic_metadata, meta.forwarding_metadata, standard_metadata});

        add_switch_stats(swid);
    }

    action forward_egress_processing_bi_cast_for_clone(switchID_t swid) {
        remove_switch_stats();

        hdr.coding.next_primitive = meta.forwarding_metadata.bi_cast_todo_for_clone;

        add_switch_stats(swid);
    }

    table table_egress_forward {
        key = {
                hdr.coding.stream_id: exact;
                meta.forwarding_metadata.is_bi_cast: exact;
                meta.forwarding_metadata.bi_cast_instance_num: exact;
              }

        actions = {_nop; forward_egress_processing_uni_cast; forward_egress_processing_bi_cast_for_orig;
                    forward_egress_processing_bi_cast_for_clone;}
        size = 10;
        default_action = _nop;
    }

    table table_egress_forward_bi_cast {
        key = {
                hdr.coding.stream_id: exact;
                meta.forwarding_metadata.is_bi_cast: exact;
                meta.forwarding_metadata.bi_cast_instance_num: exact;
              }

        actions = {_nop; forward_egress_processing_uni_cast; forward_egress_processing_bi_cast_for_orig;
                    forward_egress_processing_bi_cast_for_clone;}
        size = 10;
        default_action = _nop;
    }

    apply {
        if (hdr.coding.isValid()) {

            if (meta.forwarding_metadata.is_bi_cast == 0) {

                // Logic for coding has three type of packets...

                // These are packets that just came from ingress and will be cloned and sent out...
                if (hdr.coding.next_primitive == CODING_PACKET_TO_CODE && meta.coding_metadata.do_clone == DO_CLONE)
                {
                    // Ensure that the outgoing packet is correctly forwarded by the next hop
                    hdr.coding.next_primitive = CODING_PACKET_TO_FORWARD;
                    table_egress_code.apply();
                }

                // These are packets that are being recirculated
                else if (hdr.coding.next_primitive == CODING_PACKET_TO_FORWARD && meta.coding_metadata.do_clone == DO_CLONE)
                {
                    // Switch these back to coding
                    hdr.coding.next_primitive = CODING_PACKET_TO_CODE;
                    table_egress_code.apply();
                }
                // These are packets after the recirculated packets return from ingress
                else if (hdr.coding.next_primitive == CODING_PACKET_TO_CODE && meta.coding_metadata.do_clone == DONT_CLONE)
                {
                    // Ensure that the outgoing packet is correctly forwarded by the next hop
                    hdr.coding.next_primitive = CODING_PACKET_TO_FORWARD;
                    switch_stats.apply();
                }

                // Logic to forward
                else if (hdr.coding.next_primitive == CODING_PACKET_TO_FORWARD) {
                    table_egress_forward.apply();
                }

                // Logic for decoding
                else if (hdr.coding.next_primitive == CODING_PACKET_TO_DECODE) {
                    table_egress_decode.apply();
                }

            } else if (meta.forwarding_metadata.is_bi_cast == 1) {

                reg_num_bi_cast_forwarding_input_pkts.read(num_bi_cast_forwarding_input_pkts, 0);
                reg_num_bi_cast_forwarding_input_pkts.write(0, num_bi_cast_forwarding_input_pkts + 1);

                meta.forwarding_metadata.bi_cast_instance_num = num_bi_cast_forwarding_input_pkts % 2;

                table_egress_forward_bi_cast.apply();

                if (hdr.coding.next_primitive == CODING_PACKET_TO_CODE) {
                    reg_num_bi_cast_forwarding_input_pkts.read(num_bi_cast_forwarding_input_pkts, 0);
                } else
                if (hdr.coding.next_primitive == CODING_PACKET_TO_DECODE) {
                    reg_num_bi_cast_forwarding_input_pkts.read(num_bi_cast_forwarding_input_pkts, 0);
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

control CodingComputeChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

/*************************************************************************
 ***********************  D E P A R S E R  *******************************
 *************************************************************************/
control CodingDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.stats);
        packet.emit(hdr.switch_stats);
        packet.emit(hdr.coding);
    }
}

/*************************************************************************
 ***********************  S W I T T C H **********************************
 *************************************************************************/

V1Switch(
CodingParser(),
CodingVerifyChecksum(),
CodingIngress(),
CodingEgress(),
CodingComputeChecksum(),
CodingDeparser()
) main;
