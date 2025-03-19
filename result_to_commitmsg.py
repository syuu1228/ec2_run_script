#!/usr/bin/python

import io
import sys
import yaml

for t in sys.argv[1:]:
    for i in range(3):
        with open(f'results/{t}.{i}.log') as f:
            log = f.readlines()
        matched = None
        print(f'- {t} ({i}/3)')
        for j in range(0, len(log)):
            if log[j] == 'Starting Evaluation. This may take a while...\n':
                matched = j
            # iotune output is 6 lines
            if matched is not None and j < matched + 6:
                print(log[j], end='')
        print()
