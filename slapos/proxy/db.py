import time

import requests
import slapos
from slapos.slap.slap import ComputerPartition, SoftwareInstance, SoftwareRelease
from slapos.util import xml2dict, dict2xml, dumps, loads, bytes2str

import six
from six.moves.urllib.parse import urlparse, urljoin

from flask import g, current_app, request, url_for
from slapos.proxy.db_version import DB_VERSION
from slapos.slap.slap import DEFAULT_SOFTWARE_TYPE, OLD_DEFAULT_SOFTWARE_TYPE

class NotFoundPartitionFailure(Exception):
  pass

class PartitionDeletionFailure(Exception):
  pass

class AllocationFailure(Exception):
  pass

class HostNotReady(AllocationFailure):
  """A shared instance's hosting instance is not available yet.

  Distinct from a capacity exhaustion: the host is another instance that a
  later slapgrid run may allocate, so this is transient. It mirrors the
  master's pending Slave Instance, which returns the 102 SoftwareInstanceNotReady
  arm until the slave is allocated, rather than a terminal failure. It stays an
  AllocationFailure subclass so the slap_tool blueprint keeps treating it like
  any other allocation miss."""
  pass

class ConfigurationError(Exception):
  pass

class UnknownRequester(Exception):
  """An identity was asserted but does not resolve to a known, allocated
  instance."""
  pass


def encodeSharedParameters(parameters):
  """Serialize shared-instance parameters preserving their Python types.

  Shared params travel to the hosting software through the slave_instance_list
  projection, which deployed SRs (rapid-cdn, re6stnet) parse for typed values
  (int ports, bool flags, nested dict/list). xml_marshaller round-trips those
  types verbatim; dict2xml would stringify them. Non-shared params keep dict2xml
  (which stringifies, mirroring the master)."""
  return bytes2str(dumps(parameters))


def decodeSharedParameters(xml):
  """Decode a shared row's typed parameter blob written by
  encodeSharedParameters."""
  return loads(xml.encode('utf-8'))


def execute_db(table, query, args=(), one=False, db_version=DB_VERSION, db=None):
  if not db:
    db = g.db
  query = query % (table + db_version,)
  # current_app.logger.debug(query)
  # try:
  cur = db.execute(query, args)
  # except Exception:
  #   current_app.logger.error(
  #     'There was some issue during processing query %r on table %r with args %r',
  #     query, table, args)
  #   raise
  rv = ({cur.description[idx][0]: value
    for idx, value in enumerate(row)} for row in cur)
  return next(rv, None) if one else list(rv)


def _write(table, query, args=()):
  """Run an INSERT/UPDATE/DELETE statement, returning the cursor so callers
  can read rowcount. Mirrors execute_db's table/version substitution."""
  return g.db.execute(query % (table + DB_VERSION,), args)


def checkIfMasterIsCurrentMaster(master_url):
  """
  Because there are several ways to contact this server, we can't easily check
  in a request() if master_url is ourself or not. So we contact master_url,
  and if it returns an ID we know: it is ourself
  """
  # Dumb way: compare with listening host/port
  host = request.host
  port = request.environ['SERVER_PORT']
  if master_url == 'http://%s:%s/' % (host, port):
    return True

  # Hack way: call ourself
  try:
    return current_app.config['run_id'] == requests.get(
      urljoin(master_url, 'getRunId')).text
  except Exception:
    return False


def formatFromDB(computer_reference, partition_list,
                 computer_address=None,
                 computer_netmask=None):
  execute_db('computer', 'INSERT OR REPLACE INTO %s values(?, ?, ?)',
             (computer_reference, computer_address, computer_netmask))

  # Create as many placeholders as partitions requested; the first argument is
  # the computer_reference, followed by every requested partition reference.
  placeholders = ','.join('?' * len(partition_list))
  reference_args = [x['partition_id'] for x in partition_list]

  # remove references to old partitions (pure resource rows).
  execute_db(
    'partition',
    'DELETE FROM %s WHERE computer_reference = ? and reference not in ({})'.format(
      placeholders),
    [computer_reference] + reference_args
  )
  # An instance is allocated to a partition; deleting the partition row
  # deletes its instance too.
  execute_db(
    'instance',
    'DELETE FROM %s WHERE allocated_computer = ? and allocated_partition not in ({})'.format(
      placeholders),
    [computer_reference] + reference_args
  )
  execute_db('partition_network', 'DELETE FROM %s WHERE computer_reference = ?', (computer_reference,))

  for partition in partition_list:
    partition['computer_reference'] = computer_reference
    execute_db('partition', 'INSERT OR IGNORE INTO %s (reference, computer_reference) values(:partition_id, :computer_reference)', partition)
    for ip in partition['ip_list']:
      execute_db(
        'partition_network',
        'INSERT OR REPLACE INTO %s (reference, partition_reference, computer_reference, address, netmask) values(?, ?, ?, ?, ?)',
        (ip['network-interface'], partition['partition_id'], computer_reference,
         ip['ip-address'], ip.get('netmask', ''))
      )


