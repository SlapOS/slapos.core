##############################################################################
#
# Copyright (c) 2013 Vifib SARL and Contributors. All Rights Reserved.
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

import logging
import pprint
import unittest
import tempfile
import sys
import os
import pkg_resources

from contextlib import contextmanager
from mock import patch, create_autospec
import mock
from slapos.util import sqlite_connect, bytes2str

import slapos.cli.console
import slapos.cli.entry
import slapos.cli.info
import slapos.cli.list
import slapos.cli.supervisorctl
from slapos.cli.proxy_show import do_show, StringIO
from slapos.client import ClientConfig
import slapos.grid.svcbackend
import slapos.proxy
import slapos.slap

import supervisor.supervisorctl

def raiseNotFoundError(*args, **kwargs):
  raise slapos.slap.NotFoundError()

class CliMixin(unittest.TestCase):
  def setUp(self):
    slap = slapos.slap.slap()
    self.local = {'slap': slap}
    self.logger = create_autospec(logging.Logger)
    self.conf = create_autospec(ClientConfig)


class TestCliProxy(CliMixin):
  def test_generateSoftwareProductListFromString(self):
    """
    Test that generateSoftwareProductListFromString correctly parses a parameter
    coming from the configuration file.
    """
    software_product_list_string = """
product1 url1
product2 url2"""
    software_release_url_list = {
        'product1': 'url1',
        'product2': 'url2',
    }
    self.assertEqual(
        slapos.proxy._generateSoftwareProductListFromString(
            software_product_list_string),
        software_release_url_list
    )

  def test_generateSoftwareProductListFromString_emptyString(self):
    self.assertEqual(
        slapos.proxy._generateSoftwareProductListFromString(''),
        {}
    )


class TestCliProxyShow(CliMixin):
  def setUp(self):
    super(TestCliProxyShow, self).setUp()
    self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    self.db_file.close()
    self.conf.database_uri = self.db_file.name
    self.conf.logger = self.logger

    # load database
    schema = bytes2str(pkg_resources.resource_string(
        'slapos.tests',
        os.path.join('test_slapproxy', 'database_dump_version_current.sql')))
    db = sqlite_connect(self.db_file.name)
    db.cursor().executescript(schema)
    db.commit()

    # by default we simulate being invoked with "show all" arguments
    self.conf.computers = True
    self.conf.software = True
    self.conf.partitions = True
    self.conf.slaves = True
    self.conf.params = True
    self.conf.network = True

  def tearDown(self):
    super(TestCliProxyShow, self).tearDown()
    os.remove(self.db_file.name)

  def test_proxy_show(self):
    logger = create_autospec(logging.Logger)
    with mock.patch(
            'slapos.cli.proxy_show.logging.getLogger',
            return_value=logger):
        do_show(self.conf)

    # installed softwares are listed
    logger.info.assert_any_call(
        '      /srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg          slaprunner        available    287375f0cba269902ba1bc50242839d7 ')

    # instance parameters are listed
    # _ parameter is json formatted
    logger.info.assert_any_call(
        '    %s = %s',
        '_',
        '{\n  "monitor-base-url": "",\n  "url": "memcached://10.0.30.235:2003/"\n}')

    # other parameters are displayed as simple string
    logger.info.assert_any_call(
        '    %s = %s',
        'url',
        'http://10.0.30.235:4444/wd/hub')

    # if _ cannot be decoded as json, it is displayed "as is"
    logger.info.assert_any_call(
        '    %s = %s',
        '_',
        u'Ahah this is not json \U0001f61c ')
    # Nothing was output on application logger, because this command uses
    # its own logger.
    self.logger.info.assert_not_called()

  def test_proxy_show_displays_on_stdout(self):
    # we patch logging to make sure our messages are outputed, even with test
    # runners like pytest which allows disabling output
    with patch.object(sys, 'stdout', StringIO()) as stdout, \
        patch.object(sys, 'stderr', StringIO()) as stderr, \
        patch('logging.Logger.isEnabledFor', returned_value=True):
      do_show(self.conf)

    # 287375f0cba269902ba1bc50242839d7 is the hash of an installed software
    # in our setup database
    self.assertIn('287375f0cba269902ba1bc50242839d7', stdout.getvalue())
    self.assertEqual('', stderr.getvalue())

  def test_proxy_show_use_pager(self):
    # we patch logging to make sure our messages are outputed, even with test
    # runners like pytest which allows disabling output
    with patch.object(sys, 'stdout', StringIO()) as stdout, \
        patch.object(sys, 'stderr', StringIO()) as stderr, \
        patch('logging.Logger.isEnabledFor', returned_value=True):
      stdout.isatty = lambda *args: True

      # use a pager that just output to a file.
      tmp = tempfile.NamedTemporaryFile(delete=False)
      self.addCleanup(os.unlink, tmp.name)
      os.environ['PAGER'] = 'cat > {}'.format(tmp.name)

      do_show(self.conf)

    self.assertEqual('', stdout.getvalue())
    self.assertEqual('', stderr.getvalue())
    # our pager was set to output to this temporary file
    with open(tmp.name, 'r') as f:
      self.assertIn('287375f0cba269902ba1bc50242839d7', f.read())


