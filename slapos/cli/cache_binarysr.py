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

import hashlib
import json
import re
import sys

import prettytable

from slapos.grid import networkcache
from slapos.cli.config import ConfigCommand
from slapos.util import str2bytes

class CacheLookupCommand(ConfigCommand):
    """
    perform a query to the networkcache
    You can provide either a complete URL to the software release,
    or a corresponding MD5 hash value.

    The command will report which OS distribution/version have a binary
    cache of the software release, and which ones are compatible
    with the OS you are currently running.
    """
    command_group = 'cachelookup'

    def get_parser(self, prog_name):
        ap = super(CacheLookupCommand, self).get_parser(prog_name)
        ap.add_argument('software_url',
                        help='Your software url or MD5 hash')
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        cache_dir = configp.get('networkcache', 'download-binary-dir-url')
        cache_url = configp.get('networkcache', 'download-binary-cache-url')
        signature_certificate_list = configp.get('networkcache', 'signature-certificate-list')

        sys.exit(
          do_lookup(self.app.log, cache_dir, cache_url,
                    signature_certificate_list, args.software_url,))

def looks_like_md5(s):
    """
    Return True if the parameter looks like an hashed value.
    Not 100% precise, but we're actually more interested in filtering out URLs and pathnames.
    """
    return re.match('[0-9a-f]{32}', s)


def infotuple(entry):
    info_dict = networkcache.loadJsonEntry(entry[0])
    return info_dict['multiarch'], info_dict['os'], entry[1]


def do_lookup(logger, cache_dir, cache_url, signature_certificate_list,
              software_url):
    if looks_like_md5(software_url):
        md5 = software_url
    else:
        md5 = hashlib.md5(str2bytes(software_url)).hexdigest()
    try:
        entries = networkcache.download_entry_list(cache_url, cache_dir,
            md5, logger, signature_certificate_list)
    except Exception:
        logger.critical('Error while looking object %s', software_url,
            exc_info=True)
        return 1

    if not entries:
        logger.info('Object found in cache, but has no binary entries.')
        return 0

    pt = prettytable.PrettyTable(['multiarch', 'distribution', 'version', 'id', 'compatible?', 'verified?'])
    machine_info = networkcache.machine_info_tuple()

    for multiarch, os, verified in sorted(map(infotuple, entries)):
        row = [multiarch] + os
        row.append('yes' if networkcache.is_compatible(machine_info, (multiarch, os)) else 'no')
        row.append('yes' if verified else 'no')
        pt.add_row(row)

    meta = json.loads(entries[0][0])
    logger.info('Software URL: %s', meta['software_url'])
    logger.info('MD5:          %s', md5)

    for line in pt.get_string(border=True, padding_width=0, vrules=prettytable.NONE).split('\n'):
        logger.info(line)

    return 0
