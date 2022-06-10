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

import json
import logging
import pprint
import unittest
import tempfile
import shutil
import socket
import textwrap
import sys
import os
import pkg_resources

from contextlib import contextmanager
from mock import patch, create_autospec
import mock
from slapos.util import sqlite_connect, bytes2str
from slapos.slap.slap import DEFAULT_SOFTWARE_TYPE

import slapos.cli.console
import slapos.cli.entry
import slapos.cli.info
import slapos.cli.list
import slapos.cli.computer_info
import slapos.cli.computer_list
import slapos.cli.computer_token
import slapos.cli.supervisorctl
import slapos.cli.request
from slapos.cli.proxy_show import do_show, StringIO
from slapos.cli.cache_binarysr import do_lookup as cache_binarysr_do_lookup
from slapos.cli.cache_url import do_lookup as cache_url_do_lookup
from slapos.cli.cache_pypi import do_lookup as cache_pypi_do_lookup
from slapos.client import ClientConfig
from slapos.slap import SoftwareProductCollection
import slapos.grid.svcbackend
import slapos.proxy
import slapos.slap

import supervisor.supervisorctl

signature_certificate_list = """-----BEGIN CERTIFICATE-----
MIIB9jCCAV+gAwIBAgIJAKRvzcy7OH0UMA0GCSqGSIb3DQEBBQUAMBMxETAPBgNV
BAMMCENPTVAtNzcyMCAXDTEyMDgxMDE1NDI1MVoYDzIxMTIwNzE3MTU0MjUxWjAT
MREwDwYDVQQDDAhDT01QLTc3MjCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEA
o7aipd6MbnuGDeR1UJUjuMLQUariAyQ2l2ZDS6TfOwjHiPw/mhzkielgk73kqN7A
sUREx41eTcYCXzTq3WP3xCLE4LxLg1eIhd4nwNHj8H18xR9aP0AGjo4UFl5BOMa1
mwoyBt3VtfGtUmb8whpeJgHhqrPPxLoON+i6fIbXDaUCAwEAAaNQME4wHQYDVR0O
BBYEFEfjy3OopT2lOksKmKBNHTJE2hFlMB8GA1UdIwQYMBaAFEfjy3OopT2lOksK
mKBNHTJE2hFlMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEAaNRx6YN2
M/p3R8/xS6zvH1EqJ3FFD7XeAQ52WuQnKSREzuw0dsw12ClxjcHiQEFioyTiTtjs
5pW18Ry5Ie7iFK4cQMerZwWPxBodEbAteYlRsI6kePV7Gf735Y1RpuN8qZ2sYL6e
x2IMeSwJ82BpdEI5niXxB+iT0HxhmR+XaMI=
-----END CERTIFICATE-----
"""

def raiseNotFoundError(*args, **kwargs):
  raise slapos.slap.NotFoundError()

class CliMixin(unittest.TestCase):
  def setUp(self):
    slap = slapos.slap.slap()
    self.logger = create_autospec(logging.Logger)
    self.local = {'slap': slap, 'product': SoftwareProductCollection(self.logger, slap)}
    self.conf = create_autospec(ClientConfig)
    self.sign_cert_list = signature_certificate_list

