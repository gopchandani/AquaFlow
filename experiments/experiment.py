import os
import argparse
import json


def process_file_name(f_name):
    new_f_name = ""

    for i in xrange(0, len(f_name)):

        if f_name[i] == "/":
            new_f_name = new_f_name + "\\/"
        else:
            new_f_name = new_f_name + f_name[i]

    return new_f_name


def modify_experiment_json_for_dev_mode(exp_json_file_path):

    # Open the JSON File
    with open(exp_json_file_path, 'r') as infile:
        experiment_json = json.load(infile)

    # Make the modifications
    experiment_json["targets"]["multiswitch"]["cli"] = True
    experiment_json["targets"]["multiswitch"]["pcap_dump"] = True
    experiment_json["targets"]["multiswitch"]["bmv2_log"] = True

    for host_dict in experiment_json["targets"]["multiswitch"]["hosts"].values():
        host_dict.clear()

    # Write the JSON File
    with open(exp_json_file_path, 'w') as outfile:
        json.dump(experiment_json, outfile, indent=2)


def run_diversity_experiment(AquaFlow_dir, base_delay, dev_mode, differential, npackets, payload, iface):

    print differential
    print payload

    assert differential >= -5
    assert differential <= 5
    assert payload >= 1

    templates_dir = AquaFlow_dir + "/templates"

    if differential > 0:
        differential_str = "plus_" + str(differential)
    elif differential < 0:
        differential_str = "minus_" + str(-1 * differential)
    else:
        differential_str = "0"

    experiment_name = "payload_" + str(payload) + "_differential_" + str(differential_str) + ".json"

    log_file = AquaFlow_dir + "/experiments/data/" + "diversity" + "_" + experiment_name

    AquaFlow_dir_fmt = process_file_name(AquaFlow_dir)
    log_file_fmt = process_file_name(log_file)
    dst_dir = AquaFlow_dir + "/" + "diversity"

    cmd_1 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) + "/g\' " + str(
        templates_dir) + "/aqua_flow_template.p4 > " + dst_dir + "/aqua_flow.p4"
    # print cmd_1
    os.system(cmd_1)

    cmd_2 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) \
            + "/g; s/@AQUA_FLOW_DIR@/" + str(AquaFlow_dir_fmt) \
            + "/g; s/@IFACE@/" + str(iface) \
            + "/g; s/@N_PACKETS@/" + str(npackets) \
            + "/g; s/@LOG_FILE@/" + str(log_file_fmt) \
            + "/g; s/@d1@/" + str(base_delay) \
            + "/g; s/@d2@/" + str(base_delay + differential) + "/g\' " \
            + str(templates_dir) + "/p4app." + "diversity" + ".json.template > " + dst_dir + "/p4app" + ".json"

    os.system(cmd_2)

    if dev_mode:
        modify_experiment_json_for_dev_mode(dst_dir + "/p4app" + ".json")

    print "Starting Experiment ..."
    os.system("sudo " + AquaFlow_dir + "/run.sh " + "diversity")
    os.system("sudo chmod -R 777 " + str(AquaFlow_dir))


def run_butterfly_experiment(AquaFlow_dir, base_delay, dev_mode, iface1, iface2, npackets, payload, send_rate, bw):

    base_delay = 0
    assert (payload >= 1 and payload % 8 == 0)

    templates_dir = AquaFlow_dir + "/templates"

    experiment_name = "payload_" + str(payload) + "_send_rate_" + str(send_rate)

    log_file_1 = AquaFlow_dir + "/experiments/data/" + "butterfly" + "_" + experiment_name + "_recv_1.json" 
    log_file_2 = AquaFlow_dir + "/experiments/data/" + "butterfly" + "_" + experiment_name + "_recv_2.json" 
    AquaFlow_dir_fmt = process_file_name(AquaFlow_dir)
    log_file_1_fmt = process_file_name(log_file_1)
    log_file_2_fmt = process_file_name(log_file_2)

    dst_dir = AquaFlow_dir + "/" + "butterfly"

    cmd_1 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) + "/g\' " + str(
        templates_dir) + "/aqua_flow_template.p4 > " + dst_dir + "/aqua_flow.p4"
    # print cmd_1
    os.system(cmd_1)

    cmd_2 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) \
            + "/g; s/@AQUA_FLOW_DIR@/" + str(AquaFlow_dir_fmt) \
            + "/g; s/@IFACE1@/" + str(iface1) \
            + "/g; s/@IFACE2@/" + str(iface2) \
            + "/g; s/@N_PACKETS@/" + str(npackets) \
            + "/g; s/@LOG_FILE_1@/" + str(log_file_1_fmt) \
            + "/g; s/@LOG_FILE_2@/" + str(log_file_2_fmt) \
            + "/g; s/@d1@/" + str(base_delay) \
            + "/g; s/@bw@/" + str(bw) \
            + "/g; s/@bw2@/" + str(2*bw) \
             + "/g; s/@RATE@/" + str(send_rate) \
            + "/g\' " \
            + str(templates_dir) + "/p4app." + "butterfly" + ".json.template > " + dst_dir + "/p4app" + ".json"

    os.system(cmd_2)

    if dev_mode:
        modify_experiment_json_for_dev_mode(dst_dir + "/p4app" + ".json")

    print "Starting Experiment ..."
    os.system("sudo " + AquaFlow_dir + "/run.sh " + "butterfly")
    os.system("sudo chmod -R 777 " + str(AquaFlow_dir))


