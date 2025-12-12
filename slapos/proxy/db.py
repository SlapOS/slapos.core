import time

import slapos
from slapos.slap.slap import ComputerPartition, SoftwareInstance
from slapos.util import loads, dumps
from slapos.util import bytes2str, \
    xml2dict, dict2xml

import six
from six.moves.urllib.parse import urlparse

from flask import g, current_app, request, url_for
from slapos.proxy.db_version import DB_VERSION
from slapos.slap.slap import DEFAULT_SOFTWARE_TYPE, OLD_DEFAULT_SOFTWARE_TYPE

class NotFoundPartitionFailure(Exception):
  pass

class PartitionDeletionFailure(Exception):
  pass

class AllocationFailure(Exception):
  pass

class ConfigurationError(Exception):
  pass


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
  slap = slapos.slap.slap()
  slap.initializeConnection(master_url)
  try:
    return current_app.config['run_id'] == bytes2str(slap._connection_helper.GET('/getRunId'))
  except Exception:
    return False


def formatFromDB(computer_reference, partition_list,
                 computer_address=None,
                 computer_netmask=None):
  execute_db('computer', 'INSERT OR REPLACE INTO %s values(?, ?, ?)',
             (computer_reference, computer_address, computer_netmask))

  # remove references to old partitions.
  execute_db(
    'partition',
    'DELETE FROM %s WHERE computer_reference = ? and reference not in ({})'.format(
      ','.join('?' * len(partition_list)) # Create as many placeholder as partitions requested
    ),
    # Prepare arguments : first is for computer_reference, followed by the same of the partitions
    [computer_reference] + [x['partition_id'] for x in partition_list]
  )

  execute_db(
    'slave',
    'DELETE FROM %s WHERE computer_reference = ? and hosted_by not in ({})'.format(
      ','.join('?' * len(partition_list)) # Create as many placeholder as partitions requested
    ),
    # Prepare arguments : first is for computer_reference, followed by the same of the partitions
    [computer_reference] + [x['partition_id'] for x in partition_list]
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
         ip['ip-address'], ip['netmask'])
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


def freePartitionFromDB(computer_partition_id, computer_id):
  partition = getPartitionFromDB(computer_partition_id, computer_id)
  if not partition:
    raise NotFoundPartitionFailure("Unknown partition %r on %r" % (computer_partition_id, computer_id))

  # Implement something similar to Alarm_garbageCollectDestroyUnlinkedInstance, if root instance
  # is destroyed, we request child instances in deleted state
  if not partition['requested_by']:
    args = partition['partition_reference'],
    child_partitions = execute_db(
      'partition',
      'SELECT partition_reference'
      ' FROM %s WHERE requested_by=?'
      ' ORDER BY partition_reference',
      args)
    if child_partitions:
      execute_db(
        'partition',
        "UPDATE %s SET requested_state='destroyed' WHERE requested_by=?",
        args)
      raise PartitionDeletionFailure("Not destroying yet because this partition has child partitions: "
                                     + ', '.join(p['partition_reference'] for p in child_partitions))

  execute_db(
    "partition",
    "UPDATE %s SET"
      " slap_state='free',"
      " software_release=NULL,"
      " xml=NULL,"
      " connection_xml=NULL,"
      " slave_instance_list=NULL,"
      " software_type=NULL,"
      " partition_reference=NULL,"
      " requested_by='',"
      " requested_state='started'"
    " WHERE reference=? AND computer_reference=?",
    (computer_partition_id, computer_id))

def getPartitionFromDB(reference, computer_reference):
  partition = execute_db('partition',
    'SELECT * FROM %s WHERE reference=? AND computer_reference=?',
    (reference, computer_reference), one=True)
  if partition:
    return partition
  current_app.logger.warning("Nonexisting partition %r on %r. Known are %s",
    reference, computer_reference,
    execute_db("partition", "select reference, requested_by from %s"))



def getAllocatedInstance(partition_reference, requested_by=''):
  """
  Look for existence of instance, if so return the
  corresponding partition dict, else return None
  """
  return execute_db('partition',
    'SELECT * FROM %s WHERE partition_reference=? AND requested_by=?',
    (partition_reference, requested_by), one=True)

