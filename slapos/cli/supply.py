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
from slapos.client import init, ClientConfig, _getSoftwareReleaseFromSoftwareString

class SupplyCommand(ClientConfigCommand):
    """
    supply a Software to a node
    """

    def get_parser(self, prog_name):
        ap = super(SupplyCommand, self).get_parser(prog_name)

        ap.add_argument('software_url',
                        help='Your software url')

        ap.add_argument('node',
                        help='Target node')

        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        conf = ClientConfig(args, configp)
        local = init(conf, self.app.log)
        do_supply(self.app.log, args.software_url, args.node, local)


def do_supply(logger, software_release, computer_id, local):
    """
    Request installation of Software Release
    'software_release' on computer 'computer_id'.
    """
    logger.info('Requesting software installation of %s...',
                software_release)

    software_release = _getSoftwareReleaseFromSoftwareString(
        logger, software_release, local['product'])

    local['supply'](
        software_release=software_release,
        computer_guid=computer_id,
        state='available'
    )
    logger.info('Done.')
