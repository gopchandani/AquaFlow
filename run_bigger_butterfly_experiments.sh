#!/bin/bash


OPTIND=1         

# Initialize our own variables:
i_face_1="h2-eth0"
i_face_2="h3-eth0"
i_face_3="h4-eth0"

n_packets=100
exp_type="bigger_butterfly"
bandwidth=0.05

while getopts "h?i:j:n" opt; do
    case "$opt" in
    h|\?)
        echo "./run_experiments.sh -i <Interface name for receive stream 1> -j <Interface name for receive stream 2> -k <Interface name for receive stream 3> -n <Number of packets to send> "
        exit 0
        ;;
    i)  i_face_1=$OPTARG
        ;;
    j)  i_face_2=$OPTARG
        ;;
    k)  i_face_3=$OPTARG
        ;;
    n)  n_packets=$OPTARG
        ;;
    esac
done

echo "Iface 1: " $i_face_1
echo "Iface 2: " $i_face_2
echo "Iface 3: " $i_face_3
echo "NPackets: " $n_packets
echo "Experiemt type: " $exp_type

for send_rate in 0.1 #0.01 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1
do
	for pkt_size in 4096
	do
		echo "Configuration of  next experiment ...."
		echo "Payload size = " $pkt_size

		sudo python experiments/experiment.py --iface1 $i_face_1 --iface2 $i_face_2 --iface3 $i_face_3 --npackets $n_packets --type $exp_type --payload $pkt_size --rate $send_rate --bw $bandwidth
        rm -rf experiments/pcaps/pcaps_bigger_butterfly_payload_${pkt_size}_send_rate_${send_rate}
        mkdir -p experiments/pcaps/pcaps_bigger_butterfly_payload_${pkt_size}_send_rate_${send_rate}
        cp build/*.pcap experiments/pcaps/pcaps_bigger_butterfly_payload_${pkt_size}_send_rate_${send_rate}
        sudo chmod -R 777 experiments/pcaps/pcaps_bigger_butterfly_payload_${pkt_size}_send_rate_${send_rate}
	done
done