def run_bigger_butterfly_experiment(AquaFlow_dir, base_delay, dev_mode, iface1, iface2, iface3, npackets, payload, send_rate, bw):
    base_delay = 0
    assert (payload >= 1 and payload % 8 == 0)

    templates_dir = AquaFlow_dir + "/templates"

    experiment_name = "payload_" + str(payload) + "_send_rate_" + str(send_rate)

    log_file_1 = AquaFlow_dir + "/experiments/data/" + "bigger_butterfly" + "_" + experiment_name + "_recv_1.json"
    log_file_2 = AquaFlow_dir + "/experiments/data/" + "bigger_butterfly" + "_" + experiment_name + "_recv_2.json"
    log_file_3 = AquaFlow_dir + "/experiments/data/" + "bigger_butterfly" + "_" + experiment_name + "_recv_3.json"

    AquaFlow_dir_fmt = process_file_name(AquaFlow_dir)
    log_file_1_fmt = process_file_name(log_file_1)
    log_file_2_fmt = process_file_name(log_file_2)
    log_file_3_fmt = process_file_name(log_file_3)

    dst_dir = AquaFlow_dir + "/" + "bigger_butterfly"

    cmd_1 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) + "/g\' " + str(
        templates_dir) + "/aqua_flow_template.p4 > " + dst_dir + "/aqua_flow.p4"
    # print cmd_1
    os.system(cmd_1)

    cmd_2 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) \
            + "/g; s/@AQUA_FLOW_DIR@/" + str(AquaFlow_dir_fmt) \
            + "/g; s/@IFACE1@/" + str(iface1) \
            + "/g; s/@IFACE2@/" + str(iface2) \
            + "/g; s/@IFACE3@/" + str(iface3) \
            + "/g; s/@N_PACKETS@/" + str(npackets) \
            + "/g; s/@LOG_FILE_1@/" + str(log_file_1_fmt) \
            + "/g; s/@LOG_FILE_2@/" + str(log_file_2_fmt) \
            + "/g; s/@LOG_FILE_3@/" + str(log_file_3_fmt) \
            + "/g; s/@d1@/" + str(base_delay) \
            + "/g; s/@bw@/" + str(bw) \
            + "/g; s/@bw2@/" + str(2 * bw) \
            + "/g; s/@RATE@/" + str(send_rate) \
            + "/g\' " \
            + str(templates_dir) + "/p4app." + "bigger_butterfly" + ".json.template > " + dst_dir + "/p4app" + ".json"

    os.system(cmd_2)

    if dev_mode:
        modify_experiment_json_for_dev_mode(dst_dir + "/p4app" + ".json")

    print "Starting Experiment ..."
    os.system("sudo " + AquaFlow_dir + "/run.sh " + "bigger_butterfly")
    os.system("sudo chmod -R 777 " + str(AquaFlow_dir))