def getAllocatedSlaveInstance(slave_reference, requested_computer_id):
  """
  Look for existence of instance, if so return the
  corresponding partition dict, else return None

  # XXX: Scope currently depends on instance which requests slave.
  # Meaning that two different instances requesting the same slave will
  # result in two different allocated slaves.
  """
  return execute_db('slave',
    'SELECT * FROM %s WHERE reference=? AND computer_reference=?',
    (slave_reference, requested_computer_id), one=True)

def requestSlave(software_release, software_type, partition_reference, requester_id, requested_by, partition_parameter_kw, filter_kw, requested_state):
  """
  Function to organise link between slave and master.
  Slave information are stored in places:
  1. slave table having information such as slave reference,
      connection information to slave (given by slave master),
      hosted_by and asked_by reference.
  2. A dictionary in slave_instance_list of selected slave master
      in which are stored slave_reference, software_type, slave_title and
      partition_parameter_kw stored as individual keys.
  """
  requested_computer_id = filter_kw['computer_guid']
  instance_xml = dict2xml(partition_parameter_kw)

  # We will search for a master corresponding to request
  args = []
  a = args.append
  q = 'SELECT * FROM %s WHERE software_release=? and computer_reference=?'
  a(software_release)
  a(requested_computer_id)
  if software_type:
    q += ' AND software_type=?'
    a(software_type)
  if 'instance_guid' in filter_kw:
    q += ' AND reference=?'
    # instance_guid should be like: %s-%s % (requested_computer_id, partition_id)
    # But code is convoluted here, so we check
    instance_guid = filter_kw['instance_guid']
    if instance_guid.startswith(requested_computer_id):
      a(instance_guid[len(requested_computer_id) + 1:])
    else:
      a(instance_guid)

  partition = execute_db('partition', q, args, one=True)
  if partition is None:
    current_app.logger.warning('No partition corresponding to slave request: %s' % args)
    raise AllocationFailure('No partition corresponding to slave request: %s' % args)

  # We set slave dictionary as described in docstring
  new_slave = {}
  slave_reference = requested_by + '_' + partition_reference
  new_slave['slave_title'] = slave_reference
  new_slave['slap_software_type'] = software_type
  new_slave['slave_reference'] = slave_reference

  for key in partition_parameter_kw:
    new_slave[key] = partition_parameter_kw[key]

  # Add slave to partition slave_list if not present else replace information
  slave_updated_or_added = False
  slave_instance_list = partition['slave_instance_list']
  if requested_state == 'destroyed':
    if slave_instance_list:
      slave_instance_list = loads(slave_instance_list.encode('utf-8'))
    before_count = len(slave_instance_list)
    slave_instance_list = [x for x in slave_instance_list if x['slave_reference'] != slave_reference]
    if before_count != len(slave_instance_list):
      slave_updated_or_added = True
  else:
    if slave_instance_list:
      slave_instance_list = loads(slave_instance_list.encode('utf-8'))
      for i, x in enumerate(slave_instance_list):
        if x['slave_reference'] == slave_reference:
          if slave_instance_list[i] != new_slave:
            slave_instance_list[i] = new_slave
            slave_updated_or_added = True
          break
      else:
        slave_instance_list.append(new_slave)
        slave_updated_or_added = True
    else:
      slave_instance_list = [new_slave]
      slave_updated_or_added = True

  q += ' WHERE reference=? AND computer_reference=?'
  a(partition['reference'])
  a(partition['computer_reference'])
  # Update slave_instance_list in database
  args = []
  a = args.append
  q = 'UPDATE %s SET slave_instance_list=?'
  a(bytes2str(dumps(slave_instance_list)))
  if slave_updated_or_added:
    timestamp = time.time()
    q += ', timestamp=?'
    a(timestamp)
  q += ' WHERE reference=? and computer_reference=?'
  a(partition['reference'])
  a(requested_computer_id)
  execute_db('partition', q, args)
  partition = getPartitionFromDB(partition['reference'], requested_computer_id)

  # Add slave to slave table if not there
  slave = execute_db('slave', 'SELECT * FROM %s WHERE reference=? and computer_reference=?',
                     [slave_reference, requested_computer_id], one=True)
  if slave is None:
    execute_db('slave',
               'INSERT INTO %s (reference,computer_reference,asked_by,hosted_by) values(?,?,?,?)',
               (slave_reference, requested_computer_id, requested_by, partition['reference']))
    slave = execute_db('slave', 'SELECT * FROM %s WHERE reference=? and computer_reference=?',
                       [slave_reference, requested_computer_id], one=True)

  address_list = []
  for address in execute_db('partition_network',
                            'SELECT * FROM %s WHERE partition_reference=? and computer_reference=?',
                            [partition['reference'], partition['computer_reference']]):
    address_list.append((address['reference'], address['address']))

  # XXX it should be ComputerPartition, not a SoftwareInstance
  return SoftwareInstance(
    _connection_dict=xml2dict(slave['connection_xml']),
    _parameter_dict=xml2dict(instance_xml),
    slap_computer_id=partition['computer_reference'],
    slap_computer_partition_id=slave['hosted_by'],
    slap_software_release_url=partition['software_release'],
    slap_server_url='slap_server_url',
    slap_software_type=partition['software_type'],
    ip_list=address_list)

