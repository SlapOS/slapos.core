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

import re
import os
import sys
import json
from six.moves import input

import requests

from slapos.cli.config import ClientConfigCommand
from slapos.util import mkdir_p


class ConfigureClientCommand(ClientConfigCommand):
    """
    configure slapos client with an existing account
    """

    def get_parser(self, prog_name):
        ap = super(ConfigureClientCommand, self).get_parser(prog_name)

        ap.add_argument('--master-url',
                        default='https://slap.vifib.com',
                        help='URL of SlapOS Master REST API'
                             ' (default: %(default)s)')

        ap.add_argument('--master-url-web',
                        default='https://slapos.vifib.com',
                        help='URL of SlapOS Master webservice to register certificates'
                             ' (default: %(default)s)')

        ap.add_argument('--token',
                        help="SlapOS 'credential security' authentication token "
                             "(if this parameter is omitted, the token will be prompted during configuration)")

        return ap

    def take_action(self, args):
        do_configure_client(logger=self.app.log,
                            master_url_web=args.master_url_web,
                            token=args.token,
                            config_path=self.config_path(args),
                            master_url=args.master_url)


def get_certificate_key_pair(logger, master_url_web, token):
    req = requests.post('/'.join([master_url_web, 'Person_getCertificate']),
                        data={},
                        headers={'X-Access-Token': token},
                        verify=False)

    if req.status_code == 403:
        logger.critical('Access denied to the SlapOS Master. '
                        'Please check the authentication token or require a new one.')
        sys.exit(1)

    req.raise_for_status()

    json_dict = json.loads(req.text)
    return json_dict["certificate"], json_dict["key"]

def fetch_configuration_template():
    template_path = os.path.join("/".join(__file__.split('/')[:-2]), 'slapos-client.cfg.example')
    with open(template_path, 'r') as fout:
      slapos_node_configuration_template = fout.read()
    return slapos_node_configuration_template

def do_configure_client(logger, master_url_web, token, config_path, master_url):
    while not token:
        token = input('Credential security token: ').strip()

    # Check for existence of previous configuration, certificate or key files
    # where we expect to create them. If so, ask the use to manually remove them.

    if os.path.exists(config_path):
        logger.critical('There is a file in %s. '
                        'Please remove it before creating a new configuration.', config_path)
        sys.exit(1)

    basedir = os.path.dirname(config_path)
    if not os.path.isdir(basedir):
        logger.debug('Creating directory %s', basedir)
        mkdir_p(basedir, mode=0o700)

    cert_path = os.path.join(basedir, 'client.crt')
    if os.path.exists(cert_path):
        logger.critical('There is a file in %s. '
                        'Please remove it before creating a new certificate.', cert_path)
        sys.exit(1)

    key_path = os.path.join(basedir, 'client.key')
    if os.path.exists(key_path):
        logger.critical('There is a file in %s. '
                        'Please remove it before creating a new key.', key_path)
        sys.exit(1)

    # retrieve a template for the configuration file

    cfg = fetch_configuration_template()

    cfg = re.sub('master_url = .*', 'master_url = %s' % master_url, cfg)
    cfg = re.sub('cert_file = .*', 'cert_file = %s' % cert_path, cfg)
    cfg = re.sub('key_file = .*', 'key_file = %s' % key_path, cfg)

    # retrieve and parse the certicate and key

    certificate, key = get_certificate_key_pair(logger, master_url_web, token)

    # write everything

    with os.fdopen(os.open(config_path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600), 'w') as fout:
        logger.debug('Writing configuration to %s', config_path)
        fout.write(cfg)

    with os.fdopen(os.open(cert_path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600), 'w') as fout:
        logger.debug('Writing certificate to %s', cert_path)
        fout.write(certificate)

    with os.fdopen(os.open(key_path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600), 'w') as fout:
        logger.debug('Writing key to %s', key_path)
        fout.write(key)

    logger.info('SlapOS client configuration written to %s', config_path)
