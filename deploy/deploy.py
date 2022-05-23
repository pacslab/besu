import re
from redis import Redis
import subprocess
import toml
import socket
import time
import json
import sys
import os

if len(sys.argv) < 2:
    print('To few arguments; you need to specify 2 arguments.')
    print('Default values will be used. WATCHDOG ADDRESS is 192.168.23.64, NODE_COUNT is 5\n')
    WATCHDOG_ADDRESS = "192.168.23.64"
    NODE_COUNT = 5  # number of concurrent users sending request to the web server
else:
    print('Default values have been overwritten.')
    WATCHDOG_ADDRESS = sys.argv[1]
    NODE_COUNT = int(sys.argv[2])
# default consensus is ibft
CONSENSUS = "ibft"
if len(sys.argv) > 3:
    # options: clique, ibft
    CONSENSUS = sys.argv[3]

# time.sleep(5)
hostname = socket.gethostname()
# host_ip = socket.gethostbyname(socket.gethostname())
host_ip = subprocess.run(['ip', 'route', 'get', '192.168.23.64'], stdout=subprocess.PIPE)
host_ip = host_ip.stdout.decode().split(' ')
host_ip = host_ip[host_ip.index('src') + 1]

with open('config-template.toml', 'r') as f:
    config = toml.load(f)

config['identity'] = hostname
config['p2p-host'] = host_ip
config['rpc-http-host'] = host_ip
config['rpc-ws-host'] = host_ip
#config['metrics-push-host'] = host_ip

redis_miscellaneous = Redis(host=WATCHDOG_ADDRESS, port=6379, db=0)
redis_hosts = Redis(host=WATCHDOG_ADDRESS, port=6379, db=1)
redis_enode = Redis(host=WATCHDOG_ADDRESS, port=6379, db=2)
redis_deployment_logs = Redis(host=WATCHDOG_ADDRESS, port=6379, db=3)

redis_hosts.set(host_ip, json.dumps({'hostname': hostname}))

logs = []

try:
    is_master = redis_enode.setnx("master", host_ip)
    if is_master:
        # Node to provide enode URL
        with open('ibftConfigFile-template.json', 'r') as f:
            ibft_config = json.load(f)
        redis_enode.set("node_count", NODE_COUNT)
        ibft_config['blockchain']['nodes']['count'] = NODE_COUNT
        # Generate genesis and keys
        with open('ibftConfigFile.json', 'w') as f:
            json.dump(ibft_config, f)
        subprocess.run(['sh', 'create_artifacts.sh'])
        time.sleep(20 + NODE_COUNT * 0.2)
        # Push genesis to redis
        if CONSENSUS == "clique":
            pre = "0x0000000000000000000000000000000000000000000000000000000000000000"
            post = "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
            dirs = os.listdir('networkFiles/keys')
            nodeAddrs = ""
            for dir in dirs:
                if '0x' in dir:
                    nodeAddrs = nodeAddrs + dir[2:]
            with open('cliqueGenesis.json', 'r') as f:
                genesis = json.load(f)
                genesis['extraData'] = pre + nodeAddrs + post
        else:
            with open('networkFiles/genesis.json', 'r') as f:
                genesis = json.load(f)
        redis_enode.set("genesis", json.dumps(genesis))
        # Push keys to redis
        for dirname in os.listdir('networkFiles/keys'):
            with open(f"networkFiles/keys/{dirname}/key.pub", "r") as f:
                public_key = f.read()
            with open(f"networkFiles/keys/{dirname}/key", "r") as f:
                private_key = f.read()
            redis_enode.lpush('key_bucket',
                              json.dumps({'key': dirname, 'public_key': public_key, 'private_key': private_key}))
            redis_enode.lpush('key_store',
                              json.dumps({'key': dirname, 'public_key': public_key, 'private_key': private_key}))
        # Retrieve a key
        key = json.loads(redis_enode.lpop('key_bucket'))
        with open(f"data/key.pub", "w") as f:
            f.write(key['public_key'])
        with open(f"data/key", "w") as f:
            f.write(key['private_key'])
        redis_hosts.set(host_ip, json.dumps({'hostname': hostname, 'key': key['key']}))
        # Dump config.toml
        with open('config.toml', 'w') as f:
            toml.dump(config, f)
        # Dump genesis.json
        with open('genesis.json', 'w') as f:
            json.dump(genesis, f)
        # Deploy Besu
        subprocess.run(['sh', 'start.sh'], stdout=subprocess.PIPE)
        enode_url = []
        while len(enode_url) == 0:
            time.sleep(5)
            container_logs = subprocess.run(['docker', 'logs', hostname], stdout=subprocess.PIPE)
            container_logs = container_logs.stdout.decode()
            logs.append(container_logs)
            enode_url = re.findall(r"(enode?://[^\s]+)", container_logs)
        enode_url = enode_url[0]
        # ------
        # enode_url = enode_url.split('@')
        # enode_url[1] = f'@{host_ip}:30303'
        # enode_url = ''.join(enode_url)
        # -----
        # Set enode URL
        redis_enode.set("enode", enode_url)
    else:
        # node to retrieve enode URL
        time.sleep(15)
        # Retrieve enode URL
        enode_url = None
        while enode_url is None:
            enode_url = redis_enode.get("enode")
            time.sleep(5)
        enode_url = enode_url.decode()
        config['bootnodes'] = [enode_url]
        # Dump config.toml
        with open('config.toml', 'w') as f:
            toml.dump(config, f)
        genesis = json.loads(redis_enode.get('genesis'))
        # Dump genesis.json
        with open('genesis.json', 'w') as f:
            json.dump(genesis, f, indent=4)
        # Retrieve a key
        key = json.loads(redis_enode.lpop('key_bucket'))
        with open(f"data/key.pub", "w") as f:
            f.write(key['public_key'])
        with open(f"data/key", "w") as f:
            f.write(key['private_key'])
        redis_hosts.set(host_ip, json.dumps({'hostname': hostname, 'key': key['key']}))
        # Deploy Besu
        subprocess.run(['sh', 'start.sh'], stdout=subprocess.PIPE)
        time.sleep(15)
        container_logs = subprocess.run(['docker', 'logs', hostname], stdout=subprocess.PIPE)
        container_logs = container_logs.stdout.decode()
        logs.append(container_logs)
except Exception as e:
    logs.append(str(e))
redis_deployment_logs.set(host_ip, json.dumps(logs))
