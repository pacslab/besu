import re, base64, sys
from time import sleep, time
import openstack
from redis import Redis
from dotenv import dotenv_values
env = dotenv_values("../caliper-benchmarks/cc.env")

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

def create_instance(conn, instance_name, user_data, flavor_name):
    print("Creating instance ", instance_name)
    flavor = conn.compute.find_flavor(flavor_name)
    image = conn.compute.find_image("besu-base")
    network = conn.network.find_network("default-network")
    security_group = conn.network.find_security_group("open")
    key = conn.compute.find_keypair("bpet")
    conn.compute.create_server(name=instance_name, 
                        flavor_id=flavor.id, 
                        image_id=image.id, 
                        networks=[{"uuid": network.id}], 
                        security_groups=[{'name': security_group.name}], 
                        key_name=key.name,
                        user_data=user_data)

def flush_redis(watchdog_addr):
        hosts = Redis(host=watchdog_addr, port=6379, db=1)
        hosts.flushdb()
        enode = Redis(host=watchdog_addr, port=6379, db=2)
        enode.flushdb()
        logs = Redis(host=watchdog_addr, port=6379, db=3)
        logs.flushdb()

def deploy(network_size, flavor_name, watchdog_address):
    conn = create_connection()
    for server in conn.compute.servers():
        if(re.match(r'besu-\d+', server.name)):
            # print("Please delete all current besu nodes, then deploy a new network!")
            # return
            print("Deleting instance ", server.name)
            conn.compute.delete_server(server, force=True)
    sleep(30)
    print("Flushing redis dbs...")
    flush_redis(watchdog_address)
    # update post creation scripts
    with open('configuration-script.sh') as f:
        post_creation_command = f.read()
        new_command = post_creation_command[:-3] + str(network_size) + post_creation_command[-2:]
    user_data = base64.b64encode(new_command.encode("utf-8")).decode('utf-8')
    
    for id in range(network_size):
        instance_name = 'besu-'+str(id+1)
        create_instance(conn=conn, instance_name=instance_name, user_data=user_data, flavor_name=flavor_name)


if __name__ == "__main__":
    # network_size options: 4,6,8,10,12,14,16
    network_size = 8
    # flavor options: c2-7.5gb-36, c4-15gb-144, c8-30gb-288, c16-60gb-576
    flavor_name = "c2-7.5gb-36"
    watchdog_address="192.168.226.176"

    if len(sys.argv) < 2:
        print('Baseline confiuggurations will be used: N={}, flavor={}'.format(network_size, flavor_name))
    else:
        network_size = int(sys.argv[1])
        if len(sys.argv) > 2:
            flavor_name = sys.argv[2]
        print('Default values have been overwritten: N={}, flavor={}'.format(network_size, flavor_name))

    deploy(network_size, flavor_name, watchdog_address)
