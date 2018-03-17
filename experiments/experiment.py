import sys
import os

import argparse

AquaFlow_dir = os.path.dirname(os.path.realpath(__file__))
base_delay = 5


def process_file_name(f_name):

	new_f_name = ""

	for i in xrange(0, len(f_name)):

		if f_name[i] == "/":
			new_f_name = new_f_name + "\\/"
		else:
			new_f_name = new_f_name + f_name[i]

	return new_f_name


parser = argparse.ArgumentParser(description='Coding experiment')
parser.add_argument('--differential', dest="differential", help='differential added to s1-s4 link',
                    type=str, action="store", required=True)
parser.add_argument('--payload', dest="payload", help='payload size',
                    type=str, action="store", required=True)
parser.add_argument('--npackets', dest="npackets", help='number of packets to send/receive', type=str, action="store", default="100")
parser.add_argument('--iface', dest="iface", help='iface for recv stream', type=str, action="store", default="h2-eth0")
parser.add_argument('--type', dest="type", help='exp type', type=str, action="store", default="diversity")

args = parser.parse_args()

assert(args.type == "diversity" or args.type == "butterfly")


differential = int(args.differential)
n_packets = int(args.npackets)
payload = int(args.payload)
iface = str(args.iface)

assert(differential >= -5 and differential <= 5 and payload >= 1)

templates_dir = AquaFlow_dir + "/templates"

if differential > 0 :
	differential_str = "plus_" + str(differential)
elif differential < 0:
	differential_str = "minus_" + str(-1*differential)
else:
	differential_str = "0"

experiment_name = "payload_" + str(payload) + "_differential_" + str(differential_str) + ".json"

log_file = AquaFlow_dir + "/experiment/" + str(args.type)  + "_" + experiment_name

AquaFlow_dir_fmt = process_file_name(AquaFlow_dir)
log_file_fmt = process_file_name(log_file)
experiment_dir = AquaFlow_dir + "/experiement"


cmd_1 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) + "/g\' " + str(templates_dir) + "/aqua_flow_template.p4 > " + AquaFlow_dir + "/aqua_flow.p4"
#print cmd_1
os.system(cmd_1)

cmd_2 = "sed -e \'s/@PAYLOAD_SIZE@/" + str(payload) \
	 			+ "/g; s/@AQUA_FLOW_DIR@/" + str(AquaFlow_dir_fmt) \
	 			+ "/g; s/@IFACE@/" + str(iface) 	\
	 			+ "/g; s/@N_PACKETS@/" + str(n_packets)	\
	 			+ "/g; s/@LOG_FILE@/" + str(log_file_fmt)	\
	 			+ "/g; s/@d1@/" + str(base_delay)	\
	 			+ "/g; s/@d2@/" + str(base_delay + differential) + "/g\' " \
	 			+ str(templates_dir) + "/p4app." + str(args.type) + ".json.template > " + AquaFlow_dir + "/p4app." + str(args.type) + ".json"
#print cmd_2
os.system(cmd_2)


print "Starting Experiment ..."
os.system("sudo ./run.sh " + str(args.type))
os.system("sudo chmod -R 777 " + str(AquaFlow_dir))