def supplyFromDB(computer_reference, software_release_url, state):
  if state not in ('available', 'destroyed'):
    raise ValueError("Wrong state %s" % state)

  execute_db(
    'software',
    'INSERT OR REPLACE INTO %s VALUES(?, ?, ?)',
    [software_release_url, computer_reference, state])


def removeFromDB(computer_reference, software_release_url):
  execute_db(
    'software',
    'DELETE FROM %s WHERE url = ? and computer_reference=? ',
    [software_release_url, computer_reference])


def getPartitionFromDB(reference, computer_reference):
  """Resolve a partition RESOURCE row (address + allocation state)."""
  partition = execute_db('partition',
    'SELECT * FROM %s WHERE reference=? AND computer_reference=?',
    (reference, computer_reference), one=True)
  if partition is None:
    current_app.logger.warning("Nonexisting partition %r on %r",
      reference, computer_reference)
  return partition


def getInstanceByGuid(instance_guid):
  """Resolve an instance_guid to its instance row, or None.

  The guid is opaque and this function never inspects its format. Minted
  'SOFTINST-N' guids and the 'computer-slappartN' guids frozen for migrated
  instances both resolve through this one indexed PK lookup, with no special
  case.
  """
  return execute_db('instance',
    'SELECT * FROM %s WHERE instance_guid=?', (instance_guid,), one=True)


def mintInstanceGuid():
  """Mint a fresh 'SOFTINST-N' guid from the monotonic last_instance_id counter.

  The counter only grows and guids are never reused. instance_guid is the
  PRIMARY KEY; on the (theoretical) conflict with a frozen guid that happens to
  look like 'SOFTINST-N', the counter is incremented and a fresh value tried.
  """
  row = execute_db('config',
    "SELECT value FROM %s WHERE name='last_instance_id'", one=True)
  counter = int(row['value']) if row and row['value'] is not None else 0
  while True:
    counter += 1
    guid = 'SOFTINST-%s' % counter
    if getInstanceByGuid(guid) is None:
      break
  execute_db('config',
    "INSERT OR REPLACE INTO %s (name, value) VALUES ('last_instance_id', ?)",
    (str(counter),))
  return guid


def identifyRequester(computer_id, partition_id):
  """Resolve an asserted (computer_id, partition_id) to the requester's
  instance row.

  Returns None ONLY when NEITHER field is present (no identity asserted =
  direct user request). Raises UnknownRequester when an identity is asserted
  but does not resolve -- including a PARTIAL assertion (exactly one of the two
  fields present): a half-pair is a malformed assertion, not the absence of
  one, so it is treated as bogus rather than silently downgraded to user.

  This is the proxy-local substitute for the master deriving the requester from
  the TLS client certificate: the assertion is trusted (the proxy mints no
  credentials -- deliberate, local-only), but it is verified to EXIST so a
  bogus identity fails explicitly instead of silently founding a new root tree.
  """
  if not computer_id and not partition_id:
    return None
  if not computer_id or not partition_id:
    raise UnknownRequester(
      'Incomplete requester identity: computer_id=%r partition_id=%r'
      % (computer_id, partition_id))
  requester = execute_db('instance',
    'SELECT * FROM %s'
    ' WHERE allocated_computer=? AND allocated_partition=? AND shared=0',
    (computer_id, partition_id), one=True)
  if requester is None:
    raise UnknownRequester(
      'Requester %r on %r is not a known allocated instance'
      % (partition_id, computer_id))
  return requester


def requesterScope(requester):
  """(root_instance_guid, requested_by_instance_guid) for a requester row.

  A None requester (direct user request) scopes to the empty root, i.e. the
  requested instance becomes a root of its own tree.
  """
  if requester is None:
    return '', ''
  return (requester['root_instance_guid'] or requester['instance_guid'],
          requester['instance_guid'])


