# -*- coding: utf-8 -*-

import pkg_resources
from slapos.util import bytes2str

DB_VERSION = bytes2str(pkg_resources.resource_stream('slapos.proxy', 'schema.sql').readline()).strip().split(':')[1]

