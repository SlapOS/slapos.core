# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2010, 2011, 2012, 2013, 2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import random
import string
import time
import re
import os
from datetime import datetime
from slapos.slap.slap import Computer, ComputerPartition, \
    SoftwareRelease, SoftwareInstance, NotFoundError
from slapos.proxy.db_version import DB_VERSION
import slapos.slap
from slapos.util import bytes2str, unicode2str, sqlite_connect, \
    xml2dict, dict2xml

from flask import g, Flask, request, abort, redirect, url_for
from slapos.util import loads, dumps

import six
from six.moves import range
from six.moves.urllib.parse import urlparse, unquote, urljoin

app = Flask(__name__)

EMPTY_DICT_XML = dumps({})

class UnauthorizedError(Exception):
  pass


def partitiondict2partition(partition):
  slap_partition = ComputerPartition(partition['computer_reference'],
      partition['reference'])
  slap_partition._software_release_document = None
  slap_partition._requested_state = 'destroyed'
  slap_partition._need_modification = 0
  slap_partition._instance_guid = '%(computer_reference)s-%(reference)s' \
    % partition

  root_partition = getRootPartition(partition['reference'])

  if partition['software_release']:
    slap_partition._need_modification = 1
    slap_partition._requested_state = partition['requested_state']
    slap_partition._parameter_dict = xml2dict(partition['xml'])
    address_list = []
    full_address_list = []
    for address in execute_db('partition_network',
                              'SELECT * FROM %s WHERE partition_reference=? AND computer_reference=?',
                              [partition['reference'], partition['computer_reference']]):
      address_list.append((address['reference'], address['address']))
    slap_partition._parameter_dict['ip_list'] = address_list
    slap_partition._parameter_dict['full_address_list'] = full_address_list
    slap_partition._parameter_dict['slap_software_type'] = \
        partition['software_type']
    slap_partition._parameter_dict['instance_title'] = \
        partition['partition_reference']
    slap_partition._parameter_dict['root_instance_title'] = \
        root_partition['partition_reference']
    slap_partition._parameter_dict['slap_computer_id'] = \
        partition['computer_reference']
    slap_partition._parameter_dict['slap_computer_partition_id'] = \
        partition['reference']
    slap_partition._parameter_dict['slap_software_release_url'] = \
        partition['software_release']

    if partition['slave_instance_list'] is not None:
      slap_partition._parameter_dict['slave_instance_list'] = \
          loads(partition['slave_instance_list'].encode('utf-8'))
    else:
      slap_partition._parameter_dict['slave_instance_list'] = []
    timestamp = partition['timestamp']
    if timestamp:
      slap_partition._parameter_dict['timestamp'] = str(timestamp)
    slap_partition._connection_dict = xml2dict(partition['connection_xml'])
    slap_partition._software_release_document = SoftwareRelease(
      software_release=partition['software_release'],
      computer_guid=partition['computer_reference'])

  return slap_partition


def execute_db(table, query, args=(), one=False, db_version=None, db=None):
  if not db:
    db = g.db
  if not db_version:
    db_version = DB_VERSION
  query = query % (table + db_version,)
  app.logger.debug(query)
  try:
    cur = db.execute(query, args)
  except:
    app.logger.error('There was some issue during processing query %r on table %r with args %r' % (query, table, args))
    raise
  rv = [dict((cur.description[idx][0], value)
    for idx, value in enumerate(row)) for row in cur.fetchall()]
  return (rv[0] if rv else None) if one else rv


def connect_db():
  return sqlite_connect(app.config['DATABASE_URI'])

def _getTableList():
  return g.db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name").fetchall()

def _getCurrentDatabaseSchemaVersion():
  """
  Return version of database schema.
  As there is no actual definition of version, analyse
  name of all tables (containing version) and take the
  highest version (as several versions can live in the db).
  """
  # XXX: define an actual version and proper migration/repair procedure.
  version = -1
  for table_name in _getTableList():
    try:
      table_version = int(table_name[0][-2:])
    except ValueError:
      table_version = int(table_name[0][-1:])
    if table_version > version:
      version = table_version
  return str(version)

