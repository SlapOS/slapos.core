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
import hashlib
import json
import os

LOCK_FILENAME = '.slapos-functionality-lock'
STORE_PATH = os.path.join('.slapgrid', 'functionality-lock')
SEED_SNAPSHOT_PATH = os.path.join('.slapgrid', 'functionality-snapshot.json')

INSTANCE_ROOT_ENVIRONMENT_NAME = 'SLAPGRID_INSTANCE_ROOT'

STATUS_TAG = '[functionality-locked]'

# Fields of the single-file snapshot the store can be seeded from, and the call
# each one answers.
SEED_CALL_LIST = (
  ('requested_state', 'getState', ()),
  ('software_release_url', 'getSoftwareReleaseURI', ()),
  ('parameter_dict', 'getInstanceParameterDict', ()),
)


class SnapshotMissingError(Exception):
  """Partition is locked, but this call was never recorded to pin it to."""


def getPartitionPath(partition_id, partition_path=None):
  """Directory of the partition whose lock governs this call, or None.

  Callers inside a partition pass `partition_path`; slapgrid exports the
  instance root instead, which is all its own processing needs.
  """
  if partition_path:
    return partition_path
  instance_root = os.environ.get(INSTANCE_ROOT_ENVIRONMENT_NAME)
  if not instance_root or not partition_id:
    return None
  return os.path.join(instance_root, partition_id)


def isLocked(partition_path):
  if not partition_path:
    return False
  return os.path.exists(os.path.join(partition_path, LOCK_FILENAME))


def getCallKey(method, args):
  return hashlib.sha256(
    json.dumps([method, args], sort_keys=True).encode('utf-8')).hexdigest()


def readCall(partition_path, method, args=()):
  """The recorded entry for this call, or None when nothing is recorded.

  An entry, not the bare response: a recorded response may legitimately be
  null, which must not read as "never recorded".
  """
  path = os.path.join(partition_path, STORE_PATH,
                      '%s.json' % getCallKey(method, list(args)))
  try:
    with open(path) as f:
      entry = json.load(f)
  except (IOError, OSError) as e:
    if e.errno != errno.ENOENT:
      raise
    return None
  except ValueError:
    return None
  if 'response' not in entry:
    return None
  return entry


def recordCall(partition_path, method, response, args=()):
  """Remember what SlapOS Master answered, so a later lock can replay it."""
  entry = readCall(partition_path, method, args)
  if entry is not None and entry['response'] == response:
    return
  store = os.path.join(partition_path, STORE_PATH)
  if not os.path.isdir(store):
    os.makedirs(store)
  path = os.path.join(store, '%s.json' % getCallKey(method, list(args)))
  new_path = path + '.new'
  with open(new_path, 'w') as f:
    json.dump({'method': method, 'args': list(args), 'response': response},
              f, sort_keys=True)
  # the software release reads it back as the partition user
  os.chmod(new_path, 0o644)
  os.rename(new_path, path)


def seedFromSnapshotFile(partition_path):
  """Fill an empty store from a single-file snapshot, where one is left.

  A partition locked before the store existed would otherwise have to be
  unlocked to become lockable again.
  """
  if os.path.isdir(os.path.join(partition_path, STORE_PATH)):
    return
  try:
    with open(os.path.join(partition_path, SEED_SNAPSHOT_PATH)) as f:
      snapshot = json.load(f)
  except (IOError, OSError) as e:
    if e.errno != errno.ENOENT:
      raise
    return
  except ValueError:
    return
  for field, method, args in SEED_CALL_LIST:
    if field in snapshot:
      recordCall(partition_path, method, snapshot[field], args)


def getPinnedCall(partition_id, method, args=(), partition_path=None):
  """Recorded answer to substitute for SlapOS Master's, or None if unlocked."""
  path = getPartitionPath(partition_id, partition_path)
  if not isLocked(path):
    return None
  seedFromSnapshotFile(path)
  entry = readCall(path, method, args)
  if entry is None:
    raise SnapshotMissingError(
      'Partition %s is functionality locked with no recorded %s to pin it to.'
      % (partition_id, method))
  return entry['response']
