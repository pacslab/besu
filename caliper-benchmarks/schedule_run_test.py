import os
import time
import subprocess

def run():
    working_directory = '/mnt/bpet/caliper-benchmarks'
    err = ''
    out = ''
    
    command = ['python3.9', 'run_test.py', '192.168.226.10']
    try:
        print("running...")
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory)
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
    with open(os.path.join(working_directory, 'benchmark.log'), 'w') as f:
        f.write(msg)

while True:
    os.system("docker rm $(docker ps -aq) --force")
    run()
    time.sleep(30)
