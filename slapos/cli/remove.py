# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Nexedi SA and Contributors.
# All Rights Reserved.
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

from slapos.cli.config import ClientConfigCommand
from slapos.client import init, ClientConfig


class RemoveCommand(ClientConfigCommand):
    """
    remove a Software from a node
    """

    def get_parser(self, prog_name):
        ap = super(RemoveCommand, self).get_parser(prog_name)

        ap.add_argument('software_url',
                        help='Your software url')

        ap.add_argument('node',
                        help="Target node")

        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        conf = ClientConfig(args, configp)
        local = init(conf, self.app.log)
        do_remove(self.app.log, args.software_url, args.node, local)


def do_remove(logger, software_url, computer_id, local):
    """
    Request deletion of Software Release
    'software_url' from computer 'computer_id'.
    """
    logger.info('Requesting deletion of %s Software Release...', software_url)

    if software_url in local:
        software_url = local[software_url]
    local['slap'].registerSupply().supply(
        software_release=software_url,
        computer_guid=computer_id,
        state='destroyed'
    )
    logger.info('Done.')