class TestCliNode(CliMixin):

  def test_node_software(self):
    """slapos node software command
    """
    app = slapos.cli.entry.SlapOSApp()

    software_release = mock.MagicMock()
    software_release.getState = mock.Mock(return_value='available')
    software_release.getURI = mock.Mock(return_value='http://example.org/software.cfg')
    software_release.building = mock.Mock()

    computer = mock.MagicMock()
    computer.getSoftwareReleaseList = mock.Mock(return_value=[software_release])

    software = mock.MagicMock()
    from slapos.grid.slapgrid import Slapgrid
    from slapos.slap.slap import slap
    with patch('slapos.cli.slapgrid.check_root_user', return_value=True) as checked_root_user, \
         patch('slapos.cli.slapgrid.setRunning') as write_pid_file, \
         patch.object(Slapgrid, 'checkEnvironmentAndCreateStructure') as checkEnvironmentAndCreateStructure, \
         patch.object(slap, 'registerComputer', return_value=computer) as registerComputer, \
         patch('slapos.grid.slapgrid.Software', return_value=software) as Software, \
         patch('slapos.grid.slapgrid.open') as _open:

      app.run(('node', 'software'))

      checked_root_user.assert_called_once()
      write_pid_file.assert_called_once_with(
          logger=mock.ANY,
          pidfile='/opt/slapos/slapgrid-sr.pid')
      checkEnvironmentAndCreateStructure.assert_called_once()
      registerComputer.assert_called_once()

      software_constructor_call, = Software.call_args_list
      self.assertEqual('http://example.org/software.cfg', software_constructor_call[1]['url'])
      # by default software are not built in debug mode
      self.assertFalse(software_constructor_call[1]['buildout_debug'])

      software.install.assert_called_once()

  def test_node_instance(self):
    """slapos node instance command
    """
    app = slapos.cli.entry.SlapOSApp()

    from slapos.grid.slapgrid import Slapgrid
    with patch('slapos.cli.slapgrid.check_root_user', return_value=True) as checked_root_user, \
         patch('slapos.cli.slapgrid.setRunning') as write_pid_file, \
         patch.object(Slapgrid, 'processComputerPartitionList') as processComputerPartitionList:

      app.run(('node', 'instance'))

      checked_root_user.assert_called_once()
      write_pid_file.assert_called_once_with(
          logger=mock.ANY,
          pidfile='/opt/slapos/slapgrid-cp.pid')
      processComputerPartitionList.assert_called_once()


class TestCliList(CliMixin):
  def test_list(self):
    """
    Test "slapos list" command output.
    """
    return_value = {
      'instance1': slapos.slap.SoftwareInstance(_title='instance1', _software_release_url='SR1'),
      'instance2': slapos.slap.SoftwareInstance(_title='instance2', _software_release_url='SR2'),
    }
    with patch.object(slapos.slap.slap, 'getOpenOrderDict', return_value=return_value) as _:
      slapos.cli.list.do_list(self.logger, None, self.local)

    self.logger.info.assert_any_call('%s %s', 'instance1', 'SR1')
    self.logger.info.assert_any_call('%s %s', 'instance2', 'SR2')

  def test_emptyList(self):
    with patch.object(slapos.slap.slap, 'getOpenOrderDict', return_value={}) as _:
      slapos.cli.list.do_list(self.logger, None, self.local)

    self.logger.info.assert_called_once_with('No existing service.')

