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

from six.moves import configparser
import os

from slapos.cli.command import Command


class ConfigError(Exception):
    pass


class ConfigCommand(Command):
    """
    Base class for commands that require a configuration file
    """

    default_config_var = 'SLAPOS_CONFIGURATION'

    # use this if default_config_var does not exist
    default_config_path = '/etc/opt/slapos/slapos.cfg'

    def get_parser(self, prog_name):
        ap = super(ConfigCommand, self).get_parser(prog_name)
        ap.add_argument('--cfg',
                        help='SlapOS configuration file'
                             ' (default: $%s or %s)' %
                             (self.default_config_var, self.default_config_path))
        return ap

    def config_path(self, args):
        if args.cfg:
            cfg_path = args.cfg
        else:
            cfg_path = os.environ.get(self.default_config_var, self.default_config_path)
        return os.path.expanduser(cfg_path)

    def fetch_config(self, args):
        """
        Returns a configuration object if file exists/readable/valid,
        will raise an error otherwise. The exception may come from the
        configparser itself if the configuration content is very broken,
        and will clearly show what is wrong with the file.
        """

        cfg_path = self.config_path(args)

        self.app.log.debug('Loading config: %s', cfg_path)

        if not os.path.exists(cfg_path):
            raise ConfigError('Configuration file does not exist: %s' % cfg_path)

        configp = configparser.SafeConfigParser()
        if configp.read(cfg_path) != [cfg_path]:
            # bad permission, etc.
            raise ConfigError('Cannot parse configuration file: %s' % cfg_path)

        return configp


class ClientConfigCommand(ConfigCommand):
    """
    Base class for client commands, that use the client configuration file
    """

    default_config_var = 'SLAPOS_CLIENT_CONFIGURATION'
    default_config_path = '~/.slapos/slapos-client.cfg'
    command_group = 'client'
