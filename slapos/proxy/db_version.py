# -*- coding: utf-8 -*-

import pkg_resources
from slapos.util import bytes2str

with pkg_resources.resource_stream('slapos.proxy', 'schema.sql') as f:
  DB_VERSION = bytes2str(f.readline()).strip().split(':')[1]

