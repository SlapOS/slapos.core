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

import argparse
import json
import os.path
import pprint
import warnings

import lxml.etree
import six
import yaml

from slapos.cli.config import ClientConfigCommand
from slapos.client import (ClientConfig, _getSoftwareReleaseFromSoftwareString,
                           init)
from slapos.slap import ResourceNotReady
from slapos.util import (SoftwareReleaseSchema, SoftwareReleaseSerialisation,
                         SoftwareReleaseSchemaValidationError, StrPrettyPrinter)

try:
    from typing import IO, Dict
except ImportError:
    pass


def getParametersFromFile(file, serialisation):
    # type: (IO[str], SoftwareReleaseSerialisation) -> Dict
    extension = os.path.splitext(file.name)[1]
    if extension in ('.yaml', '.yml'):
        params = yaml.safe_load(file)
    elif extension == '.xml':
        tree = lxml.etree.parse(file)
        params = {e.attrib['id']: e.text for e in tree.findall('/parameter')}
        # because the use case of xml files is to copy paste existing XML parameters
        # as found on slapos web interface, we aren't clever regarding the
        # serialisation and assume they are already correct.
        serialisation = None
    else:
        params = json.load(file)

    if serialisation == SoftwareReleaseSerialisation.JsonInXml and list(params.keys()) != ['_']:
        params = {'_': json.dumps(params)}
    return params


def parse_option_dict(options):
    # type: (str) -> Dict
    """
    Parse a list of option strings like foo=bar baz=qux and return a dictionary.
    Will raise if keys are repeated.
    """
    ret = {}
    for option_pair in (options or []):
        key, value = option_pair.split('=', 1)
        if key in ret:
            raise ValueError("Multiple values provided for the same key '%s'" % key)
        ret[key] = value
    return ret


class RequestCommand(ClientConfigCommand):
    """request an instance and get status and parameters of instance"""

    def get_parser(self, prog_name):
        ap = super(RequestCommand, self).get_parser(prog_name)

        ap.add_argument('reference',
                        help='Your instance reference (for now it is its title)')

        ap.add_argument('software_url',
                        help='Your software url')

        # XXX TODO can we do a minimal check for correctness of this argument?
        #          the alternative is a silent failure for mistyped/obsolete/invalid URL

        ap.add_argument('--node',
                        nargs='+',
                        help="Node request option 'option1=value1 option2=value2' (i.e. computer_guid=COMP-1234)")

        ap.add_argument('--type',
                        help='Software type to be requested')

        ap.add_argument('--state',
                        help='State of the requested instance')

        ap.add_argument('--slave',
                        action='store_true',
                        help='Ask for a slave instance')

        ap.add_argument('--force-serialisation',
                        choices=[s.value for s in SoftwareReleaseSerialisation],
                        help='Enforce serialisation of instance parameters when using --parameters-file')

        parameter_args = ap.add_mutually_exclusive_group()

        parameter_args.add_argument(
            '--parameters',
            nargs='+',
            help="Instance parameters, in the form 'option1=value1 option2=value2'.")

        parameter_args.add_argument(
            '--parameters-file',
            type=argparse.FileType('r'),
            help="Instance parameters, in a file.\n"
            "The file will be interpreted as json, yaml or xml depending on the file extension.")
        return ap

    def take_action(self, args):
        args.node = parse_option_dict(args.node)
        args.parameters = parse_option_dict(args.parameters)

        configp = self.fetch_config(args)
        conf = ClientConfig(args, configp)

        local = init(conf, self.app.log)
        do_request(self.app.log, conf, local)


def _validateRequestParameters(software_schema, parameter_dict):
  """Validate requests parameters.

  Default behavior is to fetch schema and warn using `warnings.warn` in case
  of problems
  """
  try:
    software_schema.validateInstanceParameterDict(parameter_dict)
  except SoftwareReleaseSchemaValidationError as e:
    warnings.warn(
      "Request parameters do not validate against schema definition:\n{e}".format(e=e.format_error(indent=2)),
      UserWarning,
    )
  except Exception as e:
    # note that we intentionally catch wide exceptions, so that if anything
    # is wrong with fetching the schema or the schema itself this does not
    # prevent users from requesting instances.
    warnings.warn(
      "Error validating request parameters against schema definition:\n{e.__class__.__name__} {e}".format(e=e),
      UserWarning,
    )

def do_request(logger, conf, local):
    logger.info('Validating request parameters for %s as an instance of %s ...',
                conf.reference, conf.software_url)

    conf.software_url = _getSoftwareReleaseFromSoftwareString(
        logger, conf.software_url, local['product'])

    if conf.software_url in local:
        conf.software_url = local[conf.software_url]

    software_schema = SoftwareReleaseSchema(conf.software_url, conf.type)
    if conf.parameters_file:
        serialisation = conf.force_serialisation
        parameters = getParametersFromFile(conf.parameters_file,
            SoftwareReleaseSerialisation(serialisation) if serialisation else
            software_schema.getSerialisation(strict=True))
    else:
        parameters = conf.parameters

    # special case for the magic git.erp5.org used as an alias
    # for frontend software release that does not have a software.cfg.json
    if conf.software_url not in (
      # no corresponding schema
      'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg',
    ):
      _validateRequestParameters(
        software_schema,
        parameters,
      )

    logger.info('Requesting %s as an instance of %s ...',
                conf.reference, conf.software_url)
    try:
        partition = local['slap'].registerOpenOrder().request(
            software_release=conf.software_url,
            partition_reference=conf.reference,
            partition_parameter_kw=parameters,
            software_type=conf.type,
            filter_kw=conf.node,
            state=conf.state,
            shared=conf.slave
        )
        logger.info('Instance requested.\nState is : %s.', partition.getState())
        logger.info('Connection parameters of instance are:')
        connection_parameter_dict = partition.getConnectionParameterDict()
        if software_schema.getSerialisation() == SoftwareReleaseSerialisation.JsonInXml:
            try:
                connection_parameter_dict = json.loads(connection_parameter_dict['_'])
            except KeyError:
                pass
        logger.info(StrPrettyPrinter().pformat(connection_parameter_dict))
        logger.info('You can rerun the command to get up-to-date information.')
    except ResourceNotReady:
        logger.warning('Instance requested. Master is provisioning it. Please rerun in a '
                       'couple of minutes to get connection information.')
        exit(2)
