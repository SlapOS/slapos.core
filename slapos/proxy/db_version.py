# -*- coding: utf-8 -*-

from slapos.util import bytes2str, get_package_resource_bytes

DB_VERSION = bytes2str(get_package_resource_bytes('slapos.proxy', 'schema.sql').splitlines()[0]).strip().split(':')[1]

