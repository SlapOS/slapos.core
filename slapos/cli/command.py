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

import argparse
import functools
import os
import sys

from cliff import command


class Command(command.Command):

    def get_parser(self, prog_name):
        parser = argparse.ArgumentParser(
            description=self.get_description(),
            prog=prog_name,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        return parser

    def run(self, parsed_args):
        return self.take_action(parsed_args)

def check_root_user(config_command_instance):
  if sys.platform != 'cygwin' and os.getuid() != 0:
      config_command_instance.app.log.error('This slapos command must be run as root.')
      sys.exit(5)

def must_be_root(func):
    @functools.wraps(func)
    def inner(self, *args, **kw):
        check_root_user(self)
        return func(self, *args, **kw)
    return inner
