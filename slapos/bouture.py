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

# XXX https://lab.nexedi.com/nexedi/slapos.core/-/merge_requests/824
from slapos.grid.slapgrid import COMPUTER_PARTITION_TIMESTAMP_FILENAME


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
    new_monitor_url = bouture_conf.new_monitor_url

    logger.info(
        "Bouturing this node onto alternate master at %s",
        new_master_url,
    )

    # Find bouture partition
    partitions = find_bouture_partitions(instance_root, slappart_base)
    if not partitions:
        logger.info(
            "No bouture partitions found on this node"
        )
        return

    # Prepare computer information.
    # Note: bouturing multiple instances will require requesting each
    # instance into the correct partition in the new master. This can
    # be achieved with partition capabilities when the are supported.
    # Hack: for now a hack is employed: register the first partition,
    # request the first instance, register the 2nd partition, request
    # request the 2nd instance, etc.
    partition_list = []
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

    # Empty preexisting partitions
    # XXX: this does not remove the content of the slave table
    # (but it does empty the shared partition list in the partition table)
    slap.registerComputer(computer_id).updateConfiguration(dumps(computer_dict))

    for partition_id in partitions:
        # Load instance information for bouture
        with open(os.path.join(instance_root, partition_id, BOUTURE_FILE)) as f:
            bouture = json.load(f)

        software_url = bouture['software-url']
        software_type = bouture['software-type']
        instance_name = bouture['instance-title']
        parameter_dict = bouture['config']
        state = bouture['instance-state']
        shared_list = bouture['shared-list']

        # Adapt parameter dict for monitoring
        # Hack: handle serialization
        if new_monitor_url:
            # match is Python3.10
            try:
                (key, serialized), = parameter_dict.items()
                if key != '_':
                    raise ValueError
            except ValueError:
                parameter_dict['monitor-interface-url'] = new_monitor_url
            else:
                deserialized = json.loads(serialized)
                deserialized['monitor-interface-url'] = new_monitor_url
                parameter_dict['_'] = json.dumps(deserialized)

        # Load partition IPs information
        with open(os.path.join(instance_root, partition_id, RESOURCE_FILE)) as f:
            resource = json.load(f)

        partition_list.append({
            'reference': partition_id,
            'address_list': resource['address_list'],
            'tap': resource['tap'],
        })

        logger.info(
            "Bouturing partition %s",
            partition_id,
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

        # Request shared instances
        logger.info(
            "Bouturing %s shared instances",
            len(shared_list),
        )
        for shared in shared_list:
            title = shared['slave-title']
            # XXX: slapproxy prepends shared names with _, and unlike SlapOS
            # master, it sets the reference and the title to this same value.
            # In case we ever bouture into the slapproxy from a bouture file
            # that was produced under the proxy, let's detect this and remove
            # the _ prefix so that the proxy does not end up with __ prefix.
            # In other words, let's keep bouture idempotent.
            if title == shared['slave-reference'] and title.startswith('_'):
              title = title[1:]
            slap.registerOpenOrder().request(
                software_url,
                title,
                shared['parameter-list'],
                shared['slap-software-type'],
                filter_kw={'instance_guid': cp._instance_guid},
                # state=?,
                shared=True,
            )

        # Bang the boutured instance to ensure it will be reprocessed
        # It must be reprocessed because the master changed, so the promises need
        # to be reconfigured to bang the new master, and possibly some parameters
        # changed as well, depending on the bouture file.
        cp.bang("Bouture")

        # XXX Workaround: Delete local timestamp file
        # Currently bang may not be enough if the new master has a different
        # time than the old master: the local timestamp file may contain a
        # timestamp from the old master that is more recent than the one from
        # the bang in the new master.
        # Until https://lab.nexedi.com/nexedi/slapos.core/-/merge_requests/824
        try:
            os.remove(os.path.join(
                instance_root,
                partition_id,
                COMPUTER_PARTITION_TIMESTAMP_FILENAME,
            ))
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


def parse_conf(cfg):
    configp = configparser.ConfigParser()
    if configp.read(cfg) != [cfg]:
       raise Exception("Could not read %s" % cfg)
    node_conf = {}
    for section in ("slapformat", "slapos"):
      node_conf.update(configp.items(section))
    return argparse.Namespace(**node_conf)


def configure(args):
    old_cfg = args.original_cfg
    new_cfg = args.new_cfg
    assert(old_cfg != new_cfg)
    logger.info(
        "Writing configuration for alternate master %s at %s",
        args.new_master_url,
        new_cfg,
    )
    configp = configparser.ConfigParser()
    if configp.read(old_cfg) != [old_cfg]:
       raise Exception("Could not read %s" % cfg)
    configp['slapos']['master_url'] = args.new_master_url
    # Remove client certificate parameters to disable client SSL
    configp.remove_option('slapos', 'key_file')
    configp.remove_option('slapos', 'cert_file')
    configp.remove_option('slapos', 'certificate_repository_path')
    with open(new_cfg, 'w') as f:
        configp.write(f)


def failover(args):
    setRunning(logger, args.pidfile)
    try:
        old_cfg = args.original_cfg
        new_cfg = args.new_cfg
        ret = subprocess.call(('slapos', 'node', 'instance', '--cfg', old_cfg))
        if ret == SLAPGRID_OFFLINE_SUCCESS:
            logger.info(
                "This node is unable to reach its SlapOS master"
            )
            if not os.path.exists(args.switchfile):
                configure(args)
                bouture(args, parse_conf(old_cfg))
                # Either bouture crashed and we don't reach here,
                # or bouture went ok and we continue.
                with open(args.switchfile, 'w') as f:
                    pass
            logger.info(
                "Processing this node from alternate master at %s",
                args.new_master_url,
            )
            subprocess.call(('slapos', 'node', 'instance', '--cfg', new_cfg))
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
            try:
                os.remove(args.switchfile)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    finally:
        setFinished(args.pidfile)


def graft(args):
    node_conf = parse_conf(args.cfg)
    bouture(args, node_conf)


def instance(args):
    subprocess.call(('slapos', 'node', 'instance', '--cfg', args.new_cfg))


def main():
    main_parser = argparse.ArgumentParser()
    subparsers = main_parser.add_subparsers()

    failover_parser = subparsers.add_parser('failover')
    failover_parser.set_defaults(func=failover)
    failover_parser.add_argument('--original-cfg', required=True)
    failover_parser.add_argument('--new-cfg', required=True)
    failover_parser.add_argument('--new-master-url', required=True)
    failover_parser.add_argument('--pidfile', required=True)
    failover_parser.add_argument('--switchfile', required=True)
    failover_parser.add_argument('--new-monitor-url')

    bouture_parser = subparsers.add_parser('graft')
    bouture_parser.set_defaults(func=graft)
    bouture_parser.add_argument('--cfg', required=True)
    bouture_parser.add_argument('--new-master-url', required=True)
    bouture_parser.add_argument('--new-monitor-url')

    configure_parser = subparsers.add_parser('configure')
    configure_parser.set_defaults(func=configure)
    configure_parser.add_argument('--original-cfg', required=True)
    configure_parser.add_argument('--new-cfg', required=True)
    configure_parser.add_argument('--new-master-url', required=True)

    instance_parser = subparsers.add_parser('instance')
    instance_parser.set_defaults(func=instance)
    instance_parser.add_argument('--new-cfg', required=True)

    args = main_parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()


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
