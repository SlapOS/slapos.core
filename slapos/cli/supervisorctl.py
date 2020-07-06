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

import argparse

from slapos.cli.command import check_root_user
from slapos.cli.config import ConfigCommand

import supervisor.supervisorctl


class SupervisorctlCommand(ConfigCommand):
    """
    open supervisor console, for process management
    """
    command_group = 'node'

    def get_parser(self, prog_name):
        ap = super(SupervisorctlCommand, self).get_parser(prog_name)
        ap.add_argument('supervisor_args',
                        nargs=argparse.REMAINDER,
                        help='parameters passed to supervisorctl')
        return ap

    def _should_check_current_user_is_root(self, configp):
      if not configp.has_option('slapos', 'root_check'):
          return True
      return configp.getboolean('slapos', 'root_check')

    def _should_forbid_supervisord_launch(self, configp):
      if not configp.has_option('slapos', 'forbid_supervisord_automatic_launch'):
          return False
      return configp.getboolean('slapos', 'forbid_supervisord_automatic_launch')

    def take_action(self, args):
        configp = self.fetch_config(args)

        # Parse if we have to check if running from root
        # XXX document this feature.
        if self._should_check_current_user_is_root(configp):
            check_root_user(self)

        instance_root = configp.get('slapos', 'instance_root')
        forbid_supervisord_launch = self._should_forbid_supervisord_launch(configp)
        do_supervisorctl(
            self.app.log, instance_root, args.supervisor_args,
            forbid_supervisord_launch
        )

def do_supervisorctl(logger, instance_root, supervisor_args, forbid_supervisord_launch=False):
    from slapos.grid.svcbackend import (launchSupervisord, _getSupervisordConfigurationFilePath)
    if forbid_supervisord_launch is False:
        launchSupervisord(instance_root=instance_root, logger=logger)
    supervisor.supervisorctl.main(
        args=['-c', _getSupervisordConfigurationFilePath(instance_root)] + supervisor_args
    )

class SupervisorctlAliasCommand(SupervisorctlCommand):
    def take_action(self, args):
        args.supervisor_args = [self.alias] + args.supervisor_args
        super(SupervisorctlAliasCommand, self).take_action(args)


class SupervisorctlStatusCommand(SupervisorctlAliasCommand):
    """alias for 'node supervisorctl status'"""
    alias = 'status'


class SupervisorctlStartCommand(SupervisorctlAliasCommand):
    """alias for 'node supervisorctl start'"""
    alias = 'start'


class SupervisorctlStopCommand(SupervisorctlAliasCommand):
    """alias for 'node supervisorctl stop'"""
    alias = 'stop'


class SupervisorctlRestartCommand(SupervisorctlAliasCommand):
    """alias for 'node supervisorctl restart'"""
    alias = 'restart'


class SupervisorctlTailCommand(SupervisorctlAliasCommand):
    """alias for 'node supervisorctl tail'"""
    alias = 'tail'
