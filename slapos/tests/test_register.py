##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import httmock
import mock
import os
import random
import shutil
import string
import tempfile
import unittest
from argparse import Namespace
from six.moves.urllib import parse

import slapos.slap
from slapos.cli.register import RegisterCommand, RegisterConfig, fetch_configuration_template, do_register
from slapos.cli.entry import SlapOSApp

class TestRegister(unittest.TestCase):
  """ Tests for slapos.cli.register

    XXX There is a lack of tests for register, so include more.
  """

  def setUp(self):
    self.slap = slapos.slap.slap()
    self.app = SlapOSApp()
    self.temp_dir = tempfile.mkdtemp()
    self.computer_id = 'COMP-%s' % random.randrange(10000)
    self.certificate = 'CN=%s/emailAddress=admin@vifib.org' % self.computer_id
    self.key = 'key_test_%s' % ''.join(random.choice(string.ascii_lowercase) for i in range(64))
    self.default_args=[
        'test-computer',
        '--token', 'token-test'
        ]

  def tearDown(self):
    if os.path.exists(self.temp_dir):
      shutil.rmtree(self.temp_dir)

  def request_handler(self, url, req):
    """
    Define _callback.
    Will register global sequence of message, sequence by partition
    and error and error message by partition
    """
    #self.sequence.append(url.path)
    if req.method == 'GET':
      qs = parse.parse_qs(url.query)
    else:
      qs = parse.parse_qs(req.body)
    print("DEBUG THOMAS")
    print(url)
    print(req)

    if url.path == '/Person_requestComputer':
      return {
              'status_code': 200,
              'content': {'certificate': self.certificate, 'key': self.key}
              }

  def getConf(self, args):
    cmd = RegisterCommand(self.app, Namespace())
    cmd_parser = cmd.get_parser("slapos node register for test")
    parsed_args = cmd_parser.parse_args(args)
    conf = RegisterConfig(logger=self.app.log)
    conf.setConfig(parsed_args)
    return conf

  def test_fetch_configuration(self):
    """ Simple test to Fetch the configuration template
    """
    template = fetch_configuration_template()
    self.assertNotEqual("", template)

    for entry in  ['computer_id',
             'master_url',
             'key_file',
             'cert_file',
             'certificate_repository_path',
             'interface_name',
             'ipv4_local_network',
             'partition_amount',
             'create_tap']:
      self.assertTrue(entry in template, "%s is not in template (%s)" % (entry, template))

  def test_default_token_rejected(self):
    """ Make sure that the token for test if rejected by default
    """
    conf = self.getConf(self.default_args)
    with self.assertRaises(SystemExit) as cm:
      do_register(conf)
    self.assertEqual(cm.exception.code, 1)

  def test_write_configuration(self):
    """ Simple test to see if we can write the configuration file
    """
    conf = self.getConf(self.default_args)
    # we manually set the parameters below because we mock the function COMPConfig
    # indeed, we don't want to put the config file in '/etc/opt/slapos'
    conf.slapos_configuration = self.temp_dir
    conf.computer_id = self.computer_id
    conf.certificate = self.certificate
    conf.key = self.key
    with httmock.HTTMock(self.request_handler), \
         mock.patch.object(RegisterConfig, 'COMPConfig') as COMPConfigMock, \
         mock.patch('slapos.cli.register.save_former_config') as save_former_config_mock:
      return_code = do_register(conf)
      COMPConfigMock.assert_called_with(
              slapos_configuration = '/etc/opt/slapos/',
              computer_id = self.computer_id,
              certificate = self.certificate,
              key = self.key)
      save_former_config_mock.assert_called()
    self.assertEquals(0, return_code)
    self.assertTrue(
      os.path.exists('%s/slapos.cfg' % self.temp_dir))
    config_content = open('%s/slapos.cfg' % self.temp_dir).read()
    self.assertIn('computer_id = %s' % self.computer_id, config_content)