def getRootInstanceTitle(row):
  """Title of the tree root the given instance row belongs to."""
  if not row['root_instance_guid']:
    return row['title']
  root = getInstanceByGuid(row['root_instance_guid'])
  return root['title'] if root else row['title']


def _touch(computer_reference, partition_reference):
  """Bump the hosting (non-shared) instance's timestamp so slapgrid reprocesses
  the partition. A shared-row mutation marks its host through here, since the
  host partition is what materializes the shared instance."""
  execute_db('instance',
    'UPDATE %s SET timestamp=?'
    ' WHERE shared=0 AND allocated_computer=? AND allocated_partition=?',
    (time.time(), computer_reference, partition_reference))


def _resolveSharedHost(filter_kw, software_release, software_type, computer_id):
  """Find the non-shared instance whose partition will host a shared instance.

  With an 'instance_guid' SLA filter the host is pinned to that exact instance's
  partition; the miss is a soft HostNotReady (transient), never a 5xx/403 on the
  request path. Without it, the host is any non-shared instance on the computer
  matching the software release (and type if given)."""
  if 'instance_guid' in filter_kw:
    host = getInstanceByGuid(filter_kw['instance_guid'])
    if host is None or host['shared'] or host['allocated_partition'] is None:
      raise HostNotReady(
        'No instance %s to host shared instance' % filter_kw['instance_guid'])
    # The instance_guid filter pins the partition, but the base software
    # release / computer / type constraints still apply (the pin is an
    # additional constraint, not a bypass) -- otherwise a stale guid silently
    # mis-pins.
    if host['software_release'] != software_release \
        or host['allocated_computer'] != computer_id \
        or (software_type and host['software_type'] != software_type):
      raise HostNotReady(
        'No instance %s to host shared instance' % filter_kw['instance_guid'])
    return host
  args = [software_release, computer_id]
  q = ('SELECT * FROM %s WHERE shared=0 AND software_release=?'
       ' AND allocated_computer=? AND allocated_partition IS NOT NULL')
  if software_type:
    q += ' AND software_type=?'
    args.append(software_type)
  host = execute_db('instance', q, args, one=True)
  if host is None:
    raise HostNotReady(
      'No instance to host shared instance for %s' % software_release)
  return host


def _pickFreePartition(computer_id):
  """Pick a free partition slot on the given computer, marking it busy."""
  partition = execute_db('partition',
    "SELECT * FROM %s WHERE slap_state='free' and computer_reference=?",
    [computer_id], one=True)
  if partition is None:
    current_app.logger.warning('No more free computer partition')
    raise AllocationFailure(
      'No free computer partition found on %s' % computer_id)
  execute_db('partition',
    "UPDATE %s SET slap_state='busy' WHERE reference=? AND computer_reference=?",
    (partition['reference'], partition['computer_reference']))
  return partition


