import sys
import os

import argparse
import matplotlib
import json
import numpy as np
import matplotlib.pyplot as plt
import math

AquaFlow_dir = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Coding experiment')
parser.add_argument('--type', dest="type", help='exp type', type=str, action="store", default="diversity")
parser.add_argument('--experiment_data_dir', dest="experiment_data_dir", help='Location of experiments data', type=str,
                    action="store")

args = parser.parse_args()

assert (args.type == "diversity" or args.type == "butterfly")

experiment_dir = AquaFlow_dir + args.experiment_data_dir


def plot_diversity_results():
    payloads = [128, 1024, 2048, 4096]
    differentials = [-5, -1, 0, 1, 5]
    n_packets = 1000
    m_factor = 1.96 / math.sqrt(n_packets)

    stats = {}

    for diff in differentials:

        for payload in payloads:

            if diff < 0:
                diff_str = "minus_" + str(-1 * diff) + ".json"
            elif diff > 0:
                diff_str = "plus_" + str(diff) + ".json"
            else:
                diff_str = "0.json"

            f_name = experiment_dir + "/" + args.type + "_payload_" + str(payload) + "_differential_" + diff_str

            if diff not in stats:
                stats[diff] = {}
            if payload not in stats[diff]:
                stats[diff][payload] = {"coding": None,
                                        "decoding": None,
                                        "forwarding": None
                                        }

            with open(f_name, 'r') as infile:
                rcvd_pkt_metrics_dict = json.load(infile)

            coding_times = rcvd_pkt_metrics_dict['A']["coding"] + rcvd_pkt_metrics_dict['B']["coding"]
            decoding_times = rcvd_pkt_metrics_dict['A']["decoding"] + rcvd_pkt_metrics_dict['B']["decoding"]
            forwarding_times = rcvd_pkt_metrics_dict['A']["forwarding"] + rcvd_pkt_metrics_dict['B']["forwarding"]

            coding_times = [x / 1000 for x in coding_times]
            decoding_times = [x / 1000 for x in decoding_times]
            forwarding_times = [x / 1000 for x in forwarding_times]

            stats[diff][payload]["coding"] = [np.mean(coding_times), np.std(coding_times)]
            stats[diff][payload]["decoding"] = [np.mean(decoding_times), np.std(decoding_times)]
            stats[diff][payload]["forwarding"] = [np.mean(forwarding_times), np.std(forwarding_times)]

    fig = plt.figure(dpi=100)
    ax = fig.add_subplot(111, projection='3d')

    x = differentials
    y = payloads

    for i in xrange(0, len(differentials)):

        for j in xrange(0, len(payloads)):

            ptc = []
            ptd = []
            ptf = []
            ptc.append([differentials[i], differentials[i]])
            ptd.append([differentials[i], differentials[i]])
            ptf.append([differentials[i], differentials[i]])
            ptc.append([payloads[j], payloads[j]])
            ptd.append([payloads[j], payloads[j]])
            ptf.append([payloads[j], payloads[j]])

            zc_max = stats[differentials[i]][payloads[j]]["coding"][0] + m_factor * \
                     stats[differentials[i]][payloads[j]]["coding"][1]
            zc_min = stats[differentials[i]][payloads[j]]["coding"][0] - m_factor * \
                     stats[differentials[i]][payloads[j]]["coding"][1]
            zc = stats[differentials[i]][payloads[j]]["coding"][0]

            zd_max = stats[differentials[i]][payloads[j]]["decoding"][0] + m_factor * \
                     stats[differentials[i]][payloads[j]]["decoding"][1]
            zd_min = stats[differentials[i]][payloads[j]]["decoding"][0] - m_factor * \
                     stats[differentials[i]][payloads[j]]["decoding"][1]
            zd = stats[differentials[i]][payloads[j]]["decoding"][0]

            zf_max = stats[differentials[i]][payloads[j]]["forwarding"][0] + m_factor * \
                     stats[differentials[i]][payloads[j]]["forwarding"][1]
            zf_min = stats[differentials[i]][payloads[j]]["forwarding"][0] - m_factor * \
                     stats[differentials[i]][payloads[j]]["forwarding"][1]
            zf = stats[differentials[i]][payloads[j]]["forwarding"][0]

            # print zc

            if i == 0 and j == 0:
                ax.plot([differentials[i]], [payloads[j]], [zc], marker="o", color="red", label='Coding')
                ax.plot([differentials[i]], [payloads[j]], [zd], marker="*", color="blue", label='Decoding')
                ax.plot([differentials[i]], [payloads[j]], [zf], marker=".", color="black", label='Forwarding')
            else:
                ax.plot([differentials[i]], [payloads[j]], [zc], marker="o", color="red")
                ax.plot([differentials[i]], [payloads[j]], [zd], marker="*", color="blue")
                ax.plot([differentials[i]], [payloads[j]], [zf], marker=".", color="black")

            ptc.append([zc_max, zc_min])
            ptd.append([zd_max, zd_min])
            ptf.append([zf_max, zf_min])

            ax.plot(ptc[0], ptc[1], ptc[2], marker="_", color="red")
            ax.plot(ptd[0], ptd[1], ptd[2], marker="_", color="blue")
            ax.plot(ptf[0], ptf[1], ptf[2], marker="_", color="black")

    ax.set_xlabel("Link Delay Differential (ms)", fontsize=11)
    ax.set_xticks(differentials)
    ax.set_ylabel("Payload Size (Bytes)", fontsize=11)
    ax.legend(ncol=4, loc=9, fontsize=11, bbox_to_anchor=(0, 1.02, 1, .102))
    ax.set_yticklabels(payloads)
    ax.set_yticks(payloads)
    ax.set_zlabel("Processing Time (ms)", fontsize=11)
    plt.show()


