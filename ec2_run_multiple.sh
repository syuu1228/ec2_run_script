#!/bin/bash

for t in "$@"; do
    for i in 0 1 2; do
        TYPE=$t SUFFIX=$t.$i. bash -x -e ./ec2_run_script.sh | tee results/$t.$i.log 2>&1
        sleep 10
    done
done
wait
./result_to_tsv.py "$@"