def requestInstance(requester, title, software_release, software_type,
                    parameters, sla, requested_state, shared):
  """Allocate or update one instance row and return the fresh row.

  Idempotency is keyed on (title, root_instance_guid, shared) -- the master's
  title-unique-per-instance-tree scope. Both tree edges (root_instance_guid and
  requested_by_instance_guid) are stamped from requesterScope() at creation.
  """
  if parameters is None:
    parameters = {}
  if sla is None:
    sla = {}
  shared = 1 if shared else 0
  if not shared and not software_type:
    software_type = DEFAULT_SOFTWARE_TYPE
  computer_id = sla.get('computer_guid', current_app.config['computer_id'])
  root_guid, requester_guid = requesterScope(requester)
  instance_xml = encodeSharedParameters(parameters) if shared \
    else dict2xml(parameters)

  if shared and requested_state == 'destroyed':
    # A shared destroy is expressed at request time. Delete the row so it
    # leaves the derived slave_instance_list projection and reprocess the host;
    # a first-ever destroyed request creates nothing. The pre-delete row (or
    # None) is returned so the destroy wire can still describe what was
    # destroyed.
    existing = execute_db('instance',
      'SELECT * FROM %s WHERE title=? AND root_instance_guid=? AND shared=1',
      (title, root_guid), one=True)
    if existing is not None:
      _write('instance', 'DELETE FROM %s WHERE instance_guid=?',
        (existing['instance_guid'],))
      _touch(existing['allocated_computer'], existing['allocated_partition'])
    return existing

  row = execute_db('instance',
    'SELECT * FROM %s WHERE title=? AND root_instance_guid=? AND shared=?',
    (title, root_guid, shared), one=True)

  if row is None:
    guid = mintInstanceGuid()
    if shared:
      host = _resolveSharedHost(sla, software_release, software_type, computer_id)
      allocated_computer = host['allocated_computer']
      allocated_partition = host['allocated_partition']
      # Frozen at creation: the legacy '<root_title>_<title>' wire reference the
      # slave_instance_list projection exposes. Frozen so a later root rename
      # does not silently change the wire reference under the hosting software.
      root_title = getRootInstanceTitle(requester) if requester is not None else ''
      slave_reference = root_title + '_' + title
      # slave_reference is the wire key the projection exposes and
      # setComputerPartitionConnectionXml addresses; two distinct shared
      # instances on one host must not collide on it. A title rename followed
      # by a re-request of the original title can mint a new instance whose
      # legacy concat equals an existing one -- disambiguate deterministically
      # with the fresh (unique) guid. Existing (including migrated) refs are
      # untouched.
      if execute_db('instance',
          'SELECT instance_guid FROM %s WHERE shared=1 AND allocated_computer=?'
          ' AND allocated_partition=? AND slave_reference=?',
          (allocated_computer, allocated_partition, slave_reference),
          one=True) is not None:
        slave_reference = slave_reference + '-' + guid
    else:
      partition = _pickFreePartition(computer_id)
      allocated_computer = partition['computer_reference']
      allocated_partition = partition['reference']
      slave_reference = None
    execute_db('instance',
      'INSERT INTO %s (instance_guid, title, shared, root_instance_guid,'
      ' requested_by_instance_guid, software_release, software_type,'
      ' requested_state, xml, connection_xml, sla_xml, slave_reference,'
      ' allocated_computer, allocated_partition, timestamp)'
      ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
      (guid, title, shared, root_guid, requester_guid, software_release,
       software_type, requested_state or 'started', instance_xml, None,
       dict2xml(sla) if sla else None, slave_reference,
       allocated_computer, allocated_partition, time.time()))
    if shared:
      _touch(allocated_computer, allocated_partition)
    return getInstanceByGuid(guid)

  guid = row['instance_guid']
  if root_guid:
    # propagate parent state to child: a child can be stopped or destroyed
    # while its parent is started, but not started while the parent is not.
    root = getInstanceByGuid(root_guid)
    if root and root['requested_state'] != 'started':
      requested_state = root['requested_state']

  changed = row['timestamp'] is None
  updates = []
  args = []
  for k, v in (('requested_state', requested_state or row['requested_state']),
               ('software_release', software_release),
               ('software_type', software_type or row['software_type']),
               ('xml', instance_xml)):
    if row[k] != v:
      updates.append('%s=?' % k)
      args.append(v)
      changed = True
  if changed:
    updates.append('timestamp=?')
    args.append(time.time())
    args.append(guid)
    _write('instance',
      'UPDATE %s SET ' + ', '.join(updates) + ' WHERE instance_guid=?', args)
    if shared:
      _touch(row['allocated_computer'], row['allocated_partition'])
  result = getInstanceByGuid(guid)
  # The wire response reports the EFFECTIVE (propagated) requested state, not
  # the stored intent: a child re-requested with no explicit state follows its
  # parent and returns to 'started' when the parent restarts, even though the
  # stored row keeps the last forced value. Storing falls back to the previous
  # value, so the two can differ -- deliberately, to mirror the master.
  result['requested_state'] = requested_state or 'started'
  return result


def renameInstance(instance_guid, new_title):
  """Rename an instance -- a single-row title UPDATE, guid untouched. No
  cascade: nothing references titles. Works for shared instances too."""
  n = _write('instance',
    'UPDATE %s SET title=? WHERE instance_guid=?',
    (new_title, instance_guid)).rowcount
  if not n:
    raise NotFoundPartitionFailure(
      'No instance %s to rename' % instance_guid)


def bangInstance(instance_guid):
  """Bump the timestamp of a whole instance tree, scoped by guid."""
  row = getInstanceByGuid(instance_guid)
  if row is None:
    raise NotFoundPartitionFailure('No instance %s to bang' % instance_guid)
  root = row['root_instance_guid'] or row['instance_guid']
  _write('instance',
    'UPDATE %s SET timestamp=?'
    ' WHERE instance_guid=? OR root_instance_guid=?',
    (time.time(), root, root))
  if row['shared']:
    # A shared instance is materialized only by its host partition's slapgrid;
    # bumping the guid's tree alone would be a wire no-op. Bump the host too.
    _touch(row['allocated_computer'], row['allocated_partition'])


