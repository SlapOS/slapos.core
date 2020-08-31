# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors.
# All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

import argparse
import os.path
import sys
import six

import slapos.slap.slap
from slapos.grid.slapgrid import COMPUTER_PARTITION_TIMESTAMP_FILENAME, \
    COMPUTER_PARTITION_LATEST_BANG_TIMESTAMP_FILENAME

from slapos.grid.SlapObject import WATCHDOG_MARK


def parseArgumentTuple():
  parser = argparse.ArgumentParser()
  parser.add_argument("--master-url",
                      help="The master server URL. Mandatory.",
                      required=True)
  parser.add_argument("--computer-id",
                      help="The computer id defined in the server.",
                      required=True)
  parser.add_argument("--certificate-repository-path",
                      help="Path to partition certificates.",
                      default=None)
  parser.add_argument("--instance-root-path",
                      help="Path to instance root directory.",
                      default=None)
  option = parser.parse_args()

  # Build option_dict
  option_dict = {}
  for argument_key, argument_value in six.iteritems(vars(option)):
    option_dict.update({argument_key: argument_value})

  return option_dict


class Watchdog(object):

  process_state_events = ['PROCESS_STATE_EXITED', 'PROCESS_STATE_FATAL']

  def __init__(self, master_url, computer_id,
               certificate_repository_path=None, instance_root_path=None):
    self.master_url = master_url
    self.computer_id = computer_id
    self.certificate_repository_path = certificate_repository_path
    self.instance_root_path = instance_root_path

    self.stdin = sys.stdin
    self.stdout = sys.stdout
    self.stderr = sys.stderr
    self.slap = slapos.slap.slap()

  def initialize_connection(self, partition_id):
    cert_file = None
    key_file = None
    if self.certificate_repository_path:
      cert_file = os.path.join(self.certificate_repository_path,
                              "%s.crt" % partition_id)
      key_file = os.path.join(self.certificate_repository_path,
                             "%s.key" % partition_id)
    self.slap.initializeConnection(
      slapgrid_uri=self.master_url, key_file=key_file, cert_file=cert_file)

  def write_stdout(self, s):
    self.stdout.write(s)
    self.stdout.flush()

  def write_stderr(self, s):
    self.stderr.write(s)
    self.stderr.flush()

  def run(self):
    while True:
      self.write_stdout('READY\n')
      line = self.stdin.readline()  # read header line from stdin
      headers = dict([x.split(':') for x in line.split()])
      data = sys.stdin.read(int(headers['len']))  # read the event payload
      self.handle_event(headers, data)
      self.write_stdout('RESULT 2\nOK')  # transition from READY to ACKNOWLEDGED

  def handle_event(self, headers, payload):
    if headers['eventname'] in self.process_state_events:
      payload_dict = dict([x.split(':') for x in payload.split()])
      if WATCHDOG_MARK in payload_dict['processname'] and \
         not self.has_bang_already_been_called(payload_dict['groupname']):
        self.handle_process_state_change_event(headers, payload_dict)

  def has_bang_already_been_called(self, partition_name):
    """
    Checks if bang has already been called since last successful deployment
    """
    if not self.instance_root_path:
      # Backward compatibility
      return False

    partition_home_path = os.path.join(
        self.instance_root_path,
        partition_name
    )
    partition_timestamp_file_path = os.path.join(
        partition_home_path,
        COMPUTER_PARTITION_TIMESTAMP_FILENAME
    )
    slapos_last_bang_timestamp_file_path = os.path.join(
        partition_home_path,
        COMPUTER_PARTITION_LATEST_BANG_TIMESTAMP_FILENAME
    )

    if not os.path.exists(slapos_last_bang_timestamp_file_path):
      # Never heard of any previous bang
      return False

    if not os.path.exists(partition_timestamp_file_path):
      # Partition never managed to deploy successfully, ignore bang
      return True

    with open(slapos_last_bang_timestamp_file_path, 'r') as f:
      last_bang_timestamp = int(f.read())
    with open(partition_timestamp_file_path, 'r') as f:
      deployment_timestamp = int(f.read())
    if deployment_timestamp > last_bang_timestamp:
      # It previously banged BEFORE latest successful deployment
      # i.e it haven't banged since last successful deployment
      return False

    # It previously banged AFTER latest successful deployment: ignore
    return True

  def create_partition_bang_timestamp_file(self, partition_name):
    """
    Copy the timestamp file of the partition to a bang timestamp file.
    If timestamp file does not exist, create a dummy bang timestamp file.
    """
    if not self.instance_root_path:
      # Backward compatibility
      return

    partition_home_path = os.path.join(
        self.instance_root_path,
        partition_name
    )
    partition_timestamp_file_path = os.path.join(
        partition_home_path,
        COMPUTER_PARTITION_TIMESTAMP_FILENAME
    )
    slapos_last_bang_timestamp_file_path = os.path.join(
        partition_home_path,
        COMPUTER_PARTITION_LATEST_BANG_TIMESTAMP_FILENAME
    )
    if os.path.exists(partition_timestamp_file_path):
      with open(partition_timestamp_file_path, 'r') as f:
        timestamp = f.read()
    else:
      timestamp = '0'
    with open(slapos_last_bang_timestamp_file_path, 'w') as f:
      f.write(timestamp)

  def handle_process_state_change_event(self, headers, payload_dict):
    partition_id = payload_dict['groupname']
    self.initialize_connection(partition_id)
    partition = slapos.slap.ComputerPartition(
      computer_id=self.computer_id,
      connection_helper=self.slap._connection_helper,
      partition_id=partition_id)
    partition.bang("%s process in partition %s encountered a problem"
                   % (payload_dict['processname'], partition_id))
    self.create_partition_bang_timestamp_file(payload_dict['groupname'])


def main():
  watchdog = Watchdog(**parseArgumentTuple())
  watchdog.run()

if __name__ == '__main__':
  main()