def requestNotSlave(software_release, software_type, partition_reference,
                    requester_id, requested_by, partition_parameter_kw, filter_kw,
                    requested_state):
  instance_xml = dict2xml(partition_parameter_kw)
  requested_computer_id = filter_kw['computer_guid']

  partition = getAllocatedInstance(partition_reference, requested_by)
  args = []
  a = args.append
  q = 'UPDATE %s SET slap_state="busy"'

  if partition is None:
    partition = execute_db('partition',
        'SELECT * FROM %s WHERE slap_state="free" and computer_reference=?',
        [requested_computer_id], one=True)
    if partition is None:
      current_app.logger.warning('No more free computer partition')
      raise AllocationFailure('No free computer partition found for: %s' % partition_reference)
    if partition_reference:
      q += ' ,partition_reference=?'
      a(partition_reference)
    if requested_by:
      q += ' ,requested_by=?'
      a(requested_by)
    if not software_type:
      software_type = DEFAULT_SOFTWARE_TYPE
  else:
    if requested_by:
      root_partition = getAllocatedInstance(requested_by)
      if root_partition and root_partition['requested_state'] != "started":
        # propagate parent state to child
        # child can be stopped or destroyed while parent is started
        requested_state = root_partition['requested_state']

  timestamp = partition['timestamp']
  changed = timestamp is None
  for k, v in (('requested_state', requested_state or
                                   partition['requested_state']),
               ('software_release', software_release),
               ('software_type', software_type),
               ('xml', instance_xml)):
    if partition[k] != v:
      q += ', %s=?' % k
      a(v)
      changed = True

  if changed:
    timestamp = time.time()
    q += ', timestamp=?'
    a(timestamp)

  q += ' WHERE reference=? AND computer_reference=?'
  a(partition['reference'])
  a(partition['computer_reference'])

  execute_db('partition', q, args)
  partition = getPartitionFromDB(partition['reference'],
                                 partition['computer_reference'])
  address_list = []
  for address in execute_db('partition_network', 'SELECT * FROM %s WHERE partition_reference=?', [partition['reference']]):
    address_list.append((address['reference'], address['address']))

  # XXX it should be ComputerPartition, not a SoftwareInstance
  parameter_dict = xml2dict(partition['xml'])
  parameter_dict['timestamp'] = str(partition['timestamp'])
  return SoftwareInstance(
    _connection_dict=xml2dict(partition['connection_xml']),
    _parameter_dict=parameter_dict,
    connection_xml=partition['connection_xml'],
    slap_computer_id=partition['computer_reference'],
    slap_computer_partition_id=partition['reference'],
    slap_software_release_url=partition['software_release'],
    slap_server_url='slap_server_url',
    slap_software_type=partition['software_type'],
    _instance_guid='%(computer_reference)s-%(reference)s' % partition,
    _requested_state=requested_state or 'started',
    ip_list=address_list)

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
  partition._software_release_document = parsed_request_dict['software_release'] # type: ignore

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

