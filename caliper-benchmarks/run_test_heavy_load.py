import yaml, subprocess, os, json, sys, re
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import dotenv_values
import openstack
import time

env = dotenv_values("cc.env")

# install docker-compose:
# sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
# sudo chmod +x /usr/local/bin/docker-compose
# python3 -m pip install PyYAML pandas python-dotenv openstacksdk
# cd bpet; mkdir data; cd caliper-benchmarks; mkdir reports 
# scp cc.env to bpet/caliper-benchmarks; scp bpet/data/rrg-bpet to bpet/data/: 
# run test
def create_connection():
    return openstack.connect(
        auth_url=env['OS_AUTH_URL'],
        project_name=env['OS_PROJECT_NAME'],
        username=env['OS_USERNAME'],
        password=env['OS_PASSWORD'],
        region_name=env['OS_REGION_NAME'],
        user_domain_name=env['OS_USER_DOMAIN_NAME'],
        project_domain_name=env['OS_PROJECT_DOMAIN_NAME'],
        project_id=env['OS_PROJECT_ID'],
        app_name='bpet',
        app_version='1.0',
    )

def collect_info():
    conn = create_connection()
    rows = []
    for server in conn.compute.servers():
        if(re.match(r'besu-\d+', server.name)):
            row = []
            NodeName = server.name
            IP = server.addresses['rrg-khazaei-network'][0]['addr']
            instance_id = conn.compute.find_server(NodeName).id
            host_id = conn.compute.get_server(instance_id).host_id

            row.append(NodeName)
            row.append(IP)
            row.append(instance_id)
            row.append(host_id)

            rows.append(row)
    df = pd.DataFrame(np.array(rows),
        columns=['NodeName', 'IP', 'InstanceID', 'HostID'])
    # sort dataframe
    df['Index'] = [int(name.split('-')[1]) for name in df.NodeName]
    df = df.set_index(keys=df.Index).drop(labels='Index', axis=1).sort_index()
    print(df)
    with open('nodeinfo.json', 'w') as f:
        json.dump({'nodeinfo': rows}, f, indent=4)
    return df

def setup_monitors(df):
    benchconfig = 'benchmarks/scenario/simple/config.yaml'
    with open(benchconfig,'r') as f:
        y=yaml.safe_load(f)
        y['monitors']['resource'][0]['options']['containers'] = []
        for _, row in df.iterrows():
            container = 'http://' + row.IP +':2375/' + row.NodeName
            y['monitors']['resource'][0]['options']['containers'].append(container)
    with open(benchconfig, 'w') as f:
        yaml.dump(y, f, default_flow_style=False, sort_keys=False, indent=4)

def run(SEND_RATES, RPC_IP):
    connection_url = "ws://" + RPC_IP + ":8546"
    networkconfig = './networks/ibft2/networkconfig.json'
    benchconfig = './benchmarks/scenario/simple/config.yaml'

    with open(networkconfig, 'r') as f:
        data = json.load(f)
        data['ethereum']['url'] = connection_url
    with open(networkconfig, 'w') as f:
        json.dump(data, f, indent=4)

    timestampStr = datetime.now().strftime("%Y%m%d-%H%M%S")
    directory = 'reports/' + timestampStr
    path = os.path.join(os.getcwd(), directory)
    
    os.mkdir(path)

    replicas = 25
    rounds = 3 # test rounds: open, query and transfer
    for tps in SEND_RATES:
        with open(benchconfig,'r') as f:
            y=yaml.safe_load(f)
            for i in range(rounds):
                y['test']['rounds'][i]['rateControl']['opts']['tps'] = tps
        with open(benchconfig,'w') as f:
            yaml.dump(y,f,default_flow_style=False, sort_keys=False, indent=4)

        for i in range(replicas):
            subprocess.run(['docker-compose', 'up'])
            subprocess.run(['mv', 'report.html', '{}/report-{}-{}.html'.format(directory, tps, i+1)])
            subprocess.run(['sleep', '10'])

def collect_log(df, key, since):
    print('Starting to collect logs on each node:')
    for _, row in df.iterrows():
        COMMAND = 'docker logs --since {} {} > {}.log'.format(since, row['NodeName'], row['NodeName'])
        subprocess.Popen(["ssh", "-i", key, 
                        "-o", "StrictHostKeyChecking=no", "ubuntu@%s" % row['IP'], COMMAND],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

    subprocess.run(['sleep', '10'])
    
    timestampStr = datetime.now().strftime("%Y%m%d-%H%M%S")
    directory = '../data/logs-' + timestampStr
    log_path = os.path.join(os.getcwd(), directory)
    os.mkdir(log_path)
    # collect besu logs
    for _, row in df.iterrows():
        subprocess.run(['scp', '-i', key, "-o", "StrictHostKeyChecking=no", 
        "ubuntu@{}:/home/ubuntu/{}.log".format(row['IP'], row.NodeName), log_path])
    # collect caliper logs
    subprocess.run(['mv', 'caliper.log', log_path])
    # collect node info json data
    subprocess.run(['cp', 'nodeinfo.json', log_path])


if __name__ == "__main__":
    watchdogAddress = "192.168.226.176"
    # watchdogAddress = "10.2.1.9"
    keyFile = "../data/rrg-bpet"
    # keyFile = "../data/bpet.pem"
    current_directory = os.getcwd()
    sshKey = os.path.join(current_directory, keyFile)
    # send rates range from 1100 to 10000 in 100 increments
    sendRates = list([i for i in range(1100, 10100, 100)])
    # collect network info
    df = collect_info()
    # set up monitors in caliper benchmark config
    setup_monitors(df)
    # run test
    rpcIP = df.IP.values[0]
    if len(sys.argv) > 1:
        rpcIP = sys.argv[1]
    # run test
    startTime = datetime.now().isoformat('T') + 'Z'
    run(SEND_RATES=sendRates, RPC_IP=rpcIP)
    # collect logs
    collect_log(df, sshKey, startTime)
