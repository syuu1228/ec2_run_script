#!/bin/bash -e

REGION=us-east-1

ARCH=x86_64

if [[ -z "${TYPE}" ]]; then
    echo "TYPE is not set"
    exit 1
fi

SSH_USER=ubuntu
AMI_NAME='ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*'
AMI_OWNER=099720109477

random=$(ruby -e "print (0...16).map{ ('a'..'z').to_a[rand(26)] }.join")
workdir=$(mktemp -d)
sshkey=/home/syuu/KEYNAME.pem
keyname=KEYNAME
secgroup_id=SECGROUP
subnet_id=SUBNETID

REMOTE_SCRIPT=remote_script.py

image_id=$(aws ec2 describe-images --region $REGION \
                --filters "Name=name,Values=$AMI_NAME" "Name=architecture,Values=$ARCH" \
                --query 'reverse(sort_by(Images, &CreationDate))[0]' \
                --owners $AMI_OWNER \
                --output json | jq -r .ImageId)

if [ "${image_id}" = "null" ]; then
    echo "unable to get image_id"
    exit 1
fi

echo -n starting instance
instance_id=$(aws ec2 run-instances --image-id $image_id \
    --count 1 \
    --instance-type $TYPE \
    --key-name $keyname \
    --security-group-ids $secgroup_id \
    --subnet-id $subnet_id | jq -r .Instances[0].InstanceId)

if [ -z "$instance_id" ]; then
    echo "failed to run-instances"
    exit 1
fi

# wait for startup instance
for i in $(seq 1 60); do
    state=$(aws ec2 describe-instances --instance-id $instance_id \
        | jq -r .Reservations[0].Instances[0].State.Name)
    if [ x"$state" = x"running" ]; then
        break
    fi
    echo -n .
    sleep 10
done
if [ $i -eq 60 ]; then
    echo Failed to start instance.
    echo Please clean up accordingly:
    echo "aws ec2 terminate-instances --instance-ids $instance_id"
    exit 1
fi

echo done: $instance_id

for i in $(seq 1 3); do
    dns_name=$(aws ec2 describe-instances --instance-id $instance_id \
            | jq -r .Reservations[0].Instances[0].PublicDnsName)
    if [ -n "$dns_name" ]; then
        break
    fi
    sleep 10
done
if [ -z "$dns_name" ]; then
   dns_name=$(aws ec2 describe-instances --instance-id $instance_id \
            | jq -r .Reservations[0].Instances[0].PublicIpAddress)
    if [ "$dns_name" = "null" ]; then
        dns_name=""
        if [ -n "$dns_name" ]; then
            break
        fi
    fi
fi
if [ -z "$dns_name" ]; then
    echo "failed to retrive instance DNS name or public address"
    exit 1
fi

echo Connecting to $dns_name
# Retry to connect since sshd may not started yet
for i in $(seq 1 60); do
    ssh $SSH_USER@$dns_name \
        -i $sshkey \
        -o UserKnownHostsFile=/dev/null \
        -o StrictHostKeyChecking=no /bin/echo "connected." && break
    sleep 10
done

scp -i $sshkey \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no $REMOTE_SCRIPT $SSH_USER@$dns_name:~/
ssh $SSH_USER@$dns_name \
    -i $sshkey \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no bash -x -e /home/$SSH_USER/$REMOTE_SCRIPT
scp -i $sshkey \
    -o UserKnownHostsFile=/dev/null \
    -o StrictHostKeyChecking=no $SSH_USER@$dns_name:~/result.txt ./results/${SUFFIX}result.txt

status=$(aws ec2 terminate-instances --instance-ids $instance_id \
        | jq -r .TerminatingInstances[0].CurrentState.Name
    )
echo Exit request sent. current status: $status
