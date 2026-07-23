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

import re
import os
from datetime import datetime
from slapos.proxy.db_version import DB_VERSION
from slapos.util import sqlite_connect

from flask import g, Flask, redirect, url_for, current_app
from werkzeug.middleware.proxy_fix import ProxyFix
from .hateoas import hateoas_blueprint
from .slap_tool import slap_tool_blueprint
from .http_proxy import http_proxy_blueprint
from .db import execute_db, encodeSharedParameters
from .json_rpc import JsonRpcManager
from .panel import panel_blueprint

from slapos.util import loads

from six.moves.urllib.parse import urlparse

app = Flask(__name__)
# Support having haproxy/nginx in front to provide https (in this case haproxy should set X-Forwarded-Proto header)
# Support to be in a different directory than / (in this case haproxy should set X-Forwarded-Prefix header)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_prefix=1)
app.register_blueprint(hateoas_blueprint, url_prefix="/hateoas")
app.register_blueprint(slap_tool_blueprint)
app.register_blueprint(http_proxy_blueprint, url_prefix="/http_proxy")
JsonRpcManager().init_app(app)
app.register_blueprint(panel_blueprint, url_prefix="/panel")

def connect_db():
  return sqlite_connect(current_app.config['DATABASE_URI'])

def _upgradeDatabaseIfNeeded():
  """
  Analyses current database compared to defined schema,
  and adapt tables/data it if needed.
  """
  previous_table_list = g.db.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
  ).fetchall()
  if previous_table_list:
    search = re.compile(r'\d+$').search
    current_schema_version, = {search(table).group(0)
                               for table, in previous_table_list}
    # If version of current database is not old, do nothing
    if current_schema_version == DB_VERSION:
      return

    # first, make a backup of current database
    backup_file_name = "{}-backup-{}to{}-{}.sql".format(
        current_app.config['DATABASE_URI'],
        current_schema_version,
        DB_VERSION,
        datetime.now().isoformat())
    current_app.logger.info(
        'Old schema detected: Creating a backup of current tables at %s',
        backup_file_name
    )
    with open(backup_file_name, 'w') as f:
      for line in g.db.iterdump():
          f.write('%s\n' % line)

  with current_app.open_resource('schema.sql', 'r') as f:
    schema = f.read() % dict(version=DB_VERSION, computer=current_app.config['computer_id'])
  g.db.execute('BEGIN')
  try:
    g.db.executescript(schema)

    if previous_table_list:
      current_app.logger.info('Old schema detected: Migrating old tables...')
      n = len(current_schema_version)
      current_schema_version = int(current_schema_version)
      # Fetch all old tables' rows before inserting anything, so a fix-up can
      # read one table's rows (e.g. slave, partition) while emitting rows into
      # a different target table (e.g. instance).
      old_rows_by_table = {}
      for old_table, in previous_table_list:
        old_rows_by_table[old_table[:-n]] = execute_db(
          old_table, 'SELECT * from %s', db_version='')
      # Identity mapping: each old table's rows go to the same-named new table.
      # A fix-up may replace an entry, drop a key (no target table), or add a
      # key pointing at rows built from another table.
      new_rows_by_table = dict(old_rows_by_table)

      if current_schema_version < 17:
        rv = old_rows_by_table.get('local_software_release_root')
        if rv:
          path, = {row['path'] for row in rv}
          del new_rows_by_table['local_software_release_root']
          new_rows_by_table.setdefault('config', []).append(
            {'name': 'local_software_release_root', 'value': path})
        partition_rows = old_rows_by_table.get('partition') or []
        request_dict = {row['reference']: (i, row['requested_by'])
                        for i, row in enumerate(partition_rows)}
        for i, requested_by in request_dict.values():
          if requested_by:
            while True:
              j, requested_by = request_dict[requested_by]
              if not requested_by:
                break
            partition_rows[i]['requested_by'] = \
              partition_rows[j]['partition_reference']

      if current_schema_version < 18:
        # Schemas older than v11 lack computer_reference; the current schema
        # fills it from its DEFAULT, so the guid the proxy publishes for such
        # a migrated instance uses the configured computer id.
        computer_id = current_app.config['computer_id']
        partition_rows = old_rows_by_table.get('partition') or []
        slave_rows = old_rows_by_table.get('slave') or []
        # Slave rows are indexed for connection_xml / asked_by recovery only.
        # They are NOT the source of shared instances: v17 never deletes a slave
        # row on destroy, so the table accumulates stale rows. The wire truth --
        # what slapgrid and deployed SRs actually consume -- is the host's
        # slave_instance_list blob, so pass 3 is driven by the blobs.
        slave_row_by_address = {
          (row.get('computer_reference') or computer_id, row['reference']): row
          for row in slave_rows}
        instance_rows, new_partition_rows = [], []
        # Guids are opaque primary keys; a frozen-guid collision (two
        # pathologically named computers/partitions freezing to the same
        # string) would be silently clobbered by INSERT OR REPLACE. Warn so the
        # drop is diagnosable rather than crashing.
        seen_guid_address = {}
        def emit_instance(inst, address):
          guid = inst['instance_guid']
          if guid in seen_guid_address:
            current_app.logger.warning(
              'Instance guid collision during migration: %r emitted for both '
              '%s and %s; INSERT OR REPLACE keeps the last, dropping the first',
              guid, seen_guid_address[guid], address)
          seen_guid_address[guid] = address
          instance_rows.append(inst)

        def slaveTitle(slave_reference, asked_by):
          # deterministic title: asked_by is the root title stored on the slave
          # row; strip it as a prefix so the split is unambiguous
          prefix = asked_by + '_'
          if asked_by and slave_reference.startswith(prefix):
            return slave_reference[len(prefix):]
          return slave_reference.lstrip('_')

        # --- pass 1: non-shared instances from busy partition rows, guid FROZEN ---
        root_guid_by_title = {}
        for row in partition_rows:
          resource = {'reference': row['reference'],
                      'slap_state': row['slap_state']}
          if 'computer_reference' in row:
            resource['computer_reference'] = row['computer_reference']
          new_partition_rows.append(resource)
          if row['slap_state'] != 'free':
            computer_reference = row.get('computer_reference') or computer_id
            # the exact string the proxy already published for this instance
            guid = '%s-%s' % (computer_reference, row['reference'])
            # a busy slot with no title (empty-title request) still has a
            # published guid that must keep resolving -- fall back to the slot
            # address for the title, but do NOT register it as a root title.
            if row['partition_reference'] and not row['requested_by']:  # v17 root
              root_guid_by_title.setdefault(row['partition_reference'], guid)
            emit_instance(dict(
              instance_guid=guid,
              title=row['partition_reference'] or row['reference'], shared=0,
              software_release=row['software_release'],
              software_type=row['software_type'],
              requested_state=row['requested_state'],
              xml=row['xml'], connection_xml=row['connection_xml'],
              sla_xml=None, slave_reference=None,
              allocated_computer=computer_reference,
              allocated_partition=row['reference'],
              timestamp=row.get('timestamp'),
              _requested_by_title=row['requested_by']),           # resolved in pass 2
              (computer_reference, row['reference']))
        # --- pass 2: tree edges from the flattened v17 root titles ---
        for inst in instance_rows:
          root_title = inst.pop('_requested_by_title')
          # v17 discarded the direct parent (it flattened the edge to the root
          # title). The root is the best available approximation for
          # pre-existing trees; trees built after v18 record the true direct
          # requester. Orphan edges (root title with no busy root) map to '',
          # so the row becomes a root -- how every v17 reader treated an
          # unmatched title.
          guid = root_guid_by_title.get(root_title, '') if root_title else ''
          inst['root_instance_guid'] = guid
          inst['requested_by_instance_guid'] = guid
        # --- pass 3: shared instances from host blobs, guid MINTED ---
        counter = 0
        for row in partition_rows:
          if row['slap_state'] == 'free' or not row['slave_instance_list']:
            continue
          host_computer = row.get('computer_reference') or computer_id
          host_reference = row['reference']
          # blob append-order reproduces today's slave_instance_list ordering
          for entry in loads(row['slave_instance_list'].encode('utf-8')):
            entry = dict(entry)
            slave_reference = entry.pop('slave_reference', None)
            entry.pop('slave_title', None)
            software_type = entry.pop('slap_software_type', None)
            params = entry
            slave = slave_row_by_address.get((host_computer, slave_reference))
            if slave is not None:
              connection_xml = slave['connection_xml']
              asked_by = slave['asked_by'] or ''
            else:
              # a blob entry with no slave row cannot happen in practice; keep
              # it live (it is on the wire) but with no recoverable connection
              # or root title
              connection_xml = None
              asked_by = ''
            counter += 1
            root_guid = root_guid_by_title.get(asked_by, '')
            emit_instance(dict(
              instance_guid='SOFTINST-%s' % counter,              # nothing published
              title=slaveTitle(slave_reference, asked_by), shared=1,  # to freeze
              root_instance_guid=root_guid,
              requested_by_instance_guid=root_guid,
              software_release=row['software_release'],
              software_type=software_type,
              requested_state='started',     # the only state v17 could express
              # params recovered from the v17 blob are already typed (loaded
              # via xml_marshaller above); store them typed so they survive
              xml=encodeSharedParameters(params), connection_xml=connection_xml,
              sla_xml=None,
              slave_reference=slave_reference,                    # frozen for the
              allocated_computer=host_computer,                   # blob projection
              allocated_partition=host_reference,
              # match v17: a migrated shared row publishes the host partition's
              # timestamp until its first mutation, not processing_timestamp 0
              timestamp=row.get('timestamp')),
              (host_computer, host_reference))
        new_rows_by_table['partition'] = new_partition_rows
        new_rows_by_table['instance'] = instance_rows
        new_rows_by_table.pop('slave', None)
        new_rows_by_table.setdefault('config', []).append(
          {'name': 'last_instance_id', 'value': str(counter)})

      for table, rows in new_rows_by_table.items():
        for row in rows:
          query = 'INSERT OR REPLACE INTO %%s (%s) VALUES (:%s)' % (
            ', '.join(row), ', :'.join(row))
          execute_db(table, query, row)
      for old_table, in previous_table_list:
        g.db.execute("DROP table " + old_table)
  except:
    g.db.rollback()
    raise
  g.db.commit()