def _upgradeDatabaseIfNeeded():
  """
  Analyses current database compared to defined schema,
  and adapt tables/data it if needed.
  """
  current_schema_version = _getCurrentDatabaseSchemaVersion()
  # If version of current database is not old, do nothing
  if current_schema_version == DB_VERSION:
    return

  previous_table_list = _getTableList()
  # first, make a backup of current database
  if current_schema_version != '-1':
    backup_file_name = "{}-backup-{}to{}-{}.sql".format(
        app.config['DATABASE_URI'],
        current_schema_version,
        DB_VERSION,
        datetime.now().isoformat())
    app.logger.info(
        'Old schema detected: Creating a backup of current tables at %s',
        backup_file_name
    )
    with open(backup_file_name, 'w') as f:
      for line in g.db.iterdump():
          f.write('%s\n' % line)

  with app.open_resource('schema.sql', 'r') as f:
    schema = f.read() % dict(version=DB_VERSION, computer=app.config['computer_id'])
  g.db.cursor().executescript(schema)
  g.db.commit()

  if current_schema_version == '-1':
    return

  # Migrate all data to new tables
  app.logger.info('Old schema detected: Migrating old tables...')
  table_list = ('software', 'computer', 'partition', 'slave', 'partition_network')
  if int(current_schema_version) >= 11:
    table_list += ('forwarded_partition_request',)
  if int(current_schema_version) >= 15:
    table_list += ('local_software_release_root',)
  for table in table_list:
    for row in execute_db(table, 'SELECT * from %s', db_version=current_schema_version):
      columns = ', '.join(row.keys())
      placeholders = ':'+', :'.join(row.keys())
      query = 'INSERT INTO %s (%s) VALUES (%s)' % ('%s', columns, placeholders)
      execute_db(table, query, row)
  # then drop old tables
  for previous_table in previous_table_list:
    g.db.execute("DROP table %s" % previous_table)
  g.db.commit()

def _updateLocalSoftwareReleaseRootPathIfNeeded():
  """
  Update the local software release root path if it changed,
  and rebase all URLs in the database relatively to the new path.
  """
  # Retrieve the current root path and replace it with the new one
  current_root_path = execute_db('local_software_release_root', 'SELECT * from %s', one=True)['path'] or os.sep
  new_root_path = app.config['local_software_release_root'] or os.sep
  execute_db('local_software_release_root', 'UPDATE %s SET path=?', [new_root_path])
  # Check whether one is the same as or a subpath of the other
  if current_root_path == new_root_path:
    return
  relpath = os.path.relpath(new_root_path, current_root_path)
  if not relpath.startswith(os.pardir + os.sep):
    app.logger.info('Do not rebase any URLs because %s is a subpath of %s', new_root_path, current_root_path)
    return
  elif os.path.basename(relpath) == os.pardir:
    app.logger.info('Do not rebase any URLs because %s is a superpath of %s', new_root_path, current_root_path)
    return
  # Backup the database before migrating
  database_path = app.config['DATABASE_URI']
  backup_path = database_path + "-backup-%s.sql" % datetime.now().isoformat()
  app.logger.info("Backuping database to %s", backup_path)
  with open(backup_path, 'w') as f:
    for line in g.db.iterdump():
      f.write('%s\n' % line)
  # Rebase all URLs relative to the new root path
  app.logger.info('Rebase URLs on local software release root path')
  app.logger.info('Old root path: %s', current_root_path)
  app.logger.info('New root path: %s', new_root_path)
  def migrate_url(url):
    app.logger.debug('Examining URL %s', url)
    if not url or urlparse(url).scheme:
      app.logger.debug('  Do not rebase because it is not a path')
      return url
    rel = os.path.relpath(url, current_root_path)
    if rel.startswith(os.pardir + os.sep):
      app.logger.debug('  Do not rebase because it is not a subpath of %s', current_root_path)
      return url
    new = os.path.join(new_root_path, rel)
    if not os.path.isfile(new) and os.path.isfile(url):
      app.logger.debug('  Do not rebase because it refers to an existing file but %s does not', new)
      return url
    app.logger.debug('  Migrate to rebased URL %s', new)
    return new
  g.db.create_function('migrate_url', 1, migrate_url)
  execute_db('software', 'UPDATE %s SET url=migrate_url(url)')
  execute_db('partition', 'UPDATE %s SET software_release=migrate_url(software_release)')

is_schema_already_executed = False
@app.before_request
def before_request():
  g.db = connect_db()
  global is_schema_already_executed
  if not is_schema_already_executed:
    _upgradeDatabaseIfNeeded()
    _updateLocalSoftwareReleaseRootPathIfNeeded()
    is_schema_already_executed = True