def run_butterfly_fwd_experiment(AquaFlow_dir, base_delay, dev_mode, iface1, iface2, npackets, payload, send_rate, bw):

    base_delay = 0
    assert (payload >= 1 and payload % 8 == 0)

    print "Running Butterfly FWD experiment ..."
    templates_dir = AquaFlow_dir + "/templates"

    experiment_name = "payload_" + str(payload) + "_send_rate_" + str(send_rate)

    log_file_1 = AquaFlow_dir + "/experiments/data/" + "butterfly_forwarding_" + "_" + experiment_name + "_recv_1.json" 
    log_file_2 = AquaFlow_dir + "/experiments/data/" + "butterfly_forwarding_" + "_" + experiment_name + "_recv_2.json" 
    AquaFlow_dir_fmt = process_file_name(AquaFlow_dir)
    log_file_1_fmt = process_file_name(log_file_1)
    log_file_2_fmt = process_file_name(log_file_2)

    dst_dir = AquaFlow_dir + "/" + "butterfly_forwarding"

    cmd_1 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) + "/g\' " + str(
        templates_dir) + "/aqua_flow_template.p4 > " + dst_dir + "/aqua_flow.p4"
    # print cmd_1
    os.system(cmd_1)

    cmd_2 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) \
            + "/g; s/@AQUA_FLOW_DIR@/" + str(AquaFlow_dir_fmt) \
            + "/g; s/@IFACE1@/" + str(iface1) \
            + "/g; s/@IFACE2@/" + str(iface2) \
            + "/g; s/@N_PACKETS@/" + str(npackets) \
            + "/g; s/@LOG_FILE_1@/" + str(log_file_1_fmt) \
            + "/g; s/@LOG_FILE_2@/" + str(log_file_2_fmt) \
            + "/g; s/@d1@/" + str(base_delay) \
            + "/g; s/@bw@/" + str(bw) \
            + "/g; s/@bw2@/" + str(2*bw) \
             + "/g; s/@RATE@/" + str(send_rate) \
            + "/g\' " \
            + str(templates_dir) + "/p4app." + "butterfly" + ".json.template > " + dst_dir + "/p4app" + ".json"

    os.system(cmd_2)

    if dev_mode:
        modify_experiment_json_for_dev_mode(dst_dir + "/p4app" + ".json")

    print "Starting Experiment ..."
    os.system("sudo " + AquaFlow_dir + "/run.sh " + "butterfly_forwarding")
    os.system("sudo chmod -R 777 " + str(AquaFlow_dir))


def main():

    AquaFlow_dir = os.path.dirname(os.path.realpath(__file__)) + "/.."
    base_delay = 5

    parser = argparse.ArgumentParser(description='Script to run coding experiments')
    parser.add_argument('--differential', dest="differential", help='differential added to s1-s4 link',
                        type=str, action="store", default="0")

    parser.add_argument('--payload', dest="payload", help='payload size',
                        type=str, action="store", required=True)

    parser.add_argument('--npackets', dest="npackets", help='number of packets to send/receive',
                        type=str, action="store", default="100")

    parser.add_argument('--iface', dest="iface", help='iface for recv stream in diversity code',
                        type=str, action="store", default="h2-eth0")

    parser.add_argument('--iface1', dest="iface1", help='iface for recv stream in diversity code',
                        type=str, action="store", default="h2-eth0")

    parser.add_argument('--iface2', dest="iface2", help='iface for recv stream in diversity code',
                        type=str, action="store", default="h3-eth0")

    parser.add_argument('--iface3', dest="iface3", help='iface for recv stream in diversity code',
                        type=str, action="store", default="h4-eth0")

    parser.add_argument('--type', dest="type", help='Experiment type',
                        type=str, action="store", default="diversity")

    parser.add_argument('--dev_mode', dest="dev_mode", help='Turn on the logs and CLI.',
                        action="store_true", default=False)

    parser.add_argument('--rate', dest="rate", help='send rate for butterfly/butterfly forwarding', type=float, action="store", default=0.0)
    parser.add_argument('--bw', dest="bw", help='Bandwidth in Mbits/sec for all links', type=float, action="store", default=0.5)

    args = parser.parse_args()

    if args.type == "diversity":
        run_diversity_experiment(AquaFlow_dir, base_delay, args.dev_mode,
                                 int(args.differential), int(args.npackets), int(args.payload), args.iface)

    elif args.type == "butterfly" :
        run_butterfly_experiment(AquaFlow_dir, base_delay, args.dev_mode,
                                 args.iface1, args.iface2, int(args.npackets), int(args.payload), float(args.rate), float(args.bw))
    elif args.type == "butterfly_forwarding":
        run_butterfly_fwd_experiment(AquaFlow_dir, base_delay, args.dev_mode,
                                     args.iface1, args.iface2, int(args.npackets), int(args.payload), float(args.rate), float(args.bw))
    elif args.type == "bigger_butterfly":
        run_bigger_butterfly_experiment(AquaFlow_dir, base_delay, args.dev_mode,
                                        args.iface1, args.iface2, args.iface3, int(args.npackets), int(args.payload), float(args.rate), float(args.bw))
    else:
        print "Invalid experiment type:", args.type


if __name__ == '__main__':
    main()
