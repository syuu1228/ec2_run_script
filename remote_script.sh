#!/bin/bash -e
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y wget
cd /etc/apt/sources.list.d/
sudo wget https://s3.amazonaws.com/downloads.scylladb.com/deb/ubuntu/scylla-6.2.list
cd -
sudo apt-get update --allow-insecure-repositories
sudo apt-get install --allow-unauthenticated -y scylla mdadm
sudo /opt/scylladb/scripts/scylla_raid_setup --disks /dev/nvme1n1 --enable-on-nextboot
sudo /opt/scylladb/scripts/scylla_io_setup
cp /etc/scylla.d/io_properties.yaml result.txt
