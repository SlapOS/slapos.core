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
from slapos.bouture import Bouture
from slapos.cli.config import ConfigCommand


class GraftCommand(ConfigCommand):
    """
    bouture node onto a new master
    """
    command_group = 'bouture'

    def get_parser(self, prog_name):
        ap = super(GraftCommand, self).get_parser(prog_name)
        ap.add_argument('--new-master-url',
                        required=True,
                        help='Url of new SlapOS Master onto which to bouture')
        ap.add_argument('--new-monitor-url',
                        help='Url of new monitor application')
        return ap

    def take_action(self, args):
        node_configp = self.fetch_config(args)
        Bouture(self.app.log, node_configp).graft(args)


class ConfigureCommand(GraftCommand):
    def get_parser(self, prog_name):
        ap = super(ConfigureCommand, self).get_parser(prog_name)
        ap.add_argument('--new-node-cfg',
                        required=True,
                        help='Path of the new node configuration file')
        return ap

    def take_action(self, args):
        node_configp = self.fetch_config(args)
        Bouture(self.app.log, node_configp).configure(args)


class FailoverCommand(ConfigureCommand):
    def get_parser(self, prog_name):
        ap = super(FailoverCommand, self).get_parser(prog_name)
        ap.add_argument('--pidfile',
                        required=True,
                        help='Path of the pidfile for instance processing')
        ap.add_argument('--switchfile',
                        required=True,
                        help='Path of the flag file for failover mode')
        return ap

    def take_action(self, args):
        node_configp = self.fetch_config(args)
        Bouture(self.app.log, node_configp).failover(args)