class TestCliCacheBinarySr(CliMixin):

  test_url = "https://lab.nexedi.com/nexedi/slapos/raw/1.0.102/software/slaprunner/software.cfg"
  def test_cached_binary(self):
    self.assertEqual(0, cache_binarysr_do_lookup(
        self.logger,
        cache_dir="http://dir.shacache.org",
        cache_url="http://shacache.org",
        software_url=self.test_url,
        signature_certificate_list=self.sign_cert_list))

    self.logger.info.assert_any_call('Software URL: %s',
            u'https://lab.nexedi.com/nexedi/slapos/raw/1.0.102/software/slaprunner/software.cfg')
    self.logger.info.assert_any_call('MD5:          %s', 'cccdc51a07e8c575c880f2d70dd4d458')
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------')
    self.logger.info.assert_any_call(u'    multiarch     distribution version    id   compatible? verified? ')
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------')
    self.logger.info.assert_any_call(u' x86_64-linux-gnu CentOS Linux 7.5.1804  Core       no        yes    ')
    self.logger.info.assert_any_call(u' x86_64-linux-gnu    Ubuntu     18.04   bionic      no        yes    ')
    # Omit some lines as it may fail depending of the OS
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------')

  def test_uncached_binary(self):
    self.assertEqual(1, cache_binarysr_do_lookup(
        self.logger,
        cache_dir="http://dir.shacache.org",
        cache_url="http://shacache.org",
        software_url="this_is_uncached_url",
        signature_certificate_list=self.sign_cert_list))

    self.logger.critical.assert_any_call(
        'Error while looking object %s', 'this_is_uncached_url', exc_info=True)

  def test_bad_cache_dir(self):
    self.assertEqual(1, cache_binarysr_do_lookup(
        self.logger,
        cache_dir="http://xxx.shacache.org",
        cache_url="http://shacache.org",
        software_url=self.test_url,
        signature_certificate_list=self.sign_cert_list))

    self.logger.critical.assert_any_call(
        'Error while looking object %s',
        'https://lab.nexedi.com/nexedi/slapos/raw/1.0.102/software/slaprunner/software.cfg',
        exc_info=True)

  def test_unverified_signature(self):
      with mock.patch(
              'slapos.grid.networkcache.machine_info_tuple',
              return_value=('x86_64-linux-gnu', ('debian', '8.10', ''))):
          self.assertEqual(0, cache_binarysr_do_lookup(
              self.logger,
              cache_dir="http://dir.shacache.org",
              cache_url="http://shacache.org",
              software_url=self.test_url,
              signature_certificate_list=""))

      self.logger.info.assert_any_call('Software URL: %s',
              u'https://lab.nexedi.com/nexedi/slapos/raw/1.0.102/software/slaprunner/software.cfg')
      self.logger.info.assert_any_call('MD5:          %s', 'cccdc51a07e8c575c880f2d70dd4d458')
      self.logger.info.assert_any_call(u'---------------------------------------------------------------------')
      self.logger.info.assert_any_call(u'    multiarch     distribution version    id   compatible? verified? ')
      self.logger.info.assert_any_call(u'---------------------------------------------------------------------')
      self.logger.info.assert_any_call(u' x86_64-linux-gnu CentOS Linux 7.5.1804  Core       no         no    ')
      self.logger.info.assert_any_call(u' x86_64-linux-gnu    Ubuntu     18.04   bionic      no         no    ')
      self.logger.info.assert_any_call(u' x86_64-linux-gnu    debian      8.10              yes         no    ')
      self.logger.info.assert_any_call(u'---------------------------------------------------------------------')