@app.after_request
def after_request(response):
  g.db.commit()
  g.db.close()
  return response

@app.route('/getComputerInformation', methods=['GET'])
def getComputerInformation():
  # Kept only for backward compatiblity
  return getFullComputerInformation()

@app.route('/getFullComputerInformation', methods=['GET'])
def getFullComputerInformation():
  computer_id = request.args['computer_id']
  computer_list = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_id])
  if len(computer_list) != 1:
    # Backward compatibility
    if computer_id != app.config['computer_id']:
      raise NotFoundError('%s is not registered.' % computer_id)
  slap_computer = Computer(computer_id)
  slap_computer._software_release_list = []
  for sr in execute_db('software', 'select * from %s WHERE computer_reference=?', [computer_id]):
    software_release = SoftwareRelease(
        software_release=sr['url'],
        computer_guid=computer_id)
    software_release._requested_state = sr['requested_state']
    slap_computer._software_release_list.append(software_release)
  slap_computer._computer_partition_list = []
  for partition in execute_db('partition', 'SELECT * FROM %s WHERE computer_reference=?', [computer_id]):
    slap_computer._computer_partition_list.append(partitiondict2partition(
      partition))
  return dumps(slap_computer)

@app.route('/setComputerPartitionConnectionXml', methods=['POST'])
def setComputerPartitionConnectionXml():
  slave_reference = request.form.get('slave_reference', None)
  computer_partition_id = unicode2str(request.form['computer_partition_id'])
  computer_id = unicode2str(request.form['computer_id'])
  connection_xml = dict2xml(loads(request.form['connection_xml'].encode('utf-8')))
  if not slave_reference or slave_reference == 'None':
    query = 'UPDATE %s SET connection_xml=? WHERE reference=? AND computer_reference=?'
    argument_list = [connection_xml, computer_partition_id, computer_id]
    execute_db('partition', query, argument_list)
    # Update timestamp of parent partition.
    requested_by = execute_db('partition',
      'SELECT requested_by FROM %s WHERE reference=? AND computer_reference=?',
      (computer_partition_id, computer_id), one=True)['requested_by']
  else:
    query = 'UPDATE %s SET connection_xml=? , hosted_by=? WHERE reference=?'
    argument_list = [connection_xml, computer_partition_id, slave_reference]
    execute_db('slave', query, argument_list)
  return 'done'

@app.route('/buildingSoftwareRelease', methods=['POST'])
def buildingSoftwareRelease():
  return 'Ignored'

@app.route('/destroyedSoftwareRelease', methods=['POST'])
def destroyedSoftwareRelease():
  execute_db(
    'software',
    'DELETE FROM %s WHERE url = ? and computer_reference=? ',
    [request.form['url'], request.form['computer_id']])
  return 'OK'

@app.route('/availableSoftwareRelease', methods=['POST'])
def availableSoftwareRelease():
  return 'Ignored'

@app.route('/softwareReleaseError', methods=['POST'])
def softwareReleaseError():
  return 'Ignored'

@app.route('/softwareInstanceError', methods=['POST'])
def softwareInstanceError():
  return 'Ignored'

@app.route('/softwareInstanceBang', methods=['POST'])
def softwareInstanceBang():
  partition_list = [getRootPartition(
    unicode2str(request.form['computer_partition_id']))['reference']]
  # Now that we have the root partition, browse recursively
  # to update the timestamp of all partitions in the instance.
  now = time.time()
  while True:
    try:
      partition_id = partition_list.pop()
    except IndexError:
      return 'OK'
    execute_db('partition',
      "UPDATE %s SET timestamp=? WHERE reference=?", (now, partition_id))
    partition_list += (partition['reference'] for partition in execute_db(
      'partition', "SELECT reference FROM %s WHERE requested_by=?",
      (partition_id,)))

@app.route('/startedComputerPartition', methods=['POST'])
def startedComputerPartition():
  return 'Ignored'

@app.route('/stoppedComputerPartition', methods=['POST'])
def stoppedComputerPartition():
  return 'Ignored'

