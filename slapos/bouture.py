import json
import os

import slapos.slap.slap
from slapos.util import dumps
from slapos.format import Partition


RESOURCE_FILE = Partition.resource_file
BOUTURE_FILE = 'bouture.json'


def find_bouture_partitions(instance_root, slappart_base):
    bouture_partitions = []
    for p in os.listdir(instance_root):
        if p.startswith(slappart_base) and p[len(slappart_base):].isdigit():
            # p is a partition :)
            if os.path.exists(os.path.join(instance_root, p, BOUTURE_FILE)):
                bouture_partitions.append(p)
    return bouture_partitions


def bouture(bouture_conf, node_conf):
    # Node configuration
    computer_id = node_conf.computer_id
    instance_root = node_conf.instance_root
    slappart_base = node_conf.partition_base_name

    # Bouture configuration
    new_master_url = bouture_conf.new_master_url

    # Find bouture partition
    partitions = find_bouture_partitions(instance_root, slappart_base)
    if not partitions:
        return
    try:
        partition_id, = partitions
    except ValueError: # len(partitions) > 1
        # Note: bouturing multiple instances will require requesting each
        # instance into the correct partition in the new master: this can
        # be achieved with partition capabilities.
        raise Exception(
            "Only one bouture partition is currently supported;"
            "\nfound %r" % partitions
        )
    assert partition_id == 'slappart5' # tmp

    # Load instance information for bouture
    with open(os.path.join(instance_root, partition_id, BOUTURE_FILE)) as f:
        bouture = json.load(f)

    software_url = bouture['software-url']
    software_type = bouture['software-type']
    instance_name = bouture['instance-title']
    parameter_dict = bouture['config']
    state = bouture['instance-state']

    # Load partition IPs information
    with open(os.path.join(instance_root, partition_id, RESOURCE_FILE)) as f:
        resource = json.load(f)

    partition_list = [{
        'reference': partition_id,
        'address_list': resource['address_list'],
        'tap': resource['tap'],
    }]
    computer_dict = dict(
        reference=computer_id,
        address=None,
        netmask=None,
        partition_list=partition_list,
    )

    # Connect to new master
    slap = slapos.slap.slap()
    slap.initializeConnection(
        new_master_url,
        key_file=None, # for now
        cert_file=None, # for now
        slapgrid_rest_uri=None, # for now
    )
    # Register bouture partition
    slap.registerComputer(computer_id).updateConfiguration(dumps(computer_dict))
    # Supply bouture SR
    slap.registerSupply().supply(software_url, computer_id)
    # Request bouture instance
    slap.registerOpenOrder().request(
        software_url,
        instance_name,
        parameter_dict,
        software_type,
        state=state,
    )


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
