# -*- coding: utf-8 -*-

import pkg_resources

DB_VERSION = pkg_resources.resource_stream('slapos.proxy', 'schema.sql').readline().strip().split(b':')[1]
import six
if six.PY3:
  DB_VERSION = DB_VERSION.decode('utf-8')

