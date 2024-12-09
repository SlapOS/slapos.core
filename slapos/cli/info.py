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

import json
import pprint
import sys

from slapos.cli.command import resetLogger
from slapos.cli.config import ClientConfigCommand
from slapos.client import init, ClientConfig
from slapos.slap import ResourceNotReady, NotFoundError

from slapos.util import (
  SoftwareReleaseSchema,
  SoftwareReleaseSerialisation,
  StrPrettyPrinter,
  xml2dict,
)


class InfoCommand(ClientConfigCommand):
    """get status, software_release and parameters of an instance"""

    def get_parser(self, prog_name):
        ap = super(InfoCommand, self).get_parser(prog_name)

        ap.add_argument('reference',
                        help='Your instance reference')

        ap.add_argument('--news',
                        action='store_true',
                        help='Include raw news in output')

        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        conf = ClientConfig(args, configp)

        local = init(conf, self.app.log)
        exit_code = do_info(self.app.log, conf, local)
        if exit_code != 0:
          exit(exit_code)


def do_info(logger, conf, local):
    try:
        instance = local['slap'].registerOpenOrder().getInformation(
            partition_reference=conf.reference,
        )
    except ResourceNotReady:
        logger.warning('Instance does not exist or is not ready yet.')
        return(2)
    except NotFoundError:
        logger.warning('Instance %s does not exist.', conf.reference)
        return(2)

    software_schema = SoftwareReleaseSchema(
        instance._software_release_url,
        getattr(instance, '_software_type', None))
    if isinstance(instance._connection_dict, list):
        # this is slapos master connection dict
        connection_parameter_dict = {}
        for param in instance._connection_dict:
            connection_parameter_dict[param['connection_key']] = param['connection_value']
    else:
        # this is slapproxy connection dict
        connection_parameter_dict = xml2dict(instance._connection_dict)
    if software_schema.getSerialisation() == SoftwareReleaseSerialisation.JsonInXml:
        if '_' in connection_parameter_dict:
            connection_parameter_dict = json.loads(connection_parameter_dict['_'])


    info = {
        'software-url': instance._software_release_url,
        'software-type': instance._source_reference,
        'shared': bool(instance._root_slave),
        'requested-state': instance._requested_state,
        'instance-parameters': instance._parameter_dict,
        'connection-parameters': connection_parameter_dict,
    }

    try:
        news = instance._news['instance']
    except (AttributeError, KeyError):
        info['status'] = 'unsupported'
    else:
      # 2 bits : 00 -> none, 01 -> green, 10 -> red, 11 -> orange
      status = 0b00
      for e in news:
          text = e.get('text', '')
          if text.startswith('#access'):
              status |= 0b01
          elif text.startswith('#error'):
              status |= 0b10
          if status == 0b11:
              break
      info['status'] = ('none', 'green', 'red', 'orange')[status]
      if conf.news:
          info['news'] = news

    with resetLogger(logger):
      logger.info(json.dumps(info, indent=2))