def setInstanceConnectionParameters(instance_guid, connection_dict):
  """Store an instance's published connection parameters."""
  row = getInstanceByGuid(instance_guid)
  if row is None:
    raise NotFoundPartitionFailure(
      'No instance %s to set connection parameters' % instance_guid)
  connection_xml = dict2xml(connection_dict)
  if row['connection_xml'] == connection_xml:
    # Unchanged: publishing the same parameters must not bump the host every
    # run (which would make slapgrid reprocess the hosting partition forever).
    return
  _write('instance',
    'UPDATE %s SET connection_xml=? WHERE instance_guid=?',
    (connection_xml, instance_guid))
  if row['shared']:
    _touch(row['allocated_computer'], row['allocated_partition'])


def destroyInstance(instance_guid):
  """Destroy an instance.

  Implements an Alarm_garbageCollectDestroyUnlinkedInstance analogue: if the
  instance has direct children, they are requested destroyed and the deletion
  is refused (raising PartitionDeletionFailure); otherwise the row is deleted.

  For a non-shared instance freeing a host slot, the shared instances hosted on
  that slot are deleted too and the partition is freed -- otherwise a newcomer
  allocated to the recycled slot would inherit the previous tenant's shared
  instances through the slave_instance_list projection.
  """
  row = getInstanceByGuid(instance_guid)
  if row is None:
    raise NotFoundPartitionFailure(
      'No instance %s to destroy' % instance_guid)
  children = execute_db('instance',
    'SELECT * FROM %s WHERE requested_by_instance_guid=?', (instance_guid,))
  # Refuse the destroy while non-shared children exist, BEFORE touching the
  # victim's shared children: a refused destroy must leave the victim (and its
  # slaves) intact.
  non_shared_children = [c for c in children if not c['shared']]
  if non_shared_children:
    _write('instance',
      "UPDATE %s SET requested_state='destroyed'"
      " WHERE requested_by_instance_guid=? AND shared=0", (instance_guid,))
    raise PartitionDeletionFailure(
      'Not destroying yet because this instance has child instances: '
      + ', '.join(sorted(c['title'] for c in non_shared_children)))
  # The destroy proceeds. Shared instances this instance requested are hosted on
  # other slots; they do NOT block destruction (nothing else ever deletes a
  # destroyed shared row, so blocking on them would deadlock teardown). Drop
  # them and reprocess their hosts so they leave those hosts'
  # slave_instance_list projections.
  for c in children:
    if c['shared']:
      _write('instance', 'DELETE FROM %s WHERE instance_guid=?',
        (c['instance_guid'],))
      _touch(c['allocated_computer'], c['allocated_partition'])
  _write('instance', 'DELETE FROM %s WHERE instance_guid=?', (instance_guid,))
  if row['shared']:
    _touch(row['allocated_computer'], row['allocated_partition'])
  else:
    _write('instance',
      'DELETE FROM %s'
      ' WHERE shared=1 AND allocated_computer=? AND allocated_partition=?',
      (row['allocated_computer'], row['allocated_partition']))
    _write('partition',
      "UPDATE %s SET slap_state='free'"
      " WHERE reference=? AND computer_reference=?",
      (row['allocated_partition'], row['allocated_computer']))


def getSlaveInstanceList(computer_reference, partition_reference):
  """Derived slave_instance_list projection for a hosting partition.

  Generated at read time from shared instance rows allocated to the partition,
  in insertion order. Byte-compatible with the v17 blob shape (slapgrid and
  deployed SRs such as rapid-cdn / re6stnet parse these entries). Shared
  instances are NOT given an _instance_guid in the entries."""
  result_list = []
  for row in execute_db('instance',
      'SELECT * FROM %s'
      ' WHERE shared=1 AND allocated_computer=? AND allocated_partition=?'
      ' ORDER BY rowid',
      (computer_reference, partition_reference)):
    entry = {
      'slave_title': row['slave_reference'],
      'slave_reference': row['slave_reference'],
      'slap_software_type': row['software_type'],
    }
    entry.update(decodeSharedParameters(row['xml']))
    result_list.append(entry)
  return result_list


def getRootInstanceList(title=None):
  """Root instances (shared and non-shared), optionally filtered by title."""
  query = "SELECT * FROM %s WHERE root_instance_guid=''"
  args = []
  if title is not None:
    query += ' AND title=?'
    args.append(title)
  return execute_db('instance', query, args)


