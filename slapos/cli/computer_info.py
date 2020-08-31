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
import pprint
import sys

from slapos.cli.config import ClientConfigCommand
from slapos.client import init, ClientConfig
from slapos.slap import ResourceNotReady, NotFoundError


def resetLogger(logger):
    """Remove all formatters, log files, etc."""
    if not getattr(logger, 'parent', None):
      return
    handler = logger.parent.handlers[0]
    logger.parent.removeHandler(handler)
    logger.addHandler(logging.StreamHandler(sys.stdout))

class InfoCommand(ClientConfigCommand):
    """get information of an computer"""

    def get_parser(self, prog_name):
        ap = super(InfoCommand, self).get_parser(prog_name)

        ap.add_argument('reference',
                        help='Your computer reference')

        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        conf = ClientConfig(args, configp)

        local = init(conf, self.app.log)
        exit_code = do_info(self.app.log, conf, local)
        if exit_code != 0:
          exit(exit_code)


def do_info(logger, conf, local):
    resetLogger(logger)
    try:
        computer = local['slap'].registerComputer(conf.reference).getInformation()
    except ResourceNotReady:
        logger.warning('Computer does not exist or is not ready yet.')
        return(2)
    except NotFoundError:
        logger.warning('Computer %s does not exist.', conf.reference)
        return(2)

    logger.info('Computer Reference: %s', computer._reference)
    logger.info('Computer Title    : %s', computer._title)

