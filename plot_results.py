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
parser.add_argument('--type', dest="type", help='exp type', type=str, action="store", default="diversity")

args = parser.parse_args()

assert(args.type == "diversity" or args.type == "butterfly")


experiment_dir = AquaFlow_dir + "/experiment"

payloads = [128, 256, 512, 1024, 2048, 4096]
differentials = [-5, -1, 0, 1, 5]
n_packets = 200
m_factor = 1.96/math.sqrt(n_packets)

stats  = {}

for diff in differentials :

	for payload in payloads :

		if diff < 0 :
			diff_str = "minus_" + str(-1*diff) + ".json"
		elif diff > 0 :
			diff_str = "plus_" + str(diff) + ".json"
		else:
			diff_str = "0.json"

		f_name = experiment_dir + "/" + args.type + "_payload_" + str(payload) + "_differential_" + diff_str

		
		if diff not in stats :
			stats[diff] = {}
		if payload not in stats[diff]:
			stats[diff][payload] = { "coding" : None,
									 "decoding" : None,
									 "forwarding" : None
									}

		
		with open(f_name, 'r') as infile:
			rcvd_pkt_metrics_dict = json.load(infile)

		coding_times = rcvd_pkt_metrics_dict['A']["coding"] + rcvd_pkt_metrics_dict['B']["coding"]
		decoding_times = rcvd_pkt_metrics_dict['A']["decoding"] + rcvd_pkt_metrics_dict['B']["decoding"]
		forwarding_times = rcvd_pkt_metrics_dict['A']["forwarding"] + rcvd_pkt_metrics_dict['B']["forwarding"]



		stats[diff][payload]["coding"] = [np.mean(coding_times), np.std(coding_times)]
		stats[diff][payload]["decoding"] = [np.mean(decoding_times), np.std(decoding_times)]
		stats[diff][payload]["forwarding"] = [np.mean(forwarding_times), np.std(forwarding_times)]


fig = plt.figure(dpi=100)
ax = fig.add_subplot(111, projection='3d')

x = differentials
y = payloads

for i in xrange(0,len(differentials)):
	

	for j in xrange(0, len(payloads)) :

		ptc = []
		ptd = []
		ptf = []
		ptc.append([differentials[i], differentials[i]])
		ptd.append([differentials[i], differentials[i]])
		ptf.append([differentials[i], differentials[i]])
		ptc.append([payloads[j], payloads[j]])
		ptd.append([payloads[j], payloads[j]])
		ptf.append([payloads[j], payloads[j]])

		zc_max = stats[differentials[i]][payloads[j]]["coding"][0] + m_factor*stats[differentials[i]][payloads[j]]["coding"][1]
		zc_min = stats[differentials[i]][payloads[j]]["coding"][0] - m_factor*stats[differentials[i]][payloads[j]]["coding"][1]
		zc = stats[differentials[i]][payloads[j]]["coding"][0]

		zd_max = stats[differentials[i]][payloads[j]]["decoding"][0] + m_factor*stats[differentials[i]][payloads[j]]["decoding"][1]
		zd_min = stats[differentials[i]][payloads[j]]["decoding"][0] - m_factor*stats[differentials[i]][payloads[j]]["decoding"][1]
		zd = stats[differentials[i]][payloads[j]]["decoding"][0]

		zf_max = stats[differentials[i]][payloads[j]]["forwarding"][0] + m_factor*stats[differentials[i]][payloads[j]]["forwarding"][1]
		zf_min = stats[differentials[i]][payloads[j]]["forwarding"][0] - m_factor*stats[differentials[i]][payloads[j]]["forwarding"][1]
		zf = stats[differentials[i]][payloads[j]]["forwarding"][0]


		#print zc

		if i == 0 and j == 0 :
			ax.plot([differentials[i]], [payloads[j]], [zc], marker="o", color="red", label='Coding')
			ax.plot([differentials[i]], [payloads[j]], [zd], marker="*", color="blue", label='Decoding')
			ax.plot([differentials[i]], [payloads[j]], [zf], marker="^", color="black", label='Forwarding')
		else:
			ax.plot([differentials[i]], [payloads[j]], [zc], marker="o", color="red")
			ax.plot([differentials[i]], [payloads[j]], [zd], marker="*", color="blue")
			ax.plot([differentials[i]], [payloads[j]], [zf], marker="^", color="black")

		ptc.append([zc_max, zc_min])
		ptd.append([zd_max, zd_min])
		ptf.append([zf_max, zf_min])


		ax.plot(ptc[0], ptc[1], ptc[2], marker="_", color="red")
		ax.plot(ptd[0], ptd[1], ptd[2], marker="_", color="blue")
		ax.plot(ptf[0], ptf[1], ptf[2], marker="_", color="black")


ax.set_xlabel("Differential")
ax.set_xticks(differentials)
ax.set_ylabel("Payload Size (Bytes)")
ax.legend()
ax.set_yticklabels(payloads, rotation=-45)
ax.set_yticks(payloads)
ax.set_zlabel("Processing Time")
plt.show()
		