def getInstanceTreeList(title=None):
  """List of tree-root instance rows, optionally filtered by title."""
  return getRootInstanceList(title=title)


def isRequestToBeForwardedToExternalMaster(parsed_request_dict):
    """
    Check if we HAVE TO forward the request.
    Several cases:
     * The request specifies a master_url in filter_kw
     * The software_release of the request is in a automatic forward list
    """
    master_url = parsed_request_dict['filter_kw'].get('master_url')

    if checkMasterUrl(master_url):
      # Don't allocate the instance locally, but forward to specified master
      return master_url

    software_release = parsed_request_dict['software_release']
    for mutimaster_url, mutimaster_entry in six.iteritems(current_app.config.get('multimaster', {})):
      if software_release in mutimaster_entry['software_release_list']:
        # Don't allocate the instance locally, but forward to specified master
        return mutimaster_url
    return None

def forwardRequestToExternalMaster(master_url, parsed_request_dict):
  """
  Forward instance request to external SlapOS Master.
  """
  master_entry = current_app.config.get('multimaster').get(master_url, {})
  key_file = master_entry.get('key')
  cert_file = master_entry.get('cert')
  if master_url.startswith('https') and (not key_file or not cert_file):
    current_app.logger.warning('External master %s configuration did not specify key or certificate.' % master_url)
    raise ConfigurationError('External master %s configuration did not specify key or certificate.' % master_url)
  if master_url.startswith('https') and not master_url.startswith('https') and (key_file or cert_file):
    current_app.logger.warning('External master %s configuration specifies key or certificate but is using plain http.' % master_url)
    raise ConfigurationError('External master %s configuration specifies key or certificate but is using plain http.' % master_url)

  slap = slapos.slap.slap()
  if key_file:
    slap.initializeConnection(master_url, key_file=key_file, cert_file=cert_file)
  else:
    slap.initializeConnection(master_url)

  partition_reference = parsed_request_dict['partition_reference']

  filter_kw = parsed_request_dict['filter_kw']
  partition_parameter_kw = parsed_request_dict['partition_parameter_kw']

  state = parsed_request_dict['requested_state']
  current_app.logger.info("Forwarding request of %s (state=%s) to %s ", partition_reference, state, master_url)
  current_app.logger.debug("parsed_request_dict: %s", parsed_request_dict)

  if master_entry.get('computer') and master_entry.get('partition'):
    current_app.logger.debug("requesting from partition %s", master_entry)
    # XXX ComputerPartition.request and OpenOrder.request have different signatures
    partition = slap.registerComputerPartition(
        master_entry['computer'],
        master_entry['partition'],
    ).request(
        software_release=parsed_request_dict['software_release'],
        software_type=parsed_request_dict['software_type'],
        partition_reference=partition_reference,
        shared=parsed_request_dict['slave'],
        partition_parameter_kw=partition_parameter_kw,
        filter_kw=filter_kw,
        state=state,
    )
  else:
    filter_kw['source_instance_id'] = partition_reference
    partition = slap.registerOpenOrder().request(
        software_release=parsed_request_dict['software_release'],
        partition_reference=partition_reference,
        partition_parameter_kw=partition_parameter_kw,
        software_type=parsed_request_dict['software_type'],
        filter_kw=filter_kw,
        state=state,
        shared=parsed_request_dict['slave'],
    )

  # Store in database
  if state == 'destroyed':
    execute_db(
      'forwarded_partition_request',
      'DELETE FROM %s WHERE partition_reference = :partition_reference and master_url = :master_url',
      {'partition_reference':partition_reference, 'master_url': master_url})
  else:
    execute_db(
      'forwarded_partition_request',
      'INSERT OR REPLACE INTO %s values(:partition_reference, :master_url)',
      {'partition_reference':partition_reference, 'master_url': master_url})

  # XXX move to other end
  partition._master_url = master_url # type: ignore
  partition._connection_helper = None
  # getSoftwareRelease() must yield a SoftwareRelease object (consumers call
  # .getURI() on it), so wrap the forwarded release URL instead of storing the
  # raw string.
  partition._software_release_document = SoftwareRelease( # type: ignore
      software_release=parsed_request_dict['software_release'],
      computer_guid=partition._computer_id,
  )

  return partition

