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

from slapos.cli.config import ConfigCommand
from slapos.proxy import do_proxy, ProxyConfig


class ProxyStartCommand(ConfigCommand):
    """
    minimalist, stand-alone SlapOS Master
    """

    def get_parser(self, prog_name):
        ap = super(ProxyStartCommand, self).get_parser(prog_name)

        ap.add_argument('-u', '--database-uri',
                        help='URI for sqlite database')
        ap.add_argument('--port',
                        help='Port to use')
        ap.add_argument('--host',
                        help='Host to use')

        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)

        conf = ProxyConfig(logger=self.app.log)

        conf.mergeConfig(args, configp)

        if not self.app.options.log_file and hasattr(conf, 'log_file'):
            # no log file is provided by argparser,
            # we set up the one from config
            file_handler = logging.FileHandler(conf.log_file)
            formatter = logging.Formatter(self.app.LOG_FILE_MESSAGE_FORMAT)
            file_handler.setFormatter(formatter)
            self.app.log.addHandler(file_handler)

        conf.setConfig()

        do_proxy(conf=conf)