def requestInstanceFromDB(slave=None, **parsed_request_dict):
  # Check first if instance is already allocated
  if slave:
    # slapproxy cannot request frontends, but we can workaround common cases,
    # so that during tests promises are succesful.
    if not isRequestToBeForwardedToExternalMaster(parsed_request_dict):
      # if client request a "simple" frontend for an URL, we can tell this
      # client to use the URL directly.
      apache_frontend_sr_url_list = (
          'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg',
      )
      if parsed_request_dict['software_release'] in apache_frontend_sr_url_list \
        and parsed_request_dict.get('software_type', '') in ('', OLD_DEFAULT_SOFTWARE_TYPE, DEFAULT_SOFTWARE_TYPE):
        url_parameter = parsed_request_dict['partition_parameter_kw'].get('url')
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
      if parsed_request_dict['software_release'] in kvm_frontend_sr_url_list \
          and parsed_request_dict.get('software_type') in ('frontend', ):
        host = parsed_request_dict['partition_parameter_kw'].get('host')
        port = parsed_request_dict['partition_parameter_kw'].get('port')
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

    # XXX: concat is unreliable
    slave_reference = parsed_request_dict['requested_by'] + '_' \
                    + parsed_request_dict['partition_reference']
    requested_computer_id = parsed_request_dict['filter_kw'].get('computer_guid', current_app.config['computer_id'])
    matching_partition = getAllocatedSlaveInstance(slave_reference, requested_computer_id)
  else:
    matching_partition = getAllocatedInstance(
      parsed_request_dict['partition_reference'],
      parsed_request_dict['requested_by'])

  if not matching_partition:
    # Instance is not yet allocated: try to do it.
    external_master_url = isRequestToBeForwardedToExternalMaster(parsed_request_dict)
    if external_master_url:
      return forwardRequestToExternalMaster(external_master_url, {
        # Prefix instance reference with id of requester (partition id (ends with a digit) or 'user' (cannot be a partition id))
        'requested_by': parsed_request_dict['requested_by'],
        'partition_reference': '%s_%s' % (parsed_request_dict['requester_id'], parsed_request_dict['partition_reference']),
        'software_release': parsed_request_dict['software_release'],
        'software_type': parsed_request_dict['software_type'],
        'partition_parameter_kw': parsed_request_dict['partition_parameter_kw'],
        'filter_kw': parsed_request_dict['filter_kw'],
        # Note: currently ignored for slave instance (slave instances
        # are always started).
        'requested_state': parsed_request_dict['requested_state'],
        # Is it a slave instance?
        'slave': slave
      })
    # XXX add support for automatic deployment on specific node depending on available SR and partitions on each Node.
    # Note: It only deploys on default node if SLA not specified
    # XXX: split request and request slave into different update/allocate functions and simplify.

  # By default, ALWAYS request instance on default computer
  parsed_request_dict['filter_kw'].setdefault('computer_guid', current_app.config['computer_id'])
  if slave:
    software_instance = requestSlave(**parsed_request_dict)
  else:
    software_instance = requestNotSlave(**parsed_request_dict)
  return software_instance


def bangInstanceFromDB(partition_reference, requested_by):
  execute_db('partition',
    "UPDATE %s SET timestamp=?"
    " WHERE (partition_reference=? AND requested_by=?) OR requested_by=?",
    (time.time(), partition_reference, requested_by, partition_reference))


def getRootPartitionList(title=None):
  query = "SELECT * FROM %s WHERE slap_state!='free' AND requested_by=''"
  args = []
  if title:
    query += ' AND partition_reference=?'
    args.append(title)
  return execute_db('partition', query, args)

def getRootSharedList(title=None):
  query = "SELECT * FROM %s WHERE asked_by=''"
  args = []
  if title:
    query += ' AND reference=?'
    args.append('_' + title)
  return execute_db('slave', query, args)

def getInstanceTreeList(title=None):
  return [getRootPartitionList(), getRootSharedList()]