def checkMasterUrl(master_url):
  """
  Check if master_url doesn't represent ourself, and check if it is whitelisted
  in multimaster configuration.
  """
  if not master_url:
    return False

  if checkIfMasterIsCurrentMaster(master_url):
    # master_url is current server: don't forward
    return False

  master_entry = current_app.config.get('multimaster').get(master_url, None)
  # Check if this master is known
  if not master_entry:
    # Check if it is ourself
    if not master_url.startswith('https') and checkIfMasterIsCurrentMaster(master_url):
      return False
    current_app.logger.warning('External SlapOS Master URL %s is not listed in multimaster list.' % master_url)
    raise ConfigurationError('External SlapOS Master URL %s is not listed in multimaster list.' % master_url)

  return True


def _rowToSoftwareInstance(row):
  """Build the slap_tool SoftwareInstance wire object from an instance row.

  Shared instances carry NO _instance_guid on this wire (an old client's
  getInstanceGuid() on a shared partition must keep its behaviour)."""
  address_list = []
  for address in execute_db('partition_network',
      'SELECT * FROM %s WHERE partition_reference=? AND computer_reference=?',
      (row['allocated_partition'], row['allocated_computer'])):
    address_list.append((address['reference'], address['address']))

  if row['shared']:
    return SoftwareInstance(
      _connection_dict=xml2dict(row['connection_xml']),
      _parameter_dict=decodeSharedParameters(row['xml']),
      slap_computer_id=row['allocated_computer'],
      slap_computer_partition_id=row['allocated_partition'],
      slap_software_release_url=row['software_release'],
      slap_server_url='slap_server_url',
      slap_software_type=row['software_type'],
      ip_list=address_list)

  parameter_dict = xml2dict(row['xml'])
  parameter_dict['timestamp'] = str(row['timestamp'])
  return SoftwareInstance(
    _connection_dict=xml2dict(row['connection_xml']),
    _parameter_dict=parameter_dict,
    connection_xml=row['connection_xml'],
    slap_computer_id=row['allocated_computer'],
    slap_computer_partition_id=row['allocated_partition'],
    slap_software_release_url=row['software_release'],
    slap_server_url='slap_server_url',
    slap_software_type=row['software_type'],
    _instance_guid=row['instance_guid'],
    _requested_state=row['requested_state'] or 'started',
    ip_list=address_list)


