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
from .db import execute_db
from .json_rpc import JsonRpcManager
from .panel import panel_blueprint

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
      for old_table, in previous_table_list:
        rv = execute_db(old_table, 'SELECT * from %s', db_version='')
        if rv:
          table = old_table[:-n]
          if current_schema_version < 17:
            if table == 'local_software_release_root':
              path, = {row['path'] for row in rv}
              rv = {'name': table, 'value': path},
              table = 'config'
            elif table == 'partition':
              request_dict = {row['reference']: (i, row['requested_by'])
                              for i, row in enumerate(rv)}
              for i, requested_by in request_dict.values():
                if requested_by:
                  while True:
                    j, requested_by = request_dict[requested_by]
                    if not requested_by:
                      break
                  rv[i]['requested_by'] = rv[j]['partition_reference']
          for row in rv:
            query = 'INSERT OR REPLACE INTO %%s (%s) VALUES (:%s)' % (
              ', '.join(row), ', :'.join(row))
            execute_db(table, query, row)
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
