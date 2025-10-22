import argparse
import errno
import json
import logging
import os
import subprocess

import slapos.slap.slap
from slapos.util import dumps
from slapos.format import Partition

from slapos.grid.slapgrid import SLAPGRID_SUCCESS, SLAPGRID_OFFLINE_SUCCESS
from slapos.grid.utils import setRunning, setFinished

from six.moves import configparser


RESOURCE_FILE = Partition.resource_file
BOUTURE_FILE = 'bouture.json'


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bouture')


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
    cp = slap.registerOpenOrder().request(
        software_url,
        instance_name,
        parameter_dict,
        software_type,
        state=state,
    )
    # Bang the boutured instance to ensure it will be reprocessed
    # It must be reprocessed because the master changed, so the promises need
    # to be reconfigured to bang the new master, and possibly some parameters
    # changed as well, depending on the bouture file.
    cp.bang()


def parse_conf(cfg):
    configp = configparser.ConfigParser()
    if configp.read(cfg) != [cfg]:
       raise Exception("Could not read %s" % cfg)
    node_conf = {}
    for section in ("slapformat", "slapos"):
      node_conf.update(configp.items(section))
    return argparse.Namespace(**node_conf)


def failover():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node-cfg', required=True)
    parser.add_argument('--new-master-url', required=True)
    parser.add_argument('--new-cert-dir', required=True)
    parser.add_argument('--pidfile', required=True)
    parser.add_argument('--switchfile', required=True)
    args = parser.parse_args()

    setRunning(logger, args.pidfile)
    try:
        cfg = args.node_cfg
        node_conf = parse_conf(cfg)

        ret = subprocess.call(('slapos', 'node', 'instance', '--cfg', cfg))
        if ret == SLAPGRID_OFFLINE_SUCCESS:
            logger.info(
                "This node is unable to reach its SlapOS master"
            )
            try:
                os.remove(args.switchfile)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            else:
                logger.info(
                    "Bouturing this node onto alternate master at %s",
                    args.new_master_url,
                )
                bouture(args, node_conf)
            logger.info(
                "Processing this node from alternate master at %s",
                args.new_master_url,
            )
            subprocess.call((
                'slapos', 'node', 'instance',
                '--cfg', cfg,
                '--master-url', args.new_master_url,
                '--certificate_repository_path', args.new_cert_dir,
            ))
        else:
            # If ret != 0, likely SlapOS master is reachable and some
            # promise or buildout is failing. If SlapOS master is not
            # reachable then it's offline processing that failed, and
            # that means there is a bug in slapos node instance or an
            # error in starting instance services, and things are bad
            # anyway.
            logger.info(
                "This node seems able to reach its SlapOS master: "
                "slapos node instance returned %d",
                ret,
            )
            with open(args.switchfile, 'w'):
                pass

    finally:
        setFinished(args.pidfile)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node-cfg', required=True)
    parser.add_argument('--new-master-url', required=True)
    args = parser.parse_args()
    node_conf = parse_conf(args.node_cfg)
    bouture(args, node_conf)


if __name__ == '__main__':
    failover()


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
