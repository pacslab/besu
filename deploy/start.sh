#!/bin/bash
docker stop $(docker ps -q)
sleep 5
export HOSTNAME=$(hostname)
docker run -d --rm \
    --name $HOSTNAME \
    --net host \
    -v ${PWD}/data:/opt/besu/data \
    -v ${PWD}/genesis.json:/config/genesis.json \
    -v ${PWD}/config.toml:/config/config.toml \
    hyperledger/besu:22.4 \
    --config-file=/config/config.toml
# -e BESU_OPTS='-XX:MaxRAMPercentagevfcx=80.0 -XshowSettings:vm' \

sleep 3

docker run --rm -d \
    --name pushgateway \
    -p 9091:9091 \
    prom/pushgateway