class TestCliCacheUrl(CliMixin):

  test_url = "https://ftp.gnu.org/gnu/aspell/aspell-0.60.7.tar.gz"
  cache_dir = "http://dir.shacache.org"
  def test_cached_url(self):
    self.assertEqual(0, cache_url_do_lookup(
        self.logger,
        cache_dir=self.cache_dir,
        cache_url="http://shacache.org",
        url=self.test_url,
        signature_certificate_list=""))


    self.logger.info.assert_any_call('Software source URL: %s', self.test_url)
    self.logger.info.assert_any_call('SHADIR URL: %s/%s\n', self.cache_dir, "file-urlmd5:f213fcd8e97aa729f685b8cb71b976a7")
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call(u'                         url                                                                                      sha512                                                              signed ')
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call(u' https://ftp.gnu.org/gnu/aspell/aspell-0.60.7.tar.gz 6f5fcd1c29164ee18f205594b66f382b51d19b17686293a931ca92c1442d3f7228627ca7d604d860551d0d367ac34dfb2ae34170a844f51e84e390fb1edc4535 False  ')
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')

  def test_cached_signed_url(self):
    self.assertEqual(0, cache_url_do_lookup(
        self.logger,
        cache_dir=self.cache_dir,
        cache_url="http://shacache.org",
        url=self.test_url,
        signature_certificate_list=signature_certificate_list))


    self.logger.info.assert_any_call('Software source URL: %s', self.test_url)
    self.logger.info.assert_any_call('SHADIR URL: %s/%s\n', self.cache_dir, "file-urlmd5:f213fcd8e97aa729f685b8cb71b976a7")
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call(u'                         url                                                                                      sha512                                                              signed ')
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call(u' https://ftp.gnu.org/gnu/aspell/aspell-0.60.7.tar.gz 6f5fcd1c29164ee18f205594b66f382b51d19b17686293a931ca92c1442d3f7228627ca7d604d860551d0d367ac34dfb2ae34170a844f51e84e390fb1edc4535  True  ')
    self.logger.info.assert_any_call(u'---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')

  def test_uncached_url(self):
    self.assertEqual(1, cache_url_do_lookup(
        self.logger,
        cache_dir="http://dir.shacache.org",
        cache_url="http://shacache.org",
        url="this_is_uncached_url",
        signature_certificate_list=""))

    self.logger.info.assert_any_call('Object not found in cache.')

  def test_bad_cache_dir(self):
    self.assertEqual(1, cache_url_do_lookup(
        self.logger,
        cache_dir="http://xxx.shacache.org",
        cache_url="http://shacache.org",
        url=self.test_url,
        signature_certificate_list=""))

    self.logger.critical.assert_any_call('Error while looking object %s', self.test_url, exc_info=True)

