#!/bin/bash


OPTIND=1         

# Initialize our own variables:
i_face_1="h2-eth0"
i_face_2="h3-eth0"
n_packets=100
exp_type="butterfly_forwarding"

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

for diff in 0
do
	for pkt_size in 4096
	do
		echo "Configuration of  next experiment ...."
		echo "Payload size = " $pkt_size

		sudo python experiments/experiment.py --iface1 $i_face_1 --iface2 $i_face_2 --npackets $n_packets --type $exp_type --payload $pkt_size

	done
done