@app.route('/destroyedComputerPartition', methods=['POST'])
def destroyedComputerPartition():
  if not (request.form['computer_partition_id'] and request.form['computer_id']):
    raise ValueError("computer_partition_id and computer_id are required")

  # Implement something similar to Alarm_garbageCollectDestroyUnlinkedInstance, if root instance
  # is destroyed, we request child instances in deleted state
  execute_db(
      'partition',
      'UPDATE %s SET requested_state="destroyed" where requested_by=? and computer_reference=?',
      [request.form['computer_partition_id'], request.form['computer_id']])

  non_destroyed_child_partitions = [
    p['reference'] for p in execute_db(
      'partition',
      'SELECT reference FROM %s WHERE requested_by=? AND computer_reference=?',
      [request.form['computer_partition_id'], request.form['computer_id']])]
  if non_destroyed_child_partitions:
    return "Not destroying yet because this partition has child partitions: %s" % (
        ', '.join(non_destroyed_child_partitions))

  execute_db(
    'partition',
    'UPDATE %s SET '
    '  slap_state="free",'
    '  software_release=NULL,'
    '  xml=NULL,'
    '  connection_xml=NULL,'
    '  slave_instance_list=NULL,'
    '  software_type=NULL,'
    '  partition_reference=NULL,'
    '  requested_by=NULL,'
    '  requested_state="started"'
    'WHERE reference=? AND computer_reference=? ',
    [request.form['computer_partition_id'], request.form['computer_id']])
  return 'OK'

@app.route('/useComputer', methods=['POST'])
def useComputer():
  return 'Ignored'

@app.route('/loadComputerConfigurationFromXML', methods=['POST'])
def loadComputerConfigurationFromXML():
  xml = request.form['xml']
  computer_dict = loads(xml.encode('utf-8'))
  execute_db('computer', 'INSERT OR REPLACE INTO %s values(:reference, :address, :netmask)',
             computer_dict)

  # remove references to old partitions.
  execute_db(
    'partition',
    'DELETE FROM %s WHERE computer_reference = ? and reference not in ({})'.format(
      ','.join('?' * len(computer_dict['partition_list'])) # Create as many placeholder as partitions requested
    ),
    # Prepare arguments : first is for computer_reference, followed by the same of the partitions
    [computer_dict['reference']] + [x['reference'] for x in computer_dict['partition_list']]
  )
  execute_db('partition_network', 'DELETE FROM %s WHERE computer_reference = :reference', computer_dict)

  for partition in computer_dict['partition_list']:
    partition['computer_reference'] = computer_dict['reference']
    execute_db('partition', 'INSERT OR IGNORE INTO %s (reference, computer_reference) values(:reference, :computer_reference)', partition)
    for address in partition['address_list']:
      # keep "or partition['reference']" for backward compatibility in webrunner
      address['reference'] = partition['tap']['name'] or partition['reference']
      address['partition_reference'] = partition['reference']
      address['computer_reference'] = partition['computer_reference']
      execute_db('partition_network', 'INSERT OR REPLACE INTO %s (reference, partition_reference, computer_reference, address, netmask) values(:reference, :partition_reference, :computer_reference, :addr, :netmask)', address)

  return 'done'

@app.route('/registerComputerPartition', methods=['GET'])
def registerComputerPartition():
  computer_reference = unicode2str(request.args['computer_reference'])
  computer_partition_reference = unicode2str(request.args['computer_partition_reference'])
  partition = execute_db('partition', 'SELECT * FROM %s WHERE reference=? and computer_reference=?',
      [computer_partition_reference, computer_reference], one=True)
  if partition is None:
    raise UnauthorizedError
  return dumps(partitiondict2partition(partition))

@app.route('/supplySupply', methods=['POST'])
def supplySupply():
  url = request.form['url']
  computer_id = request.form['computer_id']
  state = request.form['state']
  if state not in ('available', 'destroyed'):
    raise ValueError("Wrong state %s" % state)

  execute_db(
    'software',
    'INSERT OR REPLACE INTO %s VALUES(?, ?, ?)',
    [url, computer_id, state])

  return 'Supplied %r to be %s' % (url, state)


