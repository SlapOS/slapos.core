import json
import os

from slapos.util import dumps
from slapos.format import Partition


COMPUTER_ID = 'COMP-4545'
INSTANCE_ROOT = '/srv/slapgrid'
RESOURCE = Partition.resource_file
BOUTURE = 'bouture.json'
SLAPPART_BASE = 'slappart'


candidates = []
for p in os.listdir(INSTANCE_ROOT):
    if p.startswith(SLAPPART_BASE):
        try:
            int(p[len(SLAPPART_BASE):])
        except ValueError:
            continue
        # p is a partition :)
        if os.path.exists(os.path.join(INSTANCE_ROOT, p, BOUTURE)):
            candidates.append(p)

partition_id, = candidates
assert partition_id == 'slappart5'
# XXX: bouturing multiple partitions will require partition capabilities


with open(os.path.join(INSTANCE_ROOT, partition_id, BOUTURE)) as f:
    bouture = json.load(f)

software_url = bouture['software-url']
software_type = bouture['software-type']
instance_name = bouture['instance-title']
parameter_dict = bouture['config']
state = bouture['instance-state']


with open(os.path.join(INSTANCE_ROOT, partition_id, RESOURCE)) as f:
    resource = json.load(f)

address_list = resource['address_list']
tap = resource['tap']
partition_list = [
    {'reference': partition_id, 'address_list': address_list, 'tap': tap}
]
computer_dict = dict(reference=COMPUTER_ID, address=None, netmask=None)
computer_dict['partition_list'] = partition_list
slap.registerComputer(COMPUTER_ID).updateConfiguration(dumps(computer_dict))

supply(software_url, COMPUTER_ID)

request(software_url, instance_name, parameter_dict, software_type, state=state)

# /etc/opt/slapos/slapos.cfg
"""
[slapproxy]
host = 127.0.0.1
port = 4000
database_uri = /etc/opt/slapos/slapproxy.db
"""

# /etc/opt/slapos/slapproxy-client.cfg
"""
[slapos]
master_url = http://127.0.0.1:4000
"""

# slapos console --cfg /etc/opt/slapos/slapproxy-client.cfg bouture.py

# slapos node instance --master-url http://127.0.0.1:4000 --certificate_repository_path /etc/opt/slapos/slapproxy-ssl/