def _updateLocalSoftwareReleaseRootPathIfNeeded():
  """
  Update the local software release root path if it changed,
  and rebase all URLs in the database relatively to the new path.
  """
  # Retrieve the current root path and replace it with the new one
  current_root_path = (execute_db('config',
    "SELECT value FROM %s WHERE name='local_software_release_root'",
    one=True) or {}).get('value', os.sep)
  new_root_path = current_app.config.get('local_software_release_root', os.sep)
  # Check whether one is the same as or a subpath of the other
  if current_root_path == new_root_path:
    return
  execute_db('config',
    "INSERT OR REPLACE INTO %s VALUES('local_software_release_root',?)",
    [new_root_path])
  relpath = os.path.relpath(new_root_path, current_root_path)
  if not relpath.startswith(os.pardir + os.sep):
    current_app.logger.info('Do not rebase any URLs because %s is a subpath of %s', new_root_path, current_root_path)
    return
  elif os.path.basename(relpath) == os.pardir:
    current_app.logger.info('Do not rebase any URLs because %s is a superpath of %s', new_root_path, current_root_path)
    return
  # Backup the database before migrating
  database_path = current_app.config['DATABASE_URI']
  backup_path = database_path + "-backup-%s.sql" % datetime.now().isoformat()
  current_app.logger.info("Backuping database to %s", backup_path)
  with open(backup_path, 'w') as f:
    for line in g.db.iterdump():
      f.write('%s\n' % line)
  # Rebase all URLs relative to the new root path
  current_app.logger.info('Rebase URLs on local software release root path')
  current_app.logger.info('Old root path: %s', current_root_path)
  current_app.logger.info('New root path: %s', new_root_path)
  def migrate_url(url):
    current_app.logger.debug('Examining URL %s', url)
    if not url or urlparse(url).scheme:
      current_app.logger.debug('  Do not rebase because it is not a path')
      return url
    rel = os.path.relpath(url, current_root_path)
    if rel.startswith(os.pardir + os.sep):
      current_app.logger.debug('  Do not rebase because it is not a subpath of %s', current_root_path)
      return url
    new = os.path.join(new_root_path, rel)
    if not os.path.isfile(new) and os.path.isfile(url):
      current_app.logger.debug('  Do not rebase because it refers to an existing file but %s does not', new)
      return url
    current_app.logger.debug('  Migrate to rebased URL %s', new)
    return new
  g.db.create_function('migrate_url', 1, migrate_url)
  execute_db('software', 'UPDATE %s SET url=migrate_url(url)')
  # software_release lives on the instance row under v18 (the partition row is a
  # pure resource slot); rebase the URLs there.
  execute_db('instance', 'UPDATE %s SET software_release=migrate_url(software_release)')

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
  if getattr(g, "db", None) is not None:
    # Only close the DB if it has been connected before
    g.db.commit()
    g.db.close()
  return response

@app.route('/getRunId', methods=['GET'])
def getRunId():
  return current_app.config['run_id']

@app.route('/', methods=['GET'])
def index():
  return redirect(url_for('panel.index'))
