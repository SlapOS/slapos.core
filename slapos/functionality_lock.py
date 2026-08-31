# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2026 Vifib SARL and Contributors.
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

LOCK_FILENAME = '.slapos-functionality-lock'
SNAPSHOT_PATH = os.path.join('.slapgrid', 'functionality-snapshot.json')

INSTANCE_ROOT_ENVIRONMENT_NAME = 'SLAPGRID_INSTANCE_ROOT'

STATUS_TAG = '[functionality-locked]'


class SnapshotMissingError(Exception):
  """Partition is locked, but nothing was ever recorded to pin it to."""


def getPartitionPath(partition_id):
  """Partition directory as seen from inside a buildout run, or None.

  slapgrid exports the instance root so that the pin also applies to the slap
  library used by the software release's own recipes.
  """
  instance_root = os.environ.get(INSTANCE_ROOT_ENVIRONMENT_NAME)
  if not instance_root or not partition_id:
    return None
  return os.path.join(instance_root, partition_id)


def isLocked(partition_path):
  if not partition_path:
    return False
  return os.path.exists(os.path.join(partition_path, LOCK_FILENAME))


def readSnapshot(partition_path):
  try:
    with open(os.path.join(partition_path, SNAPSHOT_PATH)) as f:
      return json.load(f)
  except (IOError, OSError) as e:
    if e.errno != errno.ENOENT:
      raise
  except ValueError:
    pass
  return None


def writeSnapshot(partition_path, requested_state, software_release_url,
                  parameter_dict):
  snapshot = {
    'requested_state': requested_state,
    'software_release_url': software_release_url,
    'parameter_dict': parameter_dict,
  }
  if readSnapshot(partition_path) == snapshot:
    return
  snapshot_path = os.path.join(partition_path, SNAPSHOT_PATH)
  snapshot_directory = os.path.dirname(snapshot_path)
  if not os.path.isdir(snapshot_directory):
    os.makedirs(snapshot_directory)
  new_snapshot_path = snapshot_path + '.new'
  with open(new_snapshot_path, 'w') as f:
    json.dump(snapshot, f, sort_keys=True)
  # the software release reads it back as the partition user
  os.chmod(new_snapshot_path, 0o644)
  os.rename(new_snapshot_path, snapshot_path)


def getPinnedSnapshot(partition_id):
  """Snapshot to substitute for what SlapOS Master reports, or None."""
  partition_path = getPartitionPath(partition_id)
  if not isLocked(partition_path):
    return None
  snapshot = readSnapshot(partition_path)
  if snapshot is None:
    raise SnapshotMissingError(
      'Partition %s is functionality locked with no snapshot to pin it to.'
      % partition_id)
  return snapshot
