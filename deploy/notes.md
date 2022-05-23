# WATCHDOG_ADDRESS
192.168.23.64

# Redis
## Deployment
```
docker run -d -v /opt/besu/redis-data:/data --name besu-redis --restart=always -p 6379:6379 redis:6.2.5

docker run -d --rm -it -e REDIS_1_HOST=172.17.0.1 -e REDIS_1_NAME=besu-redis -p 18001:80 erikdubbelboer/phpredisadmin
```
## Access
```
sudo apt install python3-pip
python3 -m pip install redis
```
## Schema
* DB0 - miscellaneous
* DB1 - hosts
  * ip: {hostname: str, public_key: str, private_key:}
* DB2 - enode
  * master: ip
  * enode: url
  * genesis: str
  * node_count: int
  * key_bucket: list (for distribution)
  * key_store: list (for persistent storage)
* DB3 - deployment logs
  * ip: logs