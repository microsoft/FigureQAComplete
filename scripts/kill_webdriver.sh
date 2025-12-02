#!/bin/bash
ps aux | grep "[w]ebdriver=" | while read -r line; do
	linearr=($line)
	pid="${linearr[1]}"
	echo "Killing ${pid}"
	kill -9 $pid
done