@patch.object(slapos.slap.slap, 'registerOpenOrder', return_value=slapos.slap.OpenOrder())
class TestCliInfo(CliMixin):
  def test_info(self, _):
    """
    Test "slapos info" command output.
    """
    setattr(self.conf, 'reference', 'instance1')
    instance = slapos.slap.SoftwareInstance(
        _software_release_url='SR1',
        _requested_state = 'mystate',
        _connection_dict = {'myconnectionparameter': 'value1'},
        _parameter_dict = {'myinstanceparameter': 'value2'}
    )
    with patch.object(slapos.slap.OpenOrder, 'getInformation', return_value=instance):
      slapos.cli.info.do_info(self.logger, self.conf, self.local)

    self.logger.info.assert_any_call(pprint.pformat(instance._parameter_dict))
    self.logger.info.assert_any_call('Software Release URL: %s', instance._software_release_url)
    self.logger.info.assert_any_call('Instance state: %s', instance._requested_state)
    self.logger.info.assert_any_call(pprint.pformat(instance._parameter_dict))
    self.logger.info.assert_any_call(pprint.pformat(instance._connection_dict))

  def test_unknownReference(self, _):
    """
    Test "slapos info" command output in case reference
    of service is not known.
    """
    setattr(self.conf, 'reference', 'instance1')
    with patch.object(slapos.slap.OpenOrder, 'getInformation', side_effect=raiseNotFoundError):
      slapos.cli.info.do_info(self.logger, self.conf, self.local)

    self.logger.warning.assert_called_once_with('Instance %s does not exist.', self.conf.reference)


@patch.object(supervisor.supervisorctl, 'main')
class TestCliSupervisorctl(CliMixin):
  def test_allow_supervisord_launch(self, _):
    """
    Test that "slapos node supervisorctl" tries to launch supervisord
    """
    instance_root = '/foo/bar'
    with patch.object(slapos.grid.svcbackend, 'launchSupervisord') as launchSupervisord:
      slapos.cli.supervisorctl.do_supervisorctl(self.logger, instance_root, ['status'], False)
      launchSupervisord.assert_any_call(instance_root=instance_root, logger=self.logger)

  def test_forbid_supervisord_launch(self, _):
    """
    Test that "slapos node supervisorctl" does not try to launch supervisord
    """
    instance_root = '/foo/bar'
    with patch.object(slapos.grid.svcbackend, 'launchSupervisord') as launchSupervisord:
      slapos.cli.supervisorctl.do_supervisorctl(self.logger, instance_root, ['status'], True)
      self.assertFalse(launchSupervisord.called)


class TestCliConsole(unittest.TestCase):

  script = """\
print(request('software_release', 'instance').getInstanceParameterDict()['parameter_name'])
"""

  @contextmanager
  def _test_console(self):
    cp = slapos.slap.ComputerPartition('computer_%s' % self.id(), 'partition_%s' % self.id())
    cp._parameter_dict = {'parameter_name': 'parameter_value'}
    with patch.object(slapos.slap.OpenOrder, 'request',
                      return_value = cp) as mock_request, \
         patch.object(sys, 'stdout', StringIO()) as app_stdout, \
         tempfile.NamedTemporaryFile() as config_file:
      config_file.write(b'[slapos]\nmaster_url=null\n')
      config_file.flush()
      yield slapos.cli.entry.SlapOSApp(), config_file.name
      mock_request.assert_called_once_with(
          'software_release', 'instance')
      self.assertIn('parameter_value', app_stdout.getvalue())

  def test_console_interactive(self):
    with self._test_console() as (app, config_file), \
         patch.object(sys, 'stdin', StringIO(self.script)):
      app.run(('console', '--cfg', config_file))

  def test_console_script(self):
    with self._test_console() as (app, config_file), \
         tempfile.NamedTemporaryFile('w') as script:
      script.write(self.script)
      script.flush()
      app.run(('console', '--cfg', config_file, script.name))