def requestInstanceFromDB(requester=None, requester_id='user',
                          software_release=None, software_type=None,
                          partition_reference=None, partition_parameter_kw=None,
                          filter_kw=None, requested_state='started', slave=False):
  """Orchestrate an instance request: frontend-bypass shortcuts and
  external-master forwarding stay here; the local allocation path delegates to
  requestInstance.

  requester is the resolved requesting instance row (or None for a direct user
  request), as identified by identifyRequester and carried in flask.g by the
  blueprint hooks. requester_id is the raw asserted partition id string, used
  only for the multimaster forwarding prefix.
  """
  if partition_parameter_kw is None:
    partition_parameter_kw = {}
  if filter_kw is None:
    filter_kw = {}
  parsed_request_dict = {
    'requester_id': requester_id,
    'software_release': software_release,
    'software_type': software_type,
    'partition_reference': partition_reference,
    'partition_parameter_kw': partition_parameter_kw,
    'filter_kw': filter_kw,
    'requested_state': requested_state,
    'slave': slave,
  }

  if slave:
    # slapproxy cannot request frontends, but we can workaround common cases,
    # so that during tests promises are succesful.
    if not isRequestToBeForwardedToExternalMaster(parsed_request_dict):
      # if client request a "simple" frontend for an URL, we can tell this
      # client to use the URL directly.
      apache_frontend_sr_url_list = (
          'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg',
      )
      if software_release in apache_frontend_sr_url_list \
        and (software_type or '') in ('', OLD_DEFAULT_SOFTWARE_TYPE, DEFAULT_SOFTWARE_TYPE):
        url_parameter = partition_parameter_kw.get('url')
        if url_parameter:
          if request.scheme == 'https':
            # Only handle the secure access if slapproxy is also
            # accessed with secure https
            # to ensure not lowering the connection
            parsed_url_parameter = urlparse(url_parameter)
            # XXX hardcoded http_proxy. set in views.py
            parsed_secure_access_url = urlparse(url_for(
              'httpproxy.proxy_request',
              url_scheme=parsed_url_parameter.scheme,
              url_netloc=parsed_url_parameter.netloc,
              url_path=parsed_url_parameter.path,
              _external=True
            ))
            secure_access_url = parsed_secure_access_url._replace(
              query=parsed_url_parameter.query,
              fragment=parsed_url_parameter.fragment
            ).geturl()
          else:
            # If slaproxy is not accessed with https
            # return the original url
            secure_access_url = url_parameter
            parsed_secure_access_url = urlparse(secure_access_url)
          current_app.logger.warning("Bypassing frontend for %s => %s", parsed_request_dict, url_parameter)
          partition = ComputerPartition('', 'Fake frontend for {}'.format(url_parameter))
          partition.slap_computer_id = ''
          partition.slap_computer_partition_id = ''
          partition._parameter_dict = {}
          partition._connection_dict = {
            'secure_access': secure_access_url,
            'domain': parsed_secure_access_url.netloc,
          }
          return partition
      # another similar case is for KVM frontends. This is used in
      # request-slave-frontend from software/kvm/instance-kvm.cfg.jinja2
      # requested values by 'return' recipe are: url resource port domainname
      kvm_frontend_sr_url_list = (
          'http://git.erp5.org/gitweb/slapos.git/blob_plain/refs/tags/slapos-0.92:/software/kvm/software.cfg',
      )
      if software_release in kvm_frontend_sr_url_list \
          and software_type in ('frontend', ):
        host = partition_parameter_kw.get('host')
        port = partition_parameter_kw.get('port')
        if host and port:
          # host is supposed to be ipv6 without brackets.
          if ':' in host and host[0] != '[':
            host = '[%s]' % host
          url = 'https://%s:%s/' % (host, port)
          current_app.logger.warning("Bypassing KVM VNC frontend for %s => %s", parsed_request_dict, url)
          partition = ComputerPartition('', 'Fake KVM VNC frontend for {}'.format(url))
          partition.slap_computer_id = ''
          partition.slap_computer_partition_id = ''
          partition._parameter_dict = {}
          partition._connection_dict = {
            'url': url,
            'domainname': host,
            'port': port,
            'path': '/'
          }
          return partition

  # Decide forwarding only for a request not already allocated locally: an
  # instance already present in this request scope stays local (and is updated).
  root_guid, _ = requesterScope(requester)
  already_local = execute_db('instance',
    'SELECT instance_guid FROM %s WHERE title=? AND root_instance_guid=? AND shared=?',
    (partition_reference, root_guid, 1 if slave else 0), one=True)
  if not already_local:
    external_master_url = isRequestToBeForwardedToExternalMaster(parsed_request_dict)
    if external_master_url:
      return forwardRequestToExternalMaster(external_master_url, {
        # Prefix instance reference with id of requester (partition id (ends
        # with a digit) or 'user' (cannot be a partition id))
        'partition_reference': '%s_%s' % (requester_id, partition_reference),
        'software_release': software_release,
        'software_type': software_type,
        'partition_parameter_kw': partition_parameter_kw,
        'filter_kw': filter_kw,
        # Note: currently ignored for slave instance (slave instances
        # are always started).
        'requested_state': requested_state,
        # Is it a slave instance?
        'slave': slave,
      })

  # By default, ALWAYS request instance on default computer
  filter_kw.setdefault('computer_guid', current_app.config['computer_id'])
  # Return the raw instance row for the local-allocation path. The wire shape is
  # the caller's concern: slap_tool wraps it with _rowToSoftwareInstance (which
  # omits _instance_guid for shared rows), json_rpc serializes the row directly
  # (publishing instance_guid for shared and non-shared alike). None is returned
  # when a first-ever shared request with state 'destroyed' allocates nothing.
  return requestInstance(requester, partition_reference, software_release,
                         software_type, partition_parameter_kw, filter_kw,
                         requested_state, slave)


def freePartitionFromDB(computer_partition_id, computer_id):
  """Destroy the non-shared instance allocated to a partition slot.

  Legacy entry point addressing an instance by its partition coordinates;
  resolves to the instance row and delegates to destroyInstance (which also
  drops the shared instances hosted on the freed slot and frees it)."""
  row = execute_db('instance',
    'SELECT * FROM %s'
    ' WHERE allocated_computer=? AND allocated_partition=? AND shared=0',
    (computer_id, computer_partition_id), one=True)
  if row is None:
    raise NotFoundPartitionFailure(
      "Unknown partition %r on %r" % (computer_partition_id, computer_id))
  destroyInstance(row['instance_guid'])