@app.route('/requestComputerPartition', methods=['POST'])
def requestComputerPartition():
  parsed_request_dict = parseRequestComputerPartitionForm(request.form)
  # Is it a slave instance?
  slave = loads(request.form.get('shared_xml', EMPTY_DICT_XML).encode('utf-8'))

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
        and parsed_request_dict.get('software_type', '') in ('', 'RootSoftwareInstance', 'default'):
        url = parsed_request_dict['partition_parameter_kw'].get('url')
        if url:
          app.logger.warning("Bypassing frontend for %s => %s", parsed_request_dict, url)
          partition = ComputerPartition('', 'Fake frontend for {}'.format(url))
          partition.slap_computer_id = ''
          partition.slap_computer_partition_id = ''
          partition._parameter_dict = {}
          partition._connection_dict = {
            'secure_access': url,
            'domain': urlparse(url).netloc,
          }
          return dumps(partition)
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
          app.logger.warning("Bypassing KVM VNC frontend for %s => %s", parsed_request_dict, url)
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
          return dumps(partition)

    # XXX: change schema to include a simple "partition_reference" which
    # is name of the instance. Then, no need to do complex search here.
    slave_reference = parsed_request_dict['partition_id'] + '_' + parsed_request_dict['partition_reference']
    requested_computer_id = parsed_request_dict['filter_kw'].get('computer_guid', app.config['computer_id'])
    matching_partition = getAllocatedSlaveInstance(slave_reference, requested_computer_id)
  else:
    matching_partition = getAllocatedInstance(parsed_request_dict['partition_reference'])

  if matching_partition:
    # Then the instance is already allocated, just update it
    # XXX: split request and request slave into different update/allocate functions and simplify.
    # By default, ALWAYS request instance on default computer
    parsed_request_dict['filter_kw'].setdefault('computer_guid', app.config['computer_id'])
    if slave:
      software_instance = requestSlave(**parsed_request_dict)
    else:
      software_instance = requestNotSlave(**parsed_request_dict)
  else:
    # Instance is not yet allocated: try to do it.
    external_master_url = isRequestToBeForwardedToExternalMaster(parsed_request_dict)
    if external_master_url:
      return forwardRequestToExternalMaster(external_master_url, request.form)
    # XXX add support for automatic deployment on specific node depending on available SR and partitions on each Node.
    # Note: It only deploys on default node if SLA not specified
    # XXX: split request and request slave into different update/allocate functions and simplify.

    # By default, ALWAYS request instance on default computer
    parsed_request_dict['filter_kw'].setdefault('computer_guid', app.config['computer_id'])
    if slave:
      software_instance = requestSlave(**parsed_request_dict)
    else:
      software_instance = requestNotSlave(**parsed_request_dict)

  return dumps(software_instance)

def parseRequestComputerPartitionForm(form):
  """
  Parse without intelligence a form from a request(), return it.
  """
  parsed_dict = {
    'software_release': unicode2str(form['software_release']),
    'software_type': unicode2str(form.get('software_type')),
    'partition_reference': unicode2str(form.get('partition_reference', '')),
    'partition_id': unicode2str(form.get('computer_partition_id', '')),
    'partition_parameter_kw': loads(form.get('partition_parameter_xml', EMPTY_DICT_XML).encode('utf-8')),
    'filter_kw': loads(form.get('filter_xml', EMPTY_DICT_XML).encode('utf-8')),
    # Note: currently ignored for slave instance (slave instances
    # are always started).
    'requested_state': loads(form.get('state').encode('utf-8')),
  }

  return parsed_dict

run_id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
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
    return run_id == bytes2str(slap._connection_helper.GET('/getRunId'))
  except:
    return False

@app.route('/getRunId', methods=['GET'])
def getRunId():
  return run_id

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

  master_entry = app.config.get('multimaster').get(master_url, None)
  # Check if this master is known
  if not master_entry:
    # Check if it is ourself
    if not master_url.startswith('https') and checkIfMasterIsCurrentMaster(master_url):
      return False
    app.logger.warning('External SlapOS Master URL %s is not listed in multimaster list.' % master_url)
    abort(404)

  return True

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
    for mutimaster_url, mutimaster_entry in six.iteritems(app.config.get('multimaster')):
      if software_release in mutimaster_entry['software_release_list']:
        # Don't allocate the instance locally, but forward to specified master
        return mutimaster_url
    return None

