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

from slapos.cli.config import ConfigCommand
from slapos.bang import do_bang
from slapos.util import string_to_boolean
from slapos.cli.command import check_root_user


class BangCommand(ConfigCommand):
    """
    request update on all partitions
    """
    command_group = 'node'

    def get_parser(self, prog_name):
        ap = super(BangCommand, self).get_parser(prog_name)
        ap.add_argument('-m', '--message', help='Message for bang')
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)

        root_check = True
        if configp.has_option('slapos', 'root_check'):
          root_check = configp.getboolean('slapos', 'root_check')

        if root_check:
          check_root_user(self)

        do_bang(configp, args.message)
