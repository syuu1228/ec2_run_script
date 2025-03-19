#!/usr/bin/python3
import sys
import csv
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--tsv-file')
args = parser.parse_args()


with open(args.tsv_file) as f:
    csvreader = csv.reader(f, delimiter='\t')
    for row in csvreader:
        if not row or row[0] == 'instance_type' or row[0] == '' or re.match(r'.+\.[0-9]+$', row[0]):
            continue
        print(f'{row[0]}:')
        print(f'  read_iops: {row[1]}')
        print(f'  read_bandwidth: {row[2]}')
        print(f'  write_iops: {row[3]}')
        print(f'  write_bandwidth: {row[4]}')
