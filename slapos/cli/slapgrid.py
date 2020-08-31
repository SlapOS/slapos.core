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

from slapos.cli.command import check_root_user
from slapos.cli.config import ConfigCommand

from slapos.grid.utils import setRunning, setFinished
from slapos.grid.slapgrid import (merged_options, check_missing_parameters, check_missing_files,
                                  random_delay, create_slapgrid_object, PROMISE_TIMEOUT)

from slapos.util import string_to_boolean

class SlapgridCommand(ConfigCommand):
    command_group = 'node'

    method_name = NotImplemented
    default_pidfile = NotImplemented
    pidfile_option_name = NotImplemented

    def get_parser(self, prog_name):
        ap = super(SlapgridCommand, self).get_parser(prog_name)

        # TODO move more options to the instance, software and report subclasses

        ap.add_argument('--instance-root',
                        help='The instance root directory location.')
        ap.add_argument('--software-root',
                        help='The software_root directory location.')
        ap.add_argument('--master-url',
                        help='The master server URL. Mandatory.')
        ap.add_argument('--computer-id',
                        help='The computer id defined in the server.')
        ap.add_argument('--supervisord-socket',
                        help='The socket supervisor will use.')
        ap.add_argument('--supervisord-configuration-path',
                        help='The location where supervisord configuration will be stored.')
        ap.add_argument('--buildout',
                        help='Location of buildout binary.')
        ap.add_argument('--pidfile',
                        help='The location where pidfile will be created. '
                             'Can be provided by configuration file as option '
                             '`%s` in slapos section, otherwise defaults '
                             'to %s' % (self.pidfile_option_name, self.default_pidfile))
        ap.add_argument('--key_file',
                        help='SSL Authorisation key file.')
        ap.add_argument('--cert_file',
                        help='SSL Authorisation certificate file.')
        ap.add_argument('--signature_private_key_file',
                        help='Signature private key file.')
        ap.add_argument('--master_ca_file',
                        help='Root certificate of SlapOS master key.')
        ap.add_argument('--certificate_repository_path',
                        help='Path to directory where downloaded certificates would be stored.')
        ap.add_argument('--maximum-periodicity',
                        type=int,
                        help='Periodicity at which buildout should be run in instance.')
        ap.add_argument('--promise-timeout',
                        default=PROMISE_TIMEOUT,
                        type=int,
                        help='Promise timeout in seconds'
                             ' (default: %(default)s)')
        ap.add_argument('--now',
                        action='store_true',
                        help='Launch slapgrid without delay. Default behavior.')
        ap.add_argument('--maximal_delay',
                        help='Deprecated. Will only work from configuration file in the future.')
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        options = merged_options(args, configp)

        # Parse if we have to check if running from root
        # XXX document this feature.
        if string_to_boolean(options.get('root_check', 'True').lower()):
          check_root_user(self)

        check_missing_parameters(options)
        check_missing_files(options)

        random_delay(options, logger=self.app.log)

        slapgrid_object = create_slapgrid_object(options, logger=self.app.log)

        pidfile = ( options.get(self.pidfile_option_name) or
            options.get('pidfile') or # for compatibility we also read pidfile from option `pidfile`
            self.default_pidfile )

        if pidfile:
            setRunning(logger=self.app.log, pidfile=pidfile)
        try:
            return getattr(slapgrid_object, self.method_name)()
        finally:
            if pidfile:
                setFinished(pidfile)


class SoftwareCommand(SlapgridCommand):
    """run software installation/deletion"""

    method_name = 'processSoftwareReleaseList'
    default_pidfile = '/opt/slapos/slapgrid-sr.pid'
    pidfile_option_name = 'pidfile_software'

    def get_parser(self, prog_name):
        ap = super(SoftwareCommand, self).get_parser(prog_name)

        ap.add_argument('--buildout-debug',
                        action='store_true',
                        help='Run buildout in debug mode (with -D command line switch)')
        only = ap.add_mutually_exclusive_group()
        only.add_argument('--all', action='store_true',
                          help='Process all Software Releases, even if already installed.')
        only.add_argument('--only-sr', '--only',
                          help='Force the update of a single software release (can be full URL or MD5 hash), '
                               'even if is already installed. This option will make all other '
                               'sofware releases be ignored.')
        return ap


class InstanceCommand(SlapgridCommand):
    """run instance deployment"""

    method_name = 'processComputerPartitionList'
    default_pidfile = '/opt/slapos/slapgrid-cp.pid'
    pidfile_option_name = 'pidfile_instance'

    def get_parser(self, prog_name):
        ap = super(InstanceCommand, self).get_parser(prog_name)

        ap.add_argument('--buildout-debug',
                        action='store_true',
                        help='Run buildout in debug mode (with -D command line switch)')
        only = ap.add_mutually_exclusive_group()
        only.add_argument('--all', action='store_true',
                          help='Process all Computer Partitions.')
        only.add_argument('--only-cp', '--only',
                          help='Update a single or a list of computer partitions '
                               '(ie.:slappartX, slappartY), '
                               'this option will make all other computer partitions be ignored.')
        return ap


class ReportCommand(SlapgridCommand):
    """run instance reports and garbage collection"""

    method_name = 'agregateAndSendUsage'
    default_pidfile = '/opt/slapos/slapgrid-ur.pid'
    pidfile_option_name = 'pidfile_report'

class PromiseCommand(SlapgridCommand):
   """run only promises to test the parition state"""

   method_name = 'processPromiseList'
   default_pidfile = '/opt/slapos/slapgrid-cp.pid'
   pidfile_option_name = 'pidfile_instance'