def plot_butterfly_results():
    payload = 4096
    rates = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]

    coding_throughput = []
    forwarding_throughput = []

    for rate in rates:

        f_name1 = experiment_dir + "/butterfly" + "_payload_" + str(payload) + "_send_rate_" + str(
            rate) + "_recv_1.json"
        f_name2 = experiment_dir + "/butterfly" + "_payload_" + str(payload) + "_send_rate_" + str(
            rate) + "_recv_2.json"
        f_name3 = experiment_dir + "/butterfly_forwarding_" + "_payload_" + str(payload) + "_send_rate_" + str(
            rate) + "_recv_1.json"
        f_name4 = experiment_dir + "/butterfly_forwarding_" + "_payload_" + str(payload) + "_send_rate_" + str(
            rate) + "_recv_2.json"

        with open(f_name1, 'r') as infile1:
            rcvd_pkt_metrics_dict1 = json.load(infile1)

        with open(f_name2, 'r') as infile2:
            rcvd_pkt_metrics_dict2 = json.load(infile2)

        with open(f_name3, 'r') as infile3:
            rcvd_pkt_metrics_dict3 = json.load(infile3)

        with open(f_name4, 'r') as infile4:
            rcvd_pkt_metrics_dict4 = json.load(infile4)

        if rcvd_pkt_metrics_dict1['time_diff'] > rcvd_pkt_metrics_dict2['time_diff']:
            coding_throughput.append(
                float(rcvd_pkt_metrics_dict1['throughput']) / float(rcvd_pkt_metrics_dict1['send_rate']))
        else:
            coding_throughput.append(
                float(rcvd_pkt_metrics_dict2['throughput']) / float(rcvd_pkt_metrics_dict2['send_rate']))

        val1 = (float(rcvd_pkt_metrics_dict3['throughput']) + float(rcvd_pkt_metrics_dict4['throughput'])) / (2 * float(rcvd_pkt_metrics_dict3['send_rate']))
        val2 = float(rcvd_pkt_metrics_dict3['throughput']) / float(rcvd_pkt_metrics_dict3['send_rate'])
        val3 = float(rcvd_pkt_metrics_dict4['throughput']) / float(rcvd_pkt_metrics_dict4['send_rate'])

        print "Forwarding:", val1, val2, val3

        forwarding_throughput.append(val1)

        # if rcvd_pkt_metrics_dict3['time_diff'] > rcvd_pkt_metrics_dict4['time_diff']:
        #     forwarding_throughput.append(
        #         float(rcvd_pkt_metrics_dict3['throughput']) / float(rcvd_pkt_metrics_dict3['send_rate']))
        # else:
        #     forwarding_throughput.append(
        #         float(rcvd_pkt_metrics_dict4['throughput']) / float(rcvd_pkt_metrics_dict4['send_rate']))

    fig = plt.figure(dpi=100)
    ax = fig.add_subplot(111)

    max_flow = 0.1
    rates = [x / max_flow for x in rates]

    ax.plot(rates, coding_throughput, marker="o", label="With Coding")
    ax.plot(rates, forwarding_throughput, marker="*", label="With Forwarding")

    ax.set_xlabel("Send Rate / Max Flow", fontsize=11)
    ax.set_ylabel("Received Rate / Send Rate", fontsize=11)

    ax.legend(loc=9, ncol=2, fontsize=11, bbox_to_anchor=(0, 1.02, 1, .102))
    ax.set_xticks(rates)

    plt.show()
    plt.savefig("butterfly_experiment.png")


if args.type == "diversity":
    plot_diversity_results()
else:
    plot_butterfly_results()
