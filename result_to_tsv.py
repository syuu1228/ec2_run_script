#!/usr/bin/python

import io
import sys
import yaml
import statistics

print("instance_type	read_iops	read_bandwidth	write_iops	write_bandwidth")

sio = io.StringIO()
for t in sys.argv[1:]:
    read_iops_list = []
    read_bandwidth_list = []
    write_iops_list = []
    write_bandwidth_list = []
    for i in range(3):
        with open(f'results/{t}.{i}.result.txt') as f:
            result = yaml.safe_load(f.read())
        read_iops = result['disks'][0]['read_iops']
        read_iops_list.append(read_iops)
        read_bandwidth = result['disks'][0]['read_bandwidth']
        read_bandwidth_list.append(read_bandwidth)
        write_iops = result['disks'][0]['write_iops']
        write_iops_list.append(write_iops)
        write_bandwidth = result['disks'][0]['write_bandwidth']
        write_bandwidth_list.append(write_bandwidth)
        print(f'{t}.{i}	{read_iops}	{read_bandwidth}	{write_iops}	{write_bandwidth}')
    read_iops_avg = int(statistics.mean(read_iops_list))
    read_bandwidth_avg = int(statistics.mean(read_bandwidth_list))
    write_iops_avg = int(statistics.mean(write_iops_list))
    write_bandwidth_avg = int(statistics.mean(write_bandwidth_list))
    sio.write(f'{t}	{read_iops_avg}	{read_bandwidth_avg}	{write_iops_avg}	{write_bandwidth_avg}\n')
print()
print(sio.getvalue())
