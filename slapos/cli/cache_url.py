# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import ast
import hashlib
import json
import re
import requests
import sys
import prettytable

from six.moves.urllib.error import HTTPError

from slapos.grid import networkcache
from slapos.cli.config import ConfigCommand
from slapos.cli.command import resetLogger
from slapos.util import str2bytes

class CacheLookupCommand(ConfigCommand):
    """
    perform a query to the networkcache.

    Check if source URL is available to be downloaded from cache.
    """
    command_group = 'cachelookup'

    def get_parser(self, prog_name):
        ap = super(CacheLookupCommand, self).get_parser(prog_name)
        ap.add_argument('url',
                        help='URL to query')
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        cache_dir = configp.get('networkcache', 'download-dir-url')
        cache_url = configp.get('networkcache', 'download-cache-url')
        signature_certificate_list = configp.get('networkcache', 'signature-certificate-list')

        sys.exit(
          do_lookup(self.app.log, cache_dir, cache_url,
                    signature_certificate_list, args.url))

def do_lookup(logger, cache_dir, cache_url, signature_certificate_list,
              url):
    key = 'file-urlmd5:' + hashlib.md5(url.encode()).hexdigest()
    try:
        entries = networkcache.download_entry_list(cache_url, cache_dir,
            key, logger, signature_certificate_list)
        if not entries:
            logger.info('Object found in cache, but has no entry.')
            return 0

        pt = prettytable.PrettyTable(['url', 'sha512', 'signed'])
        for entry in entries:
            d = json.loads(entry[0])
            pt.add_row([d["url"], d["sha512"], entry[1]])

        logger.info('Software source URL: %s', url)
        logger.info('SHADIR URL: %s/%s\n', cache_dir, key)

        resetLogger(logger)
        for line in pt.get_string(border=True, padding_width=0, vrules=prettytable.NONE).split('\n'):
            logger.info(line)
    except HTTPError as e:
        if e.code == 404:
            logger.info('Object not found in cache.')
        else:
            logger.info('Problem to connect to shacache.')
        return 1
    except Exception:
        logger.critical('Error while looking object %s', url,
            exc_info=True)
        return 1


    return 0
