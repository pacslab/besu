#!/bin/bash
docker stop $(docker ps -q)

sleep 5

cd ~/bpet/deploy/
sudo rm -rf data/database

sleep 10

sh start.sh