class TestCliCachePypi(CliMixin):

  egg_name = "pytz"
  egg_version = "2016.10"
  cache_dir = "http://dir.shacache.org"
  def test_cached_pypi(self):
    self.assertEqual(0, cache_pypi_do_lookup(
        self.logger,
        cache_dir=self.cache_dir,
        cache_url="http://shacache.org",
        name=self.egg_name,
        version=self.egg_version,
        signature_certificate_list=""))


    self.logger.info.assert_any_call('Python egg %s version %s', self.egg_name, self.egg_version)
    self.logger.info.assert_any_call('SHADIR URL: %s/%s\n', self.cache_dir, 'pypi:{}={}'.format(self.egg_name, self.egg_version))
    self.logger.info.assert_any_call('----------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call('        basename                                                                     sha512                                                              signed ')
    self.logger.info.assert_any_call('----------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call(' pytz-2016.10-py2.7.egg e072d146c42cb2efde946eef1d37ce6f8cb8eec6f6f928f6d57bb5312578bfa0031dcdbd816318015d765886bb64c02e1772adf7309142bc80324a4155b4ae8b False  ')
    self.logger.info.assert_any_call(' pytz-2016.10-py2.7.egg e072d146c42cb2efde946eef1d37ce6f8cb8eec6f6f928f6d57bb5312578bfa0031dcdbd816318015d765886bb64c02e1772adf7309142bc80324a4155b4ae8b False  ')
    self.logger.info.assert_any_call('----------------------------------------------------------------------------------------------------------------------------------------------------------------')


  def test_cached_signed_url(self):
    self.assertEqual(0, cache_pypi_do_lookup(
        self.logger,
        cache_dir=self.cache_dir,
        cache_url="http://shacache.org",
        name=self.egg_name,
        version=self.egg_version,
        signature_certificate_list=signature_certificate_list))


    self.logger.info.assert_any_call('Python egg %s version %s', self.egg_name, self.egg_version)
    self.logger.info.assert_any_call('SHADIR URL: %s/%s\n', self.cache_dir, 'pypi:{}={}'.format(self.egg_name, self.egg_version))
    self.logger.info.assert_any_call('----------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call('        basename                                                                     sha512                                                              signed ')
    self.logger.info.assert_any_call('----------------------------------------------------------------------------------------------------------------------------------------------------------------')
    self.logger.info.assert_any_call(' pytz-2016.10-py2.7.egg e072d146c42cb2efde946eef1d37ce6f8cb8eec6f6f928f6d57bb5312578bfa0031dcdbd816318015d765886bb64c02e1772adf7309142bc80324a4155b4ae8b  True  ')
    self.logger.info.assert_any_call(' pytz-2016.10-py2.7.egg e072d146c42cb2efde946eef1d37ce6f8cb8eec6f6f928f6d57bb5312578bfa0031dcdbd816318015d765886bb64c02e1772adf7309142bc80324a4155b4ae8b False  ')
    self.logger.info.assert_any_call('----------------------------------------------------------------------------------------------------------------------------------------------------------------')

  def test_uncached_url(self):
    self.assertEqual(1, cache_pypi_do_lookup(
        self.logger,
        cache_dir="http://dir.shacache.org",
        cache_url="http://shacache.org",
        name="not-existing-egg",
        version=self.egg_version,
        signature_certificate_list=""))

    self.logger.info.assert_any_call('Object not found in cache.')

  def test_bad_cache_dir(self):
    self.assertEqual(1, cache_pypi_do_lookup(
        self.logger,
        cache_dir="http://xxx.shacache.org",
        cache_url="http://shacache.org",
        name=self.egg_name,
        version=self.egg_version,
        signature_certificate_list=""))

    self.logger.critical.assert_any_call('Error while looking egg %s version %s', self.egg_name, self.egg_version, exc_info=True)

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


class TestCliBoot(CliMixin):
  def test_node_boot(self):
    # initialize instance root, with a timestamp in a partition
    temp_dir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, temp_dir)
    instance_root = os.path.join(temp_dir, 'instance')
    partition_base_name = 'partition'
    os.mkdir(instance_root)
    os.mkdir(os.path.join(instance_root, partition_base_name + '1'))
    timestamp = os.path.join(
        instance_root, partition_base_name + '1', '.timestamp')
    with open(timestamp, 'w') as f:
      f.write("1578552471")

    # make a config file using this instance root
    with tempfile.NamedTemporaryFile(mode='w') as slapos_conf:
      slapos_conf.write(
          textwrap.dedent(
              """\
              [slapos]
              instance_root = {instance_root}
              master_url = https://slap.vifib.com/

              [slapformat]
              partition_base_name = {partition_base_name}
              interface_name = interface_name_from_config
              """).format(**locals()))
      slapos_conf.flush()

      # run slapos node boot
      app = slapos.cli.entry.SlapOSApp()
      with patch('slapos.cli.boot.check_root_user', return_value=True) as check_root_user,\
          patch('slapos.cli.boot.SlapOSApp') as SlapOSApp,\
          patch('slapos.cli.boot.ConfigCommand.config_path', return_value=slapos_conf.name), \
          patch(
              'slapos.cli.boot.netifaces.ifaddresses',
              return_value={socket.AF_INET6: ({'addr': '2000::1'},),},) as ifaddresses,\
          patch('slapos.cli.boot._ping_hostname', return_value=1) as _ping_hostname:
        app.run(('node', 'boot'))

      # boot command runs as root
      check_root_user.assert_called_once()
      # it waits for interface to have an IPv6 address
      ifaddresses.assert_called_once_with('interface_name_from_config')
      # then ping master hostname to wait for connectivity
      _ping_hostname.assert_called_once_with('slap.vifib.com')
      # then format and bang
      SlapOSApp().run.assert_any_call(['node', 'format', '--now', '--verbose'])
      SlapOSApp().run.assert_any_call(['node', 'bang', '-m', 'Reboot'])

      # timestamp files have been removed
      self.assertFalse(os.path.exists(timestamp),
              timestamp)

  def test_boot_failure(self):
    # In this test, the network interfaces will not have
    # IP address at the beginning, the global IPv6 address only appears later,
    # then format and bang commands will fail two time each.
    # `slapos node boot` command retries on failures.

    app = slapos.cli.entry.SlapOSApp()
    net1 = {socket.AF_INET: ({'addr': '127.0.0.1'},),}
    net2 = {socket.AF_INET: ({'addr': '127.0.0.1'},), socket.AF_INET6: ({'addr': 'fe80::1'},),}
    net3 = {socket.AF_INET: ({'addr': '127.0.0.1'},), socket.AF_INET6: ({'addr': 'fe80::1'}, {'addr': '2000::1'},),}
    with patch('slapos.cli.boot.check_root_user', return_value=True) as check_root_user,\
        patch('slapos.cli.boot.sleep') as sleep,\
        patch('slapos.cli.boot.netifaces.ifaddresses',
              side_effect=[net1, net2, net3]),\
        patch('slapos.cli.boot._ping_hostname', return_value=0),\
        patch('slapos.cli.format.check_root_user', return_value=True),\
        patch('slapos.cli.format.logging.FileHandler', return_value=logging.NullHandler()),\
        patch('slapos.cli.bang.check_root_user', return_value=True),\
        patch('slapos.cli.format.do_format', side_effect=[Exception, Exception, None]) as do_format,\
        patch('slapos.cli.bang.do_bang', side_effect=[Exception, Exception, None]) as do_bang:

      app.run(('node', 'boot'))

    check_root_user.assert_called_once()

    self.assertEqual(do_format.call_count, 3)
    self.assertEqual(do_bang.call_count, 3)

    # between retries of ping, we sleep 5 seconds
    # between retries of bang, we sleep 15 seconds
    self.assertEqual(sleep.mock_calls, [mock.call(5)]*2 + [mock.call(15)]*4)

    # we have only one logger on the console
    from slapos.cli import coloredlogs
    self.assertEqual(
        len([
            h for h in logging.getLogger('').handlers
            if isinstance(h, coloredlogs.ColoredStreamHandler)
        ]), 1)


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

  def test_node_prune(self):
    """slapos node prune command
    """
    app = slapos.cli.entry.SlapOSApp()

    with patch('slapos.cli.prune.check_root_user', return_value=True) as checked_root_user, \
         patch('slapos.cli.prune.setRunning') as write_pid_file, \
         patch('slapos.cli.prune.merged_options', return_value={
            'shared_part_list': 'something',
            'root_check': 'true',
            'pidfile_software': 'pidfile_software.pid',
         }), \
         patch('slapos.cli.prune.do_prune') as do_prune:

      app.run(('node', 'prune'))

      checked_root_user.assert_called_once()
      write_pid_file.assert_called_once_with(
          logger=mock.ANY,
          pidfile='pidfile_software.pid')
      do_prune.assert_called_once()


class TestCliList(CliMixin):
  def test_list(self):
    """
    Test "slapos service list" command output.
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
    Test "slapos service info" command output.
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
    Test "slapos service info" command output in case reference
    of service is not known.
    """
    setattr(self.conf, 'reference', 'instance1')
    with patch.object(slapos.slap.OpenOrder, 'getInformation', side_effect=raiseNotFoundError):
      slapos.cli.info.do_info(self.logger, self.conf, self.local)

    self.logger.warning.assert_called_once_with('Instance %s does not exist.', self.conf.reference)

class TestCliComputerList(CliMixin):
  def test_computer_list(self):
    """
    Test "slapos computer list" command output.
    """
    return_value = {
      'computer1': slapos.slap.hateoas.TempDocument(title='computer1', _reference='COMP-1'),
      'computer2': slapos.slap.hateoas.TempDocument(title='computer2', _reference='COMP-0'),
    }
    with patch.object(slapos.slap.slap, 'getComputerDict', return_value=return_value) as _:
      slapos.cli.computer_list.do_list(self.logger, None, self.local)

    self.logger.info.assert_any_call('%s %s', 'COMP-1', 'computer1')
    self.logger.info.assert_any_call('%s %s', 'COMP-0', 'computer2')

  def test_computer_emptyList(self):
    with patch.object(slapos.slap.slap, 'getComputerDict', return_value={}) as _:
      slapos.cli.computer_list.do_list(self.logger, None, self.local)

    self.logger.info.assert_called_once_with('No existing computer.')

@patch.object(slapos.slap.slap, 'registerComputer', return_value=slapos.slap.Computer("COMP-1"))
class TestComputerCliInfo(CliMixin):
  def test_computer_info(self, _):
    """
    Test "slapos computer info" command output.
    """
    setattr(self.conf, 'reference', 'COMP-1')
    computer = slapos.slap.Computer("COMP-1")
    computer._reference = "COMP-1"
    computer._title = "computer1"
    with patch.object(slapos.slap.Computer, 'getInformation', return_value=computer):
      slapos.cli.computer_info.do_info(self.logger, self.conf, self.local)

    self.logger.info.assert_any_call('Computer Reference: %s', computer._reference)
    self.logger.info.assert_any_call('Computer Title    : %s', computer._title)

  def test_computer_unknownReference(self, _):
    """
    Test "slapos computer info" command output in case reference
    of computer is not known.
    """
    setattr(self.conf, 'reference', 'COMP-0')
    with patch.object(slapos.slap.Computer, 'getInformation', side_effect=raiseNotFoundError):
      slapos.cli.computer_info.do_info(self.logger, self.conf, self.local)

    self.logger.warning.assert_called_once_with('Computer %s does not exist.', self.conf.reference)

@patch.object(slapos.slap.slap, 'registerToken', return_value=slapos.slap.Token())
class TestComputerCliToken(CliMixin):
  def test_computer_token(self, _):
    """
    Test "slapos computer token" command output.
    """
    token = "1234567-90"
    with patch.object(slapos.slap.Token, 'request', return_value=token):
      slapos.cli.computer_token.do_token(self.logger, self.conf, self.local)

    self.logger.info.assert_any_call('Computer token: %s', "1234567-90")

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

  default_script = """\
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
      yield slapos.cli.entry.SlapOSApp(), \
          config_file.name, \
          mock_request, \
          app_stdout


  def test_console_interactive(self):
    with self._test_console() as (app, config_file, mock_request, stdout), \
         patch.object(sys, 'stdin', StringIO(self.default_script)):
      app.run(('console', '--cfg', config_file))
      self.assertIn('parameter_value', stdout.getvalue())
      mock_request.assert_called_once_with(
          'software_release', 'instance')

  def test_console_interactive_no__file__(self):
    script = '''if 1:
      try:
        print('FAIL __file__ is set to', __file__)
      except NameError:
        print('OK __file__ is not set')

      '''
    with self._test_console() as (app, config_file, _, stdout), \
         patch.object(sys, 'stdin', StringIO(script)):
      app.run(('console', '--cfg', config_file))
      self.assertIn('OK __file__ is not set', stdout.getvalue())

  def test_console_script(self):
    with self._test_console() as (app, config_file, mock_request, stdout), \
         tempfile.NamedTemporaryFile('w') as script:
      script.write(self.default_script)
      script.flush()
      app.run(('console', '--cfg', config_file, script.name))
      self.assertIn('parameter_value', stdout.getvalue())
      mock_request.assert_called_once_with(
          'software_release', 'instance')

  def test_console_script__file__(self):
    with self._test_console() as (app, config_file, _, stdout),\
      tempfile.NamedTemporaryFile('w') as script:
      script.write('''if 1:
        if __file__ == %r:
          print('OK __file__ is set to script')
        else:
          print('FAIL __file__ is set to', __file__)
      ''' % script.name)
      script.flush()
      app.run(('console', '--cfg', config_file, script.name))
      self.assertIn('OK __file__ is set to script', stdout.getvalue())


class TestCliComplete(CliMixin):
  def test_complete_bash(self):
    with patch.object(sys, 'stdout', StringIO()) as app_stdout:
      self.assertEqual(slapos.cli.entry.SlapOSApp().run(['complete']), 0)
    self.assertIn('COMPREPLY', app_stdout.getvalue())

  def test_complete_fish(self):
    with patch.object(sys, 'stdout', StringIO()) as app_stdout:
      self.assertEqual(slapos.cli.entry.SlapOSApp().run(['complete', '--shell=fish']), 0)
    self.assertIn('__fish_seen_subcommand_from', app_stdout.getvalue())


class TestCliRequest(CliMixin):
  def test_parse_option_dict(self):
    parse_option_dict = slapos.cli.request.parse_option_dict

    self.assertEqual(parse_option_dict(['foo=bar', 'a=b']), {'foo': 'bar', 'a': 'b'})
    # malformed option = assignment
    self.assertRaises(ValueError, parse_option_dict, ['a'])
    # duplicated key
    self.assertRaises(ValueError, parse_option_dict, ['a=b', 'a=c'])
    # corner cases
    self.assertEqual(parse_option_dict(['a=a=b']), {'a': 'a=b'})
    self.assertEqual(parse_option_dict(['a=a\nb']), {'a': 'a\nb'})
    self.assertEqual(parse_option_dict([]), {})

  def test_request(self):
    self.conf.reference = 'instance reference'
    self.conf.software_url = 'software URL'
    self.conf.parameters = {'key': 'value'}
    self.conf.parameters_file = None
    self.conf.node = {'computer_guid': 'COMP-1234'}
    self.conf.type = None
    self.conf.state = None
    self.conf.slave = False

    with patch.object(
        slapos.slap.slap,
        'registerOpenOrder',
        return_value=mock.create_autospec(slapos.slap.OpenOrder)) as registerOpenOrder:
      slapos.cli.request.do_request(self.logger, self.conf, self.local)

    registerOpenOrder().request.assert_called_once_with(
        software_release='software URL',
        partition_reference='instance reference',
        partition_parameter_kw={'key': 'value'},
        software_type=None,
        filter_kw={'computer_guid': 'COMP-1234'},
        state=None,
        shared=False,
    )

    self.logger.info.assert_any_call(
        'Requesting %s as instance of %s...',
        'instance reference',
        'software URL',
    )

  def test_request_json_in_xml_published_parameters(self):
    tmpdir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, tmpdir)
    with open(os.path.join(tmpdir, 'software.cfg.json'), 'w') as f:
      json.dump(
          {
              "name": "Test Software",
              "description": "Dummy software for Test",
              "serialisation": "json-in-xml",
              "software-type": {
                  DEFAULT_SOFTWARE_TYPE: {
                      "title": "Default",
                      "description": "Default type",
                      "request": "instance-default-input-schema.json",
                      "response": "instance-default-output-schema.json",
                      "index": 0
                  },
              }
          }, f)

    self.conf.reference = 'instance reference'
    self.conf.software_url = os.path.join(tmpdir, 'software.cfg')
    self.conf.parameters = {'key': 'value'}
    self.conf.parameters_file = None
    self.conf.node = {'computer_guid': 'COMP-1234'}
    self.conf.type = None
    self.conf.state = None
    self.conf.slave = False

    cp = slapos.slap.ComputerPartition(
        'computer_%s' % self.id(),
        'partition_%s' % self.id())
    cp._requested_state = 'started'
    cp._connection_dict = {'_': json.dumps({'foo': 'bar'})}

    with patch.object(
        slapos.slap.slap,
        'registerOpenOrder',
        return_value=mock.create_autospec(slapos.slap.OpenOrder)) as registerOpenOrder:
      registerOpenOrder().request.return_value = cp
      slapos.cli.request.do_request(self.logger, self.conf, self.local)

    registerOpenOrder().request.assert_called_once()

    self.assertEqual(self.logger.info.mock_calls, [
        mock.call('Requesting %s as instance of %s...', self.conf.reference,
                  self.conf.software_url),
        mock.call('Instance requested.\nState is : %s.', 'started'),
        mock.call('Connection parameters of instance are:'),
        mock.call("{'foo': 'bar'}"),
        mock.call('You can rerun the command to get up-to-date information.'),
    ])


class TestCliRequestParametersFileJson(CliMixin):
  """Request with --parameter-file, with a .json file.
  """
  expected_partition_parameter_kw = {'foo': ['bar']}

  def _makeParameterFile(self):
    f = tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False)
    self.addCleanup(os.unlink, f.name)
    f.write(textwrap.dedent('''\
    {
      "foo": ["bar"]
    }
    '''))
    f.flush()
    return f.name

  def test_request_parameters_file(self):
    self.conf.reference = 'instance reference'
    self.conf.software_url = 'software URL'
    self.conf.parameters =  None
    f = open(self._makeParameterFile())
    self.addCleanup(f.close)
    self.conf.parameters_file = f
    self.conf.node = {'computer_guid': 'COMP-1234'}
    self.conf.type = None
    self.conf.state = None
    self.conf.slave = False

    with patch.object(
        slapos.slap.slap,
        'registerOpenOrder',
        return_value=mock.create_autospec(slapos.slap.OpenOrder)) as registerOpenOrder:
      slapos.cli.request.do_request(self.logger, self.conf, self.local)

    registerOpenOrder().request.assert_called_once_with(
        software_release='software URL',
        partition_reference='instance reference',
        partition_parameter_kw=self.expected_partition_parameter_kw,
        software_type=None,
        filter_kw={'computer_guid': 'COMP-1234'},
        state=None,
        shared=False,
    )
    self.logger.info.assert_any_call(
        'Requesting %s as instance of %s...',
        'instance reference',
        'software URL',
    )


class TestCliRequestParametersFileJsonJsonInXMLSerialisation(
    TestCliRequestParametersFileJson):
  """Request with --parameter-file, with a .json file and a software using
  json-in-xml for serialisation. In that case, the parameters are automatically
  serialised with {'_': json.dumps(params)}
  """
  expected_partition_parameter_kw = {"_": "{\"foo\": [\"bar\"]}"}

  def test_request_parameters_file(self):
    with mock.patch(
        'slapos.cli.request.SoftwareReleaseSchema.getSerialisation',
        return_value='json-in-xml'):
      super(TestCliRequestParametersFileJsonJsonInXMLSerialisation,
            self).test_request_parameters_file()


class TestCliRequestParametersFileJsonJsonInXMLSerialisationAlreadySerialised(
    TestCliRequestParametersFileJson):
  """Request with --parameter-file, with a .json file and a software using
  json-in-xml for serialisation and parameters already serialised with
  {'_': json.dumps(params)}. In that case, parameters are not serialized one
  more time.
  """
  expected_partition_parameter_kw = {"_": "{\"foo\": [\"bar\"]}"}

  def _makeParameterFile(self):
    f = tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False)
    self.addCleanup(os.unlink, f.name)
    f.write(textwrap.dedent(r'''
      {"_": "{\"foo\": [\"bar\"]}"}
    '''))
    f.flush()
    return f.name

  def test_request_parameters_file(self):
    with mock.patch(
        'slapos.cli.request.SoftwareReleaseSchema.getSerialisation',
        return_value='json-in-xml'):
      super(
          TestCliRequestParametersFileJsonJsonInXMLSerialisationAlreadySerialised,
          self).test_request_parameters_file()


class TestCliRequestParametersFileYaml(TestCliRequestParametersFileJson):
  """Request with --parameter-file, with a .yaml file. This behaves like json.
  """
  def _makeParameterFile(self):
    f = tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False)
    self.addCleanup(os.unlink, f.name)
    f.write(textwrap.dedent('''\
      foo:
      - bar
    '''))
    f.flush()
    return f.name


class TestCliRequestParametersFileXml(TestCliRequestParametersFileJson):
  """Request with --parameter-file, with a .xml file
  """
  expected_partition_parameter_kw = {'foo': 'bar'}
  def _makeParameterFile(self):
    f = tempfile.NamedTemporaryFile(suffix='.xml', mode='w', delete=False)
    f.write(textwrap.dedent('''\
      <?xml version="1.0" encoding="utf-8"?>
      <instance>
          <parameter id="foo">bar</parameter>
      </instance>
    '''))
    f.flush()
    self.addCleanup(os.unlink, f.name)
    return f.name
