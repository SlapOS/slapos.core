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

import logging
import sys
import six

from slapos.cli.config import ClientConfigCommand
from slapos.client import init, ClientConfig

def resetLogger(logger):
    """Remove all formatters, log files, etc."""
    if not getattr(logger, 'parent', None):
      return
    handler = logger.parent.handlers[0]
    logger.parent.removeHandler(handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))

class ListCommand(ClientConfigCommand):
    """request an instance and get status and parameters of instance"""

    def get_parser(self, prog_name):
        ap = super(ListCommand, self).get_parser(prog_name)
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        conf = ClientConfig(args, configp)

        local = init(conf, self.app.log)
        do_list(self.app.log, conf, local)


def do_list(logger, conf, local):
    resetLogger(logger)
    # XXX catch exception
    instance_dict = local['slap'].getOpenOrderDict()
    if instance_dict == {}:
      logger.info('No existing service.')
      return
    logger.info('List of services:')
    for title, instance in six.iteritems(instance_dict):
      logger.info('%s %s', title, instance._software_release_url)
