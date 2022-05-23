#!/bin/bash
cd /home/ubuntu || exit
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu
docker pull hyperledger/besu:21.10
sudo -H -u ubuntu bash -c 'curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py'
sudo -H -u ubuntu bash -c 'python3 get-pip.py'
sudo -H -u ubuntu bash -c 'pip3 install redis'
sudo -H -u ubuntu bash -c 'pip3 install toml'
