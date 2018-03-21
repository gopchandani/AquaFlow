import sys
import os

import argparse
import matplotlib
import json
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as axes3d
import math


AquaFlow_dir = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Coding experiment')
parser.add_argument('--experiment_data_dir', dest="experiment_data_dir", help='Location of experiments data', type=str, action="store")

args = parser.parse_args()



experiment_dir = AquaFlow_dir + args.experiment_data_dir



def plot_butterfly_results() :

	payload = 4096
	rates = [0.01 ,0.02, 0.03, 0.04 ,0.05, 0.06 ,0.07 ,0.08, 0.09, 0.1]

	coding_throughput = []
	forwarding_throughput = []

	for rate in rates :

		f_name1 = experiment_dir + "/butterfly" + "_payload_" + str(payload) + "_send_rate_" + str(rate) + "_recv_1.json"
		f_name2 = experiment_dir + "/butterfly" + "_payload_" + str(payload) + "_send_rate_" + str(rate) + "_recv_2.json"
		f_name3 = experiment_dir + "/butterfly_forwarding_" + "_payload_" + str(payload) + "_send_rate_" + str(rate) + "_recv_1.json"
		f_name4 = experiment_dir + "/butterfly_forwarding_" + "_payload_" + str(payload) + "_send_rate_" + str(rate) + "_recv_2.json"



		with open(f_name1, 'r') as infile1:
			rcvd_pkt_metrics_dict1 = json.load(infile1)

		with open(f_name2, 'r') as infile2:
			rcvd_pkt_metrics_dict2 = json.load(infile2)

		with open(f_name3, 'r') as infile3:
			rcvd_pkt_metrics_dict3 = json.load(infile3)

		with open(f_name4, 'r') as infile4:
			rcvd_pkt_metrics_dict4 = json.load(infile4)


		if rcvd_pkt_metrics_dict1['time_diff'] > rcvd_pkt_metrics_dict2['time_diff'] :
			coding_throughput.append(float(rcvd_pkt_metrics_dict1['throughput']))
		else:
			coding_throughput.append(float(rcvd_pkt_metrics_dict2['throughput']))

		if rcvd_pkt_metrics_dict3['time_diff'] > rcvd_pkt_metrics_dict4['time_diff'] :
			forwarding_throughput.append(float(rcvd_pkt_metrics_dict3['throughput']))
		else:
			forwarding_throughput.append(float(rcvd_pkt_metrics_dict4['throughput']))


	fig = plt.figure(dpi=100)
	ax = fig.add_subplot(111)


	ax.plot(rates, coding_throughput, marker="o", label = "Data receive rate with coding")
	ax.plot(rates, forwarding_throughput, marker = "*", label="Data receive rate with forwarding")

	ax.set_xlabel("Avg Data Transmission rate (Mbits per sec)")
	ax.set_ylabel("Observed Data Receive rate (Mbits per sec)")

	ax.legend(loc='best')
	ax.set_xticks(rates)

	plt.show()



plot_butterfly_results()