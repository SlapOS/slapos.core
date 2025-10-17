# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
import errno
import json
import os
import subprocess

import slapos.slap.slap
from slapos.util import dumps
from slapos.format import Partition

from slapos.grid.slapgrid import (
    SLAPGRID_SUCCESS,
    SLAPGRID_PROMISE_FAIL,
    SLAPGRID_OFFLINE_SUCCESS,
)
from slapos.grid.utils import setRunning, setFinished

# XXX https://lab.nexedi.com/nexedi/slapos.core/-/merge_requests/824
from slapos.grid.slapgrid import COMPUTER_PARTITION_TIMESTAMP_FILENAME


RESOURCE_FILE = Partition.resource_file
BOUTURE_FILE = 'bouture.json'


def parse_conf(configp):
    node_conf = {}
    for section in ("slapformat", "slapos"):
      node_conf.update(configp.items(section))
    return node_conf


class Bouture(object):
    def __init__(self, logger, node_configp):
        self.logger = logger
        # Local node configuration
        node_conf = parse_conf(node_configp)
        self.computer_id = node_conf['computer_id']
        self.instance_root = node_conf['instance_root']
        self.slappart_base = node_conf['partition_base_name']
        # Keep the original configp for later use
        # to modify it to generate the alternate.
        self.node_configp = node_configp

    def partition_path(self, partition_id, *fragments):
        return os.path.join(self.instance_root, partition_id, *fragments)

    def find_bouture_partition_id_list(self):
        bouture_partition_id_list = []
        base = self.slappart_base
        for p in os.listdir(self.instance_root):
            if p.startswith(base) and p[len(base):].isdigit():
                # p is a partition
                if os.path.exists(self.partition_path(p, BOUTURE_FILE)):
                    bouture_partition_id_list.append(p)
        return bouture_partition_id_list

    def graft(self, args):
        # Bouture arguments
        new_master_url = args.new_master_url
        new_monitor_url = args.new_monitor_url
        self.logger.info(
            "Grafting this node onto alternate master at %s",
            new_master_url,
        )
        # Find bouture partition
        partition_id_list = self.find_bouture_partition_id_list()
        if not partition_id_list:
            self.logger.info(
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
            reference=self.computer_id,
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
        # Empty preexisting partitions of any instances and shared instances
        slap.registerComputer(self.computer_id).updateConfiguration(
          dumps(computer_dict)
        )
        for partition_id in partition_id_list:
            # Load instance information for bouture
            with open(self.partition_path(partition_id, BOUTURE_FILE)) as f:
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
                # BBB: match/case is Python3.10+ but would be perfect here
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
            with open(self.partition_path(partition_id, RESOURCE_FILE)) as f:
                resource = json.load(f)
            partition_list.append({
                'reference': partition_id,
                'address_list': resource['address_list'],
                'tap': resource['tap'],
            })
            self.logger.info(
                "Bouturing partition %s",
                partition_id,
            )
            # Register bouture partition
            # (the partition that was just appended to partition_list)
            slap.registerComputer(self.computer_id).updateConfiguration(
              dumps(computer_dict)
            )
            # Supply bouture SR
            slap.registerSupply().supply(software_url, self.computer_id)
            # Request bouture instance
            cp = slap.registerOpenOrder().request(
                software_url,
                instance_name,
                parameter_dict,
                software_type,
                state=state,
            )
            # Request shared instances
            self.logger.info(
                "Grafting %s shared instances",
                len(shared_list),
            )
            for shared in shared_list:
                title = shared['slave-title']
                # XXX: slapproxy prepends shared names with _, and unlike
                # SlapOS master, it sets the reference and title to this
                # same value. In case we ever bouture into the slapproxy
                # from a bouture file that was produced under the proxy,
                # let's detect this and remove the _ prefix so that the
                # proxy does not end up with __ prefix.
                # In other words, let's keep bouture idempotent.
                reference = shared['slave-reference']
                if title == reference and title.startswith('_'):
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
            # This is needed because the master changed, so the promises
            # need to be reconfigured to bang the new master; also possibly
            # some parameters changed as well, depending on the bouture file.
            cp.bang("Bouture")
            # XXX Workaround: Delete local timestamp file
            # Currently calling bang may not be enough if the new master has a
            # different time than the old master: the local timestamp file may
            # contain a timestamp from the old master that is more recent than
            # the one from the bang in the new master.
            # Cf https://lab.nexedi.com/nexedi/slapos.core/-/merge_requests/824
            try:
                os.remove(self.partition_path(
                    partition_id,
                    COMPUTER_PARTITION_TIMESTAMP_FILENAME,
                ))
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            else:
                self.logger.info(
                    "Removed %s's timestamp",
                    partition_id,
                )

    def configure(self, args):
        alternate_cfg = args.new_node_cfg
        assert(args.cfg != alternate_cfg)
        self.logger.info(
            "Writing configuration for alternate master %s at %s",
            args.new_master_url,
            alternate_cfg,
        )
        # Destructively modify the parsed configp from the original cfg,
        # that's ok, it won't be used anymore, this is the only reason
        # we kept it around.
        configp = self.node_configp
        del self.node_configp
        configp['slapos']['master_url'] = args.new_master_url
        # Remove client certificate parameters to disable client SSL
        configp.remove_option('slapos', 'key_file')
        configp.remove_option('slapos', 'cert_file')
        configp.remove_option('slapos', 'certificate_repository_path')
        with open(alternate_cfg, 'w') as f:
            configp.write(f)

    def failover(self, args):
        setRunning(self.logger, args.pidfile)
        try:
            self.logger.info(
                "Process node with original (pre-bouture) master"
            )
            ret = subprocess.call((
              'slapos', 'node', 'instance',
              '--cfg', args.cfg,
            ))
            if ret == SLAPGRID_OFFLINE_SUCCESS:
                self.logger.info(
                    "This node is unable to reach its SlapOS master"
                )
                if not os.path.exists(args.switchfile):
                    self.configure(args)
                    self.graft(args)
                    # Either bouture crashed and we don't reach here,
                    # or bouture went ok and we continue.
                    with open(args.switchfile, 'w') as f:
                        pass
                self.logger.info(
                    "Processing this node from alternate master at %s",
                    args.new_master_url,
                )
                subprocess.call((
                  'slapos', 'node', 'instance',
                  '--cfg', args.new_node_cfg,
                ))
            elif ret in (SLAPGRID_SUCCESS, SLAPGRID_PROMISE_FAIL):
                # If slaps node instance succeeded or only the promises failed,
                # we can be sure that master was reachable.
                if ret == SLAPGRID_SUCCESS:
                    msg = "slapos node instance succeeded"
                else:
                    msg = "slapos node instance worked but promises failed"
                self.logger.info(
                    "This node is able to reach its SlapOS master: %s" % msg
                )
                try:
                    os.remove(args.switchfile)
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise
            else:
                # If slapos node instance failed and it wasn't just the promises,
                # then either the master is reachable but buildout crashed, or
                # the master is unreachable and offline processing failed, or
                # maybe the master stopped being reachable midway.
                # Whatever the case, either the switchfile was never created yet,
                # or it was already removed previously, or it still exists. If it
                # does still exist, it's likely the bouture file was not properly
                # produced, so it's better not to remove the switchfile for now:
                # either the situation will stabilize towards offline success, and
                # what's already in the proxy is better than a stale or corrupted
                # bouture file, or it will stabilize towards a working instance and
                # a clearly reachable master, and the switchfile will be removed.
                # If it never stabilize, something is wrong beyond the normal
                # working bounds of the instance anyway.
                self.logger.info(
                    "This node is in an ambiguous state: slapos node instance "
                    "failed in an unexpected way (returned %d). "
                    "Let's wait until it stabilizes.",
                    ret,
                )
        finally:
            setFinished(args.pidfile)
