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

import logging
import sys
import argparse

from slapos.cli.command import check_root_user
from slapos.cli.config import ConfigCommand
from slapos.format import do_format, FormatConfig, tracing_monkeypatch, UsageError
from slapos.util import string_to_boolean

class FormatCommand(ConfigCommand):
    """
    create users, partitions and network configuration
    """
    command_group = 'node'

    def get_parser(self, prog_name):
        ap = super(FormatCommand, self).get_parser(prog_name)

        ap.add_argument('-x', '--computer_xml',
                        default=argparse.SUPPRESS, #can't use default here because it would overwrite .cfg
                        help="Path to file with computer's XML. If does not exists, will be created")

        ap.add_argument('--computer_json',
                        default=argparse.SUPPRESS, #can't use default here because it would overwrite .cfg
                        help="Path to a JSON version of the computer's XML (for development only)")

        ap.add_argument('-i', '--input_definition_file',
                        default=argparse.SUPPRESS, #can't use default here because it would overwrite .cfg
                        help="Path to file to read definition of computer instead of "
                        "declaration. Using definition file allows to disable "
                        "'discovery' of machine services and allows to define computer "
                        "configuration in fully controlled manner.")

        ap.add_argument('-o', '--output_definition_file',
                        default=argparse.SUPPRESS, #can't use default here because it would overwrite .cfg
                        help="Path to file to write definition of computer from "
                        "declaration.")

        ap.add_argument('--alter_user',
                        choices=['True', 'False'],
                        default=argparse.SUPPRESS, #can't use default here because it would overwrite .cfg
                        help='Shall slapformat alter user database'
                             ' (default: {})'.format(FormatConfig.alter_user))

        ap.add_argument('--alter_network',
                        choices=['True', 'False'],
                        default=argparse.SUPPRESS, #can't use default here because it would overwrite .cfg
                        help='Shall slapformat alter network configuration'
                             ' (default: {})'.format(FormatConfig.alter_network))

        ap.add_argument('--now',
                        default=False, # can have a default as it is not in .cfg
                        action="store_true",
                        help='Launch slapformat without delay'
                             ' (default: %(default)s)')

        ap.add_argument('-n', '--dry_run',
                        default=False, # can have a default as it is not in .cfg
                        action="store_true",
                        help="Don't actually do anything"
                             " (default: %(default)s)")

        ap.add_argument('-c', '--console',
                        help="Console output (obsolete)")
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args) # read the options in .cfg

        conf = FormatConfig(logger=self.app.log)

        conf.mergeConfig(args, configp) # commandline options overwrite .cfg options

        # Parse if we have to check if running from root
        # XXX document this feature.
        if string_to_boolean(getattr(conf, 'root_check', 'True').lower()):
          check_root_user(self)

        if len(self.app.log.handlers) == 0 and not self.app.options.log_file and conf.log_file:
            # This block is called again if "slapos node boot" failed.
            # Don't add a handler again, otherwise the output becomes double.
            #
            # no log file is provided by argparser,
            # we set up the one from config
            file_handler = logging.FileHandler(conf.log_file)
            formatter = logging.Formatter(self.app.LOG_FILE_MESSAGE_FORMAT)
            file_handler.setFormatter(formatter)
            self.app.log.addHandler(file_handler)

        try:
            conf.setConfig()
        except UsageError as err:
            sys.stderr.write(err.message + '\n')
            sys.stderr.write("For help use --help\n")
            sys.exit(1)

        tracing_monkeypatch(conf)

        do_format(conf=conf)
