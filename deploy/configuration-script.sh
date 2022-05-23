#!/bin/bash
rm /etc/machine-id
systemd-machine-id-setup
systemd-resolve --flush-caches
cd /home/ubuntu || exit

# enable docker remote API by appending -H= to the ExecStart line
sudo sed -i '/ExecStart/s/$/ -H=tcp:\/\/0.0.0.0:2375/' /lib/systemd/system/docker.service
sudo systemctl daemon-reload
sudo service docker restart

sudo apt install iftop

sudo apt update -y
sudo apt install ntpdate -y
# add the NTP server’s IP address and hostname in the /etc/hosts file
echo '192.168.226.176	  watchdog' | sudo tee -a /etc/hosts
sudo timedatectl set-ntp off
# install NTP service on the client system
sudo apt install ntp -y
# Configure NTP Client
echo 'server watchdog prefer iburst' | sudo tee -a /etc/ntp.conf
sudo systemctl restart ntp

sudo -H -u ubuntu bash -c 'git clone XXX.git'
cd bpet/deploy || exit
sudo -H -u ubuntu bash -c 'python3 deploy.py 192.168.226.176 8'
