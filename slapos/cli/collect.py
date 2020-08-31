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

from slapos.collect import do_collect
from slapos.cli.command import must_be_root
from slapos.cli.config import ConfigCommand

class CollectCommand(ConfigCommand):
    """
    Collect system consumption and data and store.
    """
    command_group = 'node'

    def get_parser(self, prog_name):
        ap = super(CollectCommand, self).get_parser(prog_name)
        return ap

    @must_be_root
    def take_action(self, args):
        configp = self.fetch_config(args)
        do_collect(configp)
