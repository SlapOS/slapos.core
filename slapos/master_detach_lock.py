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
import gzip
import hashlib
import json
import os

LOCK_FILENAME_PREFIX = '.slapos-master-detach-lock-'
STORE_PATH = os.path.join('.slapgrid', 'master-detach-lock')

INSTANCE_ROOT_ENVIRONMENT_NAME = 'SLAPGRID_INSTANCE_ROOT'

# What each token detaches, in operator terms. The mapping is versioned here so
# that renaming a method never asks an operator to rename a lock file.
TOKEN_METHOD_DICT = {
  'query': (
    'getState',
    'getInstanceParameterDict',
    'getConnectionParameterDict',
    'getSoftwareReleaseURI',
    'getInstanceGuid',
    'getCertificate',
    'getFullHostingIpAddressList',
  ),
  'modify-state': ('started', 'stopped', 'destroyed'),
  'modify-connection': (
    'setConnectionDict',
    'setComputerPartitionRelatedInstanceList',
  ),
  'modify-request': ('request',),
  'modify-error': ('error', 'bang'),
}

QUERY_TOKEN = 'query'


class UnknownTokenError(Exception):
  """A lock file names something that is not a detachable token."""


class RecordMissingError(Exception):
  """Partition is detached, but this call has no recorded answer to replay."""


def getPartitionPath(partition_id, partition_path=None):
  """Directory of the partition whose lock governs this call, or None.

  Callers inside a partition pass `partition_path`; slapgrid exports the
  instance root instead, which is all its own processing needs.

  A lock governs whoever can use the partition directory it lives in. One
  partition routinely holds a ComputerPartition describing another - every
  slapos.cookbook:request does - and partition directories belong to their own
  user, so the directory of somebody else's partition is not ours to read,
  write, or take a lock from.
  """
  path = partition_path
  if not path:
    instance_root = os.environ.get(INSTANCE_ROOT_ENVIRONMENT_NAME)
    if not instance_root or not partition_id:
      return None
    path = os.path.join(instance_root, partition_id)
  if not os.access(path, os.R_OK | os.W_OK | os.X_OK):
    return None
  return path


def getArmedTokenList(partition_path):
  """Tokens armed on this partition, sorted.

  A file naming an unknown token raises instead of being ignored: a typo must
  never read as "nothing to detach".
  """
  if not partition_path:
    return []
  try:
    name_list = os.listdir(partition_path)
  except (IOError, OSError) as e:
    if e.errno not in (errno.ENOENT, errno.EACCES, errno.EPERM):
      raise
    return []
  token_list = []
  for name in name_list:
    if not name.startswith(LOCK_FILENAME_PREFIX):
      continue
    token = name[len(LOCK_FILENAME_PREFIX):]
    if token not in TOKEN_METHOD_DICT:
      raise UnknownTokenError(
        '%s names no detachable token; expected one of %s'
        % (name, ', '.join(sorted(TOKEN_METHOD_DICT))))
    token_list.append(token)
  return sorted(token_list)


def isDetached(partition_path):
  return bool(getArmedTokenList(partition_path))


def getStatusTag(partition_path):
  return '[detached:%s]' % ','.join(getArmedTokenList(partition_path))


def getMethodToken(method):
  for token, method_list in TOKEN_METHOD_DICT.items():
    if method in method_list:
      return token
  return None


def isMethodDetached(partition_path, method):
  token = getMethodToken(method)
  return token is not None and token in getArmedTokenList(partition_path)


def getCallKey(method, args):
  return hashlib.sha256(
    json.dumps([method, args], sort_keys=True).encode('utf-8')).hexdigest()


def getCallFileName(method, args):
  """Name of the file holding this call, token and method first so that a
  plain listing of the store says what is in it."""
  return '%s-%s-%s.json.gz' % (
    getMethodToken(method) or 'other', method, getCallKey(method, args))


def readCall(partition_path, method, args=()):
  """The recorded entry for this call, or None when nothing is recorded.

  An entry, not the bare response: a recorded response may legitimately be
  null, which must not read as "never recorded".
  """
  path = os.path.join(partition_path, STORE_PATH,
                      getCallFileName(method, list(args)))
  try:
    with gzip.open(path) as f:
      entry = json.loads(f.read().decode('utf-8'))
  except (IOError, OSError) as e:
    # unreadable gzip data carries no errno; a record that cannot be read
    # counts as missing, which the query path then reports loudly
    if e.errno not in (None, errno.ENOENT):
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
  path = os.path.join(store, getCallFileName(method, list(args)))
  new_path = path + '.new'
  # a query record holds whatever Master answered, which for a frontend's
  # instance parameters is megabytes of slave list; the fastest level already
  # takes two orders of magnitude off it
  with gzip.open(new_path, 'wb', 1) as f:
    f.write(json.dumps(
      {'method': method, 'args': list(args), 'response': response},
      sort_keys=True).encode('utf-8'))
  # the software release reads it back as the partition user
  os.chmod(new_path, 0o644)
  os.rename(new_path, path)


def getPinnedCall(partition_id, method, args=(), partition_path=None):
  """Recorded answer to replay, or None when this call is not detached."""
  path = getPartitionPath(partition_id, partition_path)
  if not path or not isMethodDetached(path, method):
    return None
  entry = readCall(path, method, args)
  if entry is None:
    raise RecordMissingError(
      'Partition %s is detached with no recorded %s to replay.'
      % (partition_id, method))
  return entry['response']


def suppressCall(partition_id, method, attempt, args=(), partition_path=None):
  """True when this modification must not reach Master; records the attempt.

  A suppressed modification has nothing to replay, so unlike getPinnedCall a
  missing record is not an error - the record exists so that reattaching shows
  what the partition wanted to say.
  """
  path = getPartitionPath(partition_id, partition_path)
  if not path or not isMethodDetached(path, method):
    return False
  recordCall(path, method, attempt, args)
  return True
