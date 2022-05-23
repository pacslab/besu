import ast, redis, json

# connect Redis databases
WATCHDOG_ADDRESS = "127.0.0.1"
db1 = redis.StrictRedis(
    host=WATCHDOG_ADDRESS,
    port=6379,
    db=1)
db1_keys = db1.keys()

db2 = redis.StrictRedis(
    host=WATCHDOG_ADDRESS,
    port=6379,
    db=2)
db2_keys = db2.keys()
genesis = ast.literal_eval(db2.get(b'genesis').decode('utf-8'))

# construct dataframe
rows = []
for key in db1_keys:
    row = []
    # IP address of node
    ip = key.decode("utf-8")
    # check if node is validator
    value = ast.literal_eval(db1.get(key).decode('utf-8'))
    is_validator = value['key'][2:] in genesis['extraData']
    row.append(value['hostname'])
    row.append(ip)
    row.append(value['key'])
    row.append(is_validator)  
    rows.append(row)
with open('nodeinfo.json', 'w') as f:
    json.dump({'nodeinfo': rows}, f, indent=4)