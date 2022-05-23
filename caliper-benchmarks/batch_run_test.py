import os
import time
import subprocess
from redis import Redis
import shutil

watchdog_address="192.168.226.176"

working_directory = '/mnt/bpet/'
expierment_results_working_directry = '/mnt/experiments_bpet'
caliper_working_directory = os.path.join(working_directory, 'caliper-benchmarks')


network_sizes = [4, 6, 10, 12, 14, 16]
instance_flavors = ['c4-15gb-144', 'c8-30gb-288', 'c16-60gb-576', 'c1-7.5gb-36', 'c4-30gb-144']



def run():
    err = ''
    out = ''
    
    command = ['python3.9', 'run_test.py', '192.168.226.10']
    try:
        print("running...")
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=caliper_working_directory)
        o, e = proc.communicate(timeout=4200)
        out += o.decode('utf8') + '\n'
        err += e.decode('utf8') + '\n'
    except Exception as e:
        proc.kill()
        o, er = proc.communicate()
        out += o.decode('utf8') + '\n'
        err += er.decode('utf8') + '\n'
        err += str(e) + '\n'
    msg = out + err
    with open(os.path.join(caliper_working_directory, 'benchmark.log'), 'w') as f:
        f.write(msg)


if __name__ == "__main__":
    deploy_working_directory = os.path.join(working_directory, 'deploy')
    # horizontal scalability
    for size in network_sizes:
        flavor = 'c2-7.5gb-36'
        consensus = 'QBFT'
        block_time = '1S'
        flavor_name = flavor.split('-')[:2]
        flavor_name = flavor_name[0][1:] + 'C' + flavor_name[1][:-1].upper()
        task_name = f"{size}_LB_{flavor_name}_{consensus}_{block_time}"
        print(task_name)
        # create instances
        command = ['python3.9', 'create_instances.py', str(size), flavor]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=deploy_working_directory)
        time.sleep(size * 10)
        # retrieve IP addresses
        logs_db = Redis(host=watchdog_address, port=6379, db=3)
        while True:
            ip_list = logs_db.keys()
            if len(ip_list) != size:
                time.sleep(5)
                continue
            break
        ip_list = [ip.decode() for ip in ip_list]
        # prepare NGINX config
        lb_working_directory = os.path.join(working_directory, 'load-balancing')
        with open(os.path.join(lb_working_directory, 'bpet-base'), 'r') as f:
            nginx_config = f.read()
        upstream_servers = [f"    server {ip}:8546;" for ip in ip_list]
        upstream_servers = '\n'.join(upstream_servers)
        nginx_config = nginx_config.replace('# upstream servers', upstream_servers)
        with open(os.path.join(lb_working_directory, 'bpet'), 'w') as f:
            f.write(nginx_config)
        # update NGINX config
        # set no password rules in /etc/sudoers.d (not necessary for cloud images)
        command = ['sudo', 'cp', 'bpet', '/etc/nginx/sites-enabled/bpet']
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=lb_working_directory)
        # restart NGINX
        command = ['sudo', 'service', 'nginx', 'restart']
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=lb_working_directory)
        # remove the reports directory if exists and create a new reports directory
        submissions_path = os.path.join(working_directory, 'submissions')
        if os.path.exists(os.path.join(caliper_working_directory, 'reports')):
            shutil.rmtree(os.path.join(caliper_working_directory, 'reports'))
        os.mkdir(os.path.join(caliper_working_directory, 'reports'))
        # run 5 rounds
        for _ in range(5):
            os.system("docker rm $(docker ps -aq) --force")
            run()
            time.sleep(30)
        # move the reports directory into the experiment results directory
        command = ['mv', 'reports', os.path.join(expierment_results_working_directry, 'reports', task_name)]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=caliper_working_directory)
    # vertical scalability
    for flavor in instance_flavors:
        size = 8
        consensus = 'QBFT'
        block_time = '1S'
        flavor_name = flavor.split('-')[:2]
        flavor_name = flavor_name[0][1:] + 'C' + flavor_name[1][:-1].upper()
        task_name = f"{size}_LB_{flavor_name}_{consensus}_{block_time}"
        print(task_name)
        # create instances
        command = ['python3.9', 'create_instances.py', str(size), flavor]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=deploy_working_directory)
        time.sleep(size * 10)
        # retrieve IP addresses
        logs_db = Redis(host=watchdog_address, port=6379, db=3)
        while True:
            ip_list = logs_db.keys()
            if len(ip_list) != size:
                time.sleep(5)
                continue
            break
        ip_list = [ip.decode() for ip in ip_list]
        # prepare NGINX config
        lb_working_directory = os.path.join(working_directory, 'load-balancing')
        with open(os.path.join(lb_working_directory, 'bpet-base'), 'r') as f:
            nginx_config = f.read()
        upstream_servers = [f"    server {ip}:8546;" for ip in ip_list]
        upstream_servers = '\n'.join(upstream_servers)
        nginx_config = nginx_config.replace('# upstream servers', upstream_servers)
        with open(os.path.join(lb_working_directory, 'bpet'), 'w') as f:
            f.write(nginx_config)
        # update NGINX config
        # set no password rules in /etc/sudoers.d (not necessary for cloud images)
        command = ['sudo', 'cp', 'bpet', '/etc/nginx/sites-enabled/bpet']
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=lb_working_directory)
        # restart NGINX
        command = ['sudo', 'service', 'nginx', 'restart']
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=lb_working_directory)
        # remove the reports directory if exists and create a new reports directory
        submissions_path = os.path.join(working_directory, 'submissions')
        if os.path.exists(os.path.join(caliper_working_directory, 'reports')):
            shutil.rmtree(os.path.join(caliper_working_directory, 'reports'))
        os.mkdir(os.path.join(caliper_working_directory, 'reports'))
        # run 5 rounds
        for _ in range(5):
            os.system("docker rm $(docker ps -aq) --force")
            run()
            time.sleep(30)
        # move the reports directory into the experiment results directory
        command = ['mv', 'reports', os.path.join(expierment_results_working_directry, 'reports', task_name)]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=caliper_working_directory)


while True:
    os.system("docker rm $(docker ps -aq) --force")
    run()
    time.sleep(30)
