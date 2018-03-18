#!/bin/bash

OPTIND=1         

# Initialize our own variables:
i_face="h2-eth0"
n_packets=1000
exp_type="diversity"

while getopts "h?i:n:t:" opt; do
    case "$opt" in
    h|\?)
        echo "./run_experiments.sh -i <Interface name for receive stream> -n <Number of packets to send> -t <Experiment type: diversity or butterfly>"
        exit 0
        ;;
    i)  i_face=$OPTARG
        ;;
    n)  n_packets=$OPTARG
        ;;
    esac
done

echo "Iface: " $i_face
echo "NPackets: " $n_packets
echo "Experiemt type: " $exp_type

for diff in -5 -1 0 1 5
do
	for pkt_size in 128 1024 2048 4096
	do
		echo "Configuration of  next experiment ...."
		echo "Differential = " $diff
		echo "Payload size = " $pkt_size

		sudo python experiments/experiment.py --differential $diff --iface $i_face --npackets $n_packets --type $exp_type --payload $pkt_size

	done
done