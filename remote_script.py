#!/usr/bin/python3

import os
import re
import glob
from subprocess import run

def out(cmd, shell=True, timeout=None, encoding='utf-8', ignore_error=False, user=None, group=None):
    res = run(cmd, capture_output=True, shell=shell, timeout=timeout, check=False, encoding=encoding, user=user, group=group)
    if not ignore_error and res.returncode != 0:
        print(f'Command \'{cmd}\' returned non-zero exit status: {res.returncode}')
        print('----------  stdout  ----------')
        print(res.stdout, end='')
        print('------------------------------')
        print('----------  stderr  ----------')
        print(res.stderr, end='')
        print('------------------------------')
        res.check_returncode()
    return res.stdout.strip()

SYSTEM_PARTITION_UUIDS = [
        '21686148-6449-6e6f-744e-656564454649', # BIOS boot partition
        'c12a7328-f81f-11d2-ba4b-00a0c93ec93b', # EFI system partition
        '024dee41-33e7-11d3-9d69-0008c781f39f'  # MBR partition scheme
]

def get_partition_uuid(dev):
    return out(f'lsblk -n -oPARTTYPE {dev}')

def is_system_partition(dev):
    uuid = get_partition_uuid(dev)
    return (uuid in SYSTEM_PARTITION_UUIDS)

def is_unused_disk(dev):
    # resolve symlink to real path
    dev = os.path.realpath(dev)
    # dev is not in /sys/class/block/, like /dev/nvme[0-9]+
    if not os.path.isdir('/sys/class/block/{dev}'.format(dev=dev.replace('/dev/', ''))):
        return False
    try:
        fd = os.open(dev, os.O_EXCL)
        os.close(fd)
        # dev is not reserved for system
        return not is_system_partition(dev)
    except OSError:
        return False


def list_block_devices():
    devices = []
    s = out('lsblk --help')
    if re.search(r'\s*-p', s, flags=re.MULTILINE):
        s = out('lsblk -pnr')
        res = re.findall(r'^(\S+) \S+ \S+ \S+ \S+ (\S+)', s, flags=re.MULTILINE)
        for r in res:
            if r[1] != 'rom' and r[1] != 'loop':
                devices.append(r[0])
    else:
        for p in ['/dev/sd*', '/dev/hd*', '/dev/xvd*', '/dev/vd*', '/dev/nvme*', '/dev/mapper/*']:
            devices.extend([d for d in glob.glob(p) if d != '/dev/mapper/control'])
    return devices

def get_unused_disks():
    unused = []
    for dev in list_block_devices():
        # dev contains partitions
        if len(glob.glob('/sys/class/block/{dev}/{dev}*'.format(dev=dev.replace('/dev/','')))) > 0:
            continue
        # dev is used
        if not is_unused_disk(dev):
            continue
        unused.append(dev)
    return unused

if __name__ == '__main__':
    scylla_list = 'https://s3.amazonaws.com/downloads.scylladb.com/deb/ubuntu/scylla-2025.1.list'
    unused_disks = get_unused_disks()
    apt_env = os.environ.copy()
    apt_env['DEBIAN_FRONTEND'] = 'noninteractive'
    run('apt-get update', shell=True, check=True, env=apt_env)
    run('apt-get -o DPkg::Lock::Timeout=300 upgrade -y', shell=True, check=True, env=apt_env)
    run('apt-get -o DPkg::Lock::Timeout=300 install -y curl', shell=True, check=True, env=apt_env)
    run(f'curl --output-dir /etc/apt/sources.list.d -L -O {scylla_list}', shell=True, check=True)
    run('apt-get update --allow-insecure-repositories', shell=True, check=True, env=apt_env)
    run('apt-get install --allow-unauthenticated -y scylla mdadm', shell=True, check=True, env=apt_env)
    run(f'/opt/scylladb/scripts/scylla_raid_setup --disks {unused_disks[0]} --enable-on-nextboot', shell=True, check=True)
    run('/opt/scylladb/scripts/scylla_io_setup', shell=True, check=True)
    run('cp /etc/scylla.d/io_properties.yaml result.txt', shell=True, check=True)