def forwardRequestToExternalMaster(master_url, request_form):
  """
  Forward instance request to external SlapOS Master.
  """
  master_entry = app.config.get('multimaster').get(master_url, {})
  key_file = master_entry.get('key')
  cert_file = master_entry.get('cert')
  if master_url.startswith('https') and (not key_file or not cert_file):
    app.logger.warning('External master %s configuration did not specify key or certificate.' % master_url)
    abort(404)
  if master_url.startswith('https') and not master_url.startswith('https') and (key_file or cert_file):
    app.logger.warning('External master %s configurqtion specifies key or certificate but is using plain http.' % master_url)
    abort(404)

  slap = slapos.slap.slap()
  if key_file:
    slap.initializeConnection(master_url, key_file=key_file, cert_file=cert_file)
  else:
    slap.initializeConnection(master_url)

  # Prefix instance reference with id of requester (partition id (ends with a digit) or 'user' (cannot be a partition id))
  requester_id = unicode2str(request_form.get('computer_partition_id', 'user'))
  partition_reference = '%s_%s' % (requester_id, unicode2str(request_form['partition_reference']))

  filter_kw = loads(request_form['filter_xml'].encode('utf-8'))
  partition_parameter_kw = loads(request_form['partition_parameter_xml'].encode('utf-8'))

  app.logger.info("Forwarding request of %s to %s", partition_reference, master_url)
  app.logger.debug("request_form: %s", request_form)

  # Store in database
  execute_db('forwarded_partition_request', 'INSERT OR REPLACE INTO %s values(:partition_reference, :master_url)',
             {'partition_reference':partition_reference, 'master_url': master_url})

  if master_entry.get('computer') and master_entry.get('partition'):
    app.logger.debug("requesting from partition %s", master_entry)
    # XXX ComputerPartition.request and OpenOrder.request have different signatures
    partition = slap.registerComputerPartition(
        master_entry['computer'],
        master_entry['partition'],
    ).request(
        software_release=request_form['software_release'],
        software_type=request_form.get('software_type', ''),
        partition_reference=partition_reference,
        shared=loads(request_form['shared_xml'].encode('utf-8')),
        partition_parameter_kw=partition_parameter_kw,
        filter_kw=filter_kw,
        state=loads(request_form['state'].encode('utf-8')),
    )
  else:
    filter_kw['source_instance_id'] = partition_reference
    partition = slap.registerOpenOrder().request(
        software_release=request_form['software_release'],
        partition_reference=partition_reference,
        partition_parameter_kw=partition_parameter_kw,
        software_type=request_form.get('software_type', ''),
        filter_kw=filter_kw,
        state=loads(request_form['state'].encode('utf-8')),
        shared=loads(request_form['shared_xml'].encode('utf-8')),
    )

  # XXX move to other end
  partition._master_url = master_url # type: ignore
  partition._connection_helper = None
  partition._software_release_document = request_form['software_release'] # type: ignore
  return dumps(partition)

def getAllocatedInstance(partition_reference):
  """
  Look for existence of instance, if so return the
  corresponding partition dict, else return None
  """
  args = []
  a = args.append
  table = 'partition'
  q = 'SELECT * FROM %s WHERE partition_reference=?'
  a(partition_reference)
  return execute_db(table, q, args, one=True)

def getAllocatedSlaveInstance(slave_reference, requested_computer_id):
  """
  Look for existence of instance, if so return the
  corresponding partition dict, else return None
  """
  args = []
  a = args.append
  # XXX: Scope currently depends on instance which requests slave.
  # Meaning that two different instances requesting the same slave will
  # result in two different allocated slaves.
  table = 'slave'
  q = 'SELECT * FROM %s WHERE reference=? and computer_reference=?'
  a(slave_reference)
  a(requested_computer_id)
  # XXX: check there is only one result
  return execute_db(table, q, args, one=True)

def getRootPartition(reference):
  """Climb the partitions tree up by 'requested_by' link to get the root partition."""
  p = 'SELECT * FROM %s WHERE reference=?'
  partition = execute_db('partition', p, [reference], one=True)
  if partition is None:
    app.logger.warning("Nonexisting partition \"{}\". Known are\n{!s}".format(
      reference, execute_db("partition", "select reference, requested_by from %s")))
    return None

  while True:
    requested_by = partition['requested_by']
    if requested_by is None or requested_by == reference:
      return partition
    parent_partition = execute_db('partition', p, (requested_by,), one=True)
    if parent_partition is None:
      return partition
    partition = parent_partition
    reference = requested_by

