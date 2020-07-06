# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Nexedi SA and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

import ast
import hashlib
import json
import re
import requests
import sys

import prettytable

from slapos.grid import networkcache
from slapos.cli.config import ConfigCommand
from slapos.cli.list import resetLogger
from slapos.util import str2bytes

class CacheLookupCommand(ConfigCommand):
    """
    perform a query to the networkcache.

    Check if source URL is available to be downloaded from cache.
    """

    def get_parser(self, prog_name):
        ap = super(CacheLookupCommand, self).get_parser(prog_name)
        ap.add_argument('url',
                        help='URL to query')
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        cache_dir = configp.get('networkcache', 'download-cache-url')
        sys.exit(do_lookup(self.app.log, cache_dir, args.url))

def do_lookup(logger, cache_dir, url):
    md5 = hashlib.md5(str2bytes(url)).hexdigest()

    try:
        cached_url = '%s/slapos-buildout-%s' % (cache_dir, md5)
        logger.debug('Connecting to %s', url)
        req = requests.get(cached_url, timeout=5)
    except (requests.Timeout, requests.ConnectionError):
        logger.critical('Cannot connect to cache server at %s', cached_url)
        return 10

    if not req.ok:
        if req.status_code == 404:
            logger.critical('Object not in cache: %s', url)
        else:
            logger.critical('Error while looking object %s: %s', url, req.reason)
        return 10

    entries = req.json()

    if not entries:
        logger.info('Object found in cache, but has no entries.')
        return 0

    pt = prettytable.PrettyTable(['file', 'sha512'])
    entry_list = sorted(json.loads(entry[0]) for entry in entries)
    for entry in entry_list:
        pt.add_row([entry["file"], entry["sha512"]])

    meta = json.loads(entries[0][0])
    logger.info('Software source URL: %s', url)
    logger.info('SHADIR URL: %s', cached_url)

    resetLogger(logger)
    for line in pt.get_string(border=True, padding_width=0, vrules=prettytable.NONE).split('\n'):
        logger.info(line)
    return 0