def requestNotSlave(software_release, software_type, partition_reference, partition_id, partition_parameter_kw, filter_kw, requested_state):
  instance_xml = dict2xml(partition_parameter_kw)
  requested_computer_id = filter_kw['computer_guid']

  partition = execute_db('partition',
    'SELECT * FROM %s WHERE partition_reference=?',
    (partition_reference,), one=True)

  args = []
  a = args.append
  q = 'UPDATE %s SET slap_state="busy"'

  if partition is None:
    partition = execute_db('partition',
        'SELECT * FROM %s WHERE slap_state="free" and computer_reference=?',
        [requested_computer_id], one=True)
    if partition is None:
      app.logger.warning('No more free computer partition')
      abort(404)
    if partition_reference:
      q += ' ,partition_reference=?'
      a(partition_reference)
    if partition_id:
      q += ' ,requested_by=?'
      a(partition_id)
    if not software_type:
      software_type = 'RootSoftwareInstance'
  else:
    if partition['requested_by']:
      root_partition = getRootPartition(partition['requested_by'])
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
  partition = execute_db('partition', 'SELECT * FROM %s WHERE reference=? and computer_reference=?',
      [partition['reference'], partition['computer_reference']], one=True)
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

def requestSlave(software_release, software_type, partition_reference, partition_id, partition_parameter_kw, filter_kw, requested_state):
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
    app.logger.warning('No partition corresponding to slave request: %s' % args)
    abort(404)

  # We set slave dictionary as described in docstring
  new_slave = {}
  slave_reference = partition_id + '_' + partition_reference
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
  partition = execute_db('partition', 'SELECT * FROM %s WHERE reference=? and computer_reference=?',
      [partition['reference'], requested_computer_id], one=True)

  # Add slave to slave table if not there
  slave = execute_db('slave', 'SELECT * FROM %s WHERE reference=? and computer_reference=?',
                     [slave_reference, requested_computer_id], one=True)
  if slave is None:
    execute_db('slave',
               'INSERT OR IGNORE INTO %s (reference,computer_reference,asked_by,hosted_by) values(:reference,:computer_reference,:asked_by,:hosted_by)',
               [slave_reference, requested_computer_id, partition_id, partition['reference']])
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

@app.route('/softwareInstanceRename', methods=['POST'])
def softwareInstanceRename():
  new_name = unicode2str(request.form['new_name'])
  computer_partition_id = unicode2str(request.form['computer_partition_id'])
  computer_id = unicode2str(request.form['computer_id'])

  q = 'UPDATE %s SET partition_reference = ? WHERE reference = ? AND computer_reference = ?'
  execute_db('partition', q, [new_name, computer_partition_id, computer_id])
  return 'done'

@app.route('/getComputerPartitionStatus', methods=['GET'])
def getComputerPartitionStatus():
  return dumps('Not implemented.')

@app.route('/computerBang', methods=['POST'])
def computerBang():
  return dumps('')

@app.route('/getComputerPartitionCertificate', methods=['GET'])
def getComputerPartitionCertificate():
  # proxy does not use partition certificate, but client calls this.
  return dumps({'certificate': '', 'key': ''})

@app.route('/getSoftwareReleaseListFromSoftwareProduct', methods=['GET'])
def getSoftwareReleaseListFromSoftwareProduct():
  software_product_reference = request.args.get('software_product_reference')
  software_release_url = request.args.get('software_release_url')

  if software_release_url:
    assert(software_product_reference is None)
    raise NotImplementedError('software_release_url parameter is not supported yet.')
  else:
    assert(software_product_reference is not None)
    if software_product_reference in app.config['software_product_list']:
      software_release_url_list =\
          [app.config['software_product_list'][software_product_reference]]
    else:
      software_release_url_list = []
    return dumps(software_release_url_list)


# hateoas routing
# ---------------

# We only need to handle the hateoas requests made by
#   slapos service list
#   slapos service info <reference>
#   slapos computer list
#   slapos computer info <reference>


def unquoted_url_for(method, **kwargs):
  return unquote(url_for(method, **kwargs))

def busy_root_partitions_list(title=None):
  partitions = []
  query = 'SELECT * FROM %s WHERE slap_state<>"free" AND requested_by IS NULL'
  args = []
  if title:
    query += ' AND partition_reference=?'
    args.append(title)
  for row in execute_db('partition', query, args):
    p = dict(row)
    p['url_string'] = p['software_release']
    p['title'] = p['partition_reference']
    p['relative_url'] = url_for('hateoas_partitions', partition_reference=p['partition_reference'])
    partitions.append(p)
  return partitions

def computers_list(reference=None):
  computers = []
  query = 'SELECT * FROM %s'
  args = []
  if reference:
    query += ' WHERE reference=?'
    args.append(reference)
  for row in execute_db('computer', query, args):
    c = dict(row)
    c['title'] = c['reference']
    c['relative_url'] = url_for('hateoas_computers', computer_reference=c['reference'])
    computers.append(c)
  return computers

r_string = re.compile('"((\\.|[^\\"])*)"')

def is_valid(name):
  match = r_string.match(name)
  if match.group(0) == name:
    return True
  return False

p_service_list = 'portal_type:"Instance Tree" AND validation_state:validated'
p_service_info = p_service_list + ' AND title:='
p_computer_list = 'portal_type:"Computer" AND validation_state:validated'
p_computer_info = p_computer_list + ' AND reference:='

def parse_query(query):
  if query == p_service_list:
    return busy_root_partitions_list()
  elif query.startswith(p_service_info):
    title = query[len(p_service_info):]
    if is_valid(title):
      return busy_root_partitions_list(title.strip('"'))
  elif query == p_computer_list:
    return computers_list()
  elif query.startswith(p_computer_info):
    reference = query[len(p_computer_info):]
    if is_valid(reference):
      return computers_list(reference.strip('"'))
  return None

@app.route('/hateoas/partitions/<partition_reference>', methods=['GET'])
def hateoas_partitions(partition_reference):
  partition = execute_db('partition', 'SELECT * FROM %s WHERE partition_reference=?', [partition_reference], one=True)
  if partition is None:
    abort(404)
  return {
    '_embedded': {
      '_view': {
        'form_id': {
          'type': 'StringField',
          'key': 'partition',
          'default': partition['reference'],
        },
        'my_reference': {
          'type': 'StringField',
          'key': 'partition_reference',
          'default': partition['partition_reference'],
        },
        'my_slap_state': {
          'type': 'StringField',
          'key': 'slap_state',
          'default': partition['slap_state'],
        },
        'my_text_content': {
          'type': 'StringField',
          'key': 'xml',
          'default': partition['xml'],
        },
        'my_connection_parameter_list': {
          'type': 'StringField',
          'key': 'connection_xml',
          'default': partition['connection_xml'],
        },
        'my_url_string': {
          'type': 'StringField',
          'key': 'software_release',
          'default': partition['software_release'],
        },
      },
    },
    '_links': {
      'type': {
        'name': 'Instance Tree',
      },
    },
  }

@app.route('/hateoas/computers/<computer_reference>', methods=['GET'])
def hateoas_computers(computer_reference):
  computer = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_reference], one=True)
  if computer is None:
    abort(404)
  return {
    '_embedded': {
      '_view': {
        'form_id': {
          'type': 'StringField',
          'key': 'computer',
          'default': computer['reference'],
        },
        'my_reference': {
          'type': 'StringField',
          'key': 'reference',
          'default': computer['reference'],
        },
        'my_title': {
          'type': 'StringField',
          'key': 'reference',
          'default': computer['reference'],
        },
      },
    },
    '_links': {
      'type': {
        'name': 'Computer',
      },
    },
  }

def hateoas_traverse():
  return redirect(request.args.get('relative_url'))

def hateoas_search():
  contents = parse_query(request.args.get("query"))
  if contents is None:
    abort(400)
  return { '_embedded': {'contents': contents} }

def hateoas_root():
  return {
    '_links': {
      'raw_search': {
      'href': urljoin(request.host_url, unquoted_url_for('hateoas', mode='search', query='{query}', select_list='{select_list}'))
    },
      'traverse': {
        'href': urljoin(request.host_url, unquoted_url_for('hateoas', mode='traverse', relative_url='{relative_url}', view='{view}'))
      },
    }
  }

mode_handlers = {
  None: hateoas_root,
  'search': hateoas_search,
  'traverse': hateoas_traverse,
}

@app.route('/hateoas', methods=['GET'])
def hateoas():
  mode = request.args.get('mode')
  handler = mode_handlers.get(mode, lambda: abort(400))
  resp = handler()
  return resp
