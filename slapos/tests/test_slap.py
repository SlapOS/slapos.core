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

import logging
import os
import unittest
from six.moves.urllib import parse
from six import PY3
import tempfile
import logging
import warnings

from collections import OrderedDict
import httmock

import json
import mock

import slapos.slap
from slapos.util import dumps, calculate_dict_hash, dict2xml


class UndefinedYetException(Exception):
  """To catch exceptions which are not yet defined"""


logger = logging.getLogger('slapos.tests.slap')


class SlapMixin(unittest.TestCase):
  """
  Useful methods for slap tests
  """
  def setUp(self):
    self._server_url = os.environ.get('TEST_SLAP_SERVER_URL', None)
    if self._server_url is None:
      self.server_url = 'http://localhost/'
    else:
      self.server_url = self._server_url
    logger.debug('Testing against SLAP server %r', self.server_url)
    self.slap = slapos.slap.slap()
    self.partition_id = self.id()
    os.environ.pop('SLAPGRID_INSTANCE_ROOT', None)

  def tearDown(self):
    pass

  def _getTestComputerId(self):
    """
    Returns the computer id used by the test
    """
    return self.id()


class TestSlap(SlapMixin):
  """
  Test slap against slap server

  This test can be used to test a running SLAP server by setting
  TEST_SLAP_SERVER_URL environment variable to the URL of this server.
  """

  def test_slap_initialisation(self):
    """
    Asserts that slap initialisation works properly in case of
    passing correct url
    """
    slap_instance = slapos.slap.slap()
    slap_instance.initializeConnection(self.server_url)
    self.assertEqual(slap_instance._connection_helper.slapgrid_uri, self.server_url)

  def test_slap_initialisation_ipv6_and_port(self):
    slap_instance = slapos.slap.slap()
    slap_instance.initializeConnection("http://fe80:1234:1234:1234:1:1:1:1:5000/foo/")
    self.assertEqual(
        slap_instance._connection_helper.slapgrid_uri,
        "http://[fe80:1234:1234:1234:1:1:1:1]:5000/foo/"
    )

  def test_slap_initialisation_ipv6_without_port(self):
    slap_instance = slapos.slap.slap()
    slap_instance.initializeConnection("http://fe80:1234:1234:1234:1:1:1:1/foo/")
    self.assertEqual(
        slap_instance._connection_helper.slapgrid_uri,
        "http://[fe80:1234:1234:1234:1:1:1:1]/foo/"
    )

  def test_slap_initialisation_ipv6_with_bracket(self):
    slap_instance = slapos.slap.slap()
    slap_instance.initializeConnection("http://[fe80:1234:1234:1234:1:1:1:1]:5000/foo/")
    self.assertEqual(
        slap_instance._connection_helper.slapgrid_uri,
        "http://[fe80:1234:1234:1234:1:1:1:1]:5000/foo/"
    )

  def test_slap_initialisation_ipv4(self):
    slap_instance = slapos.slap.slap()
    slap_instance.initializeConnection("http://127.0.0.1:5000/foo/")
    self.assertEqual(
        slap_instance._connection_helper.slapgrid_uri,
        "http://127.0.0.1:5000/foo/"
    )

  def test_slap_initialisation_hostname(self):
    # XXX this really opens a connection !
    slap_instance = slapos.slap.slap()
    slap_instance.initializeConnection("http://example.com:80/foo/")
    self.assertEqual(
        slap_instance._connection_helper.slapgrid_uri,
        "http://example.com:80/foo/"
    )

  def test_registerComputer_with_new_guid(self):
    """
    Asserts that calling slap.registerComputer with new guid returns
    Computer object
    """
    computer_guid = self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    computer = self.slap.registerComputer(computer_guid)
    self.assertIsInstance(computer, slapos.slap.Computer)

  def test_registerComputer_with_existing_guid(self):
    """
    Asserts that calling slap.registerComputer with already used guid
    returns Computer object
    """
    computer_guid = self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    computer = self.slap.registerComputer(computer_guid)
    self.assertIsInstance(computer, slapos.slap.Computer)

    computer2 = self.slap.registerComputer(computer_guid)
    self.assertIsInstance(computer2, slapos.slap.Computer)

  # XXX: There is naming conflict in slap library.
  # SoftwareRelease is currently used as suboject of Slap transmission object
  def test_registerSoftwareRelease_with_new_uri(self):
    """
    Asserts that calling slap.registerSoftwareRelease with new guid
    returns SoftwareRelease object
    """
    software_release_uri = 'http://server/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    software_release = self.slap.registerSoftwareRelease(software_release_uri)
    self.assertIsInstance(software_release, slapos.slap.SoftwareRelease)

  def test_registerSoftwareRelease_with_existing_uri(self):
    """
    Asserts that calling slap.registerSoftwareRelease with already
    used guid returns SoftwareRelease object
    """
    software_release_uri = 'http://server/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    software_release = self.slap.registerSoftwareRelease(software_release_uri)
    self.assertIsInstance(software_release, slapos.slap.SoftwareRelease)

    software_release2 = self.slap.registerSoftwareRelease(software_release_uri)
    self.assertIsInstance(software_release2, slapos.slap.SoftwareRelease)

  def test_registerComputerPartition_new_partition_id_known_computer_guid(self):
    """
    Asserts that calling slap.registerComputerPartition on known computer
    returns ComputerPartition object
    """
    computer_guid = self._getTestComputerId()
    partition_id = self.partition_id
    self.slap.initializeConnection(self.server_url)
    self.slap.registerComputer(computer_guid)

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and qs == {
                'computer_reference': [computer_guid],
                'computer_partition_reference': [partition_id]
                }:
        partition = slapos.slap.ComputerPartition(computer_guid, partition_id)
        return {
                'status_code': 200,
                'content': dumps(partition)
                }
      else:
        return {'status_code': 400}

    self._handler = handler

    with httmock.HTTMock(handler):
      partition = self.slap.registerComputerPartition(computer_guid, partition_id)
      self.assertIsInstance(partition, slapos.slap.ComputerPartition)

  def test_registerComputerPartition_existing_partition_id_known_computer_guid(self):
    """
    Asserts that calling slap.registerComputerPartition on known computer
    returns ComputerPartition object
    """
    self.test_registerComputerPartition_new_partition_id_known_computer_guid()
    with httmock.HTTMock(self._handler):
      partition = self.slap.registerComputerPartition(self._getTestComputerId(),
                                                      self.partition_id)
      self.assertIsInstance(partition, slapos.slap.ComputerPartition)

  def test_registerComputerPartition_unknown_computer_guid(self):
    """
    Asserts that calling slap.registerComputerPartition on unknown
    computer raises NotFoundError exception
    """
    computer_guid = self._getTestComputerId()
    self.slap.initializeConnection(self.server_url)
    partition_id = self.id()

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and qs == {
              'computer_reference': [computer_guid],
              'computer_partition_reference': [partition_id]
              }:
        return {'status_code': 404}
      else:
        return {'status_code': 0}

    with httmock.HTTMock(handler):
      self.assertRaises(slapos.slap.NotFoundError,
                        self.slap.registerComputerPartition,
                        computer_guid, partition_id)


  def test_getFullComputerInformation_empty_computer_guid(self):
    """
    Asserts that calling getFullComputerInformation with empty computer_id
    raises early, before calling master.
    """
    self.slap.initializeConnection(self.server_url)

    def handler(url, req):
      # Shouldn't even be called
      self.assertFalse(True)

    with httmock.HTTMock(handler):
      self.assertRaises(slapos.slap.NotFoundError,
                        self.slap._connection_helper.getFullComputerInformation,
                        None)

  def test_registerComputerPartition_empty_computer_guid(self):
    """
    Asserts that calling registerComputerPartition with empty computer_id
    raises early, before calling master.
    """
    self.slap.initializeConnection(self.server_url)

    def handler(url, req):
      # Shouldn't even be called
      self.assertFalse(True)

    with httmock.HTTMock(handler):
      self.assertRaises(slapos.slap.NotFoundError,
                        self.slap.registerComputerPartition,
                        None, 'PARTITION_01')

  def test_registerComputerPartition_empty_computer_partition_id(self):
    """
    Asserts that calling registerComputerPartition with empty
    computer_partition_id raises early, before calling master.
    """
    self.slap.initializeConnection(self.server_url)

    def handler(url, req):
      # Shouldn't even be called
      self.assertFalse(True)

    with httmock.HTTMock(handler):
      self.assertRaises(slapos.slap.NotFoundError,
                        self.slap.registerComputerPartition,
                        self._getTestComputerId(), None)

  def test_registerComputerPartition_empty_computer_guid_empty_computer_partition_id(self):
    """
    Asserts that calling registerComputerPartition with empty
    computer_partition_id raises early, before calling master.
    """
    self.slap.initializeConnection(self.server_url)

    def handler(url, req):
      # Shouldn't even be called
      self.assertFalse(True)

    with httmock.HTTMock(handler):
      self.assertRaises(slapos.slap.NotFoundError,
                        self.slap.registerComputerPartition,
                        None, None)


  def test_getSoftwareReleaseListFromSoftwareProduct_software_product_reference(self):
    """
    Check that slap.getSoftwareReleaseListFromSoftwareProduct calls
    "/getSoftwareReleaseListFromSoftwareProduct" URL with correct parameters,
    with software_product_reference parameter being specified.
    """
    self.slap.initializeConnection(self.server_url)
    software_product_reference = 'random_reference'
    software_release_url_list = ['1', '2']

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/getSoftwareReleaseListFromSoftwareProduct' and qs == {
              'software_product_reference': [software_product_reference]
              }:
        return {
                'status_code': 200,
                'content': dumps(software_release_url_list)
                }

    with httmock.HTTMock(handler):
      self.assertEqual(
        self.slap.getSoftwareReleaseListFromSoftwareProduct(
          software_product_reference=software_product_reference),
        software_release_url_list
      )

  def test_getSoftwareReleaseListFromSoftwareProduct_software_release_url(self):
    """
    Check that slap.getSoftwareReleaseListFromSoftwareProduct calls
    "/getSoftwareReleaseListFromSoftwareProduct" URL with correct parameters,
    with software_release_url parameter being specified.
    """
    self.slap.initializeConnection(self.server_url)
    software_release_url = 'random_url'
    software_release_url_list = ['1', '2']

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/getSoftwareReleaseListFromSoftwareProduct' and qs == {
              'software_release_url': [software_release_url]
              }:
        return {
                'status_code': 200,
                'content': dumps(software_release_url_list)
                }

    with httmock.HTTMock(handler):
      self.assertEqual(
        self.slap.getSoftwareReleaseListFromSoftwareProduct(
            software_release_url=software_release_url),
        software_release_url_list
      )

  def test_getSoftwareReleaseListFromSoftwareProduct_too_many_parameters(self):
    """
    Check that slap.getSoftwareReleaseListFromSoftwareProduct raises if
    both parameters are set.
    """
    self.assertRaises(
      AttributeError,
      self.slap.getSoftwareReleaseListFromSoftwareProduct, 'foo', 'bar'
    )

  def test_getSoftwareReleaseListFromSoftwareProduct_no_parameter(self):
    """
    Check that slap.getSoftwareReleaseListFromSoftwareProduct raises if
    both parameters are either not set or None.
    """
    self.assertRaises(
      AttributeError,
      self.slap.getSoftwareReleaseListFromSoftwareProduct
    )

  def test_initializeConnection_getHateoasUrl(self):
    """
    Test that by default, slap will try to fetch Hateoas URL from XML/RPC URL.
    """
    hateoas_url = 'foo'
    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/getHateoasUrl':
        return {
                'status_code': 200,
                'content': hateoas_url
                }

    with httmock.HTTMock(handler):
      self.slap.initializeConnection('http://%s' % self.id())
    self.assertEqual(
        self.slap._hateoas_navigator.slapos_master_hateoas_uri,
        hateoas_url
    )

  def test_initializeConnection_specifiedHateoasUrl(self):
    """
    Test that if rest URL is specified, slap will NOT try to fetch
    Hateoas URL from XML/RPC URL.
    """
    hateoas_url = 'foo'
    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/getHateoasUrl':
        self.fail('slap should not have contacted master to get Hateoas URL.')

    with httmock.HTTMock(handler):
      self.slap.initializeConnection('http://%s' % self.id(), slapgrid_rest_uri=hateoas_url)
    self.assertEqual(
        self.slap._hateoas_navigator.slapos_master_hateoas_uri,
        hateoas_url
    )

  def test_initializeConnection_noHateoasUrl(self):
    """
    Test that if no rest URL is specified and master does not know about rest,
    it still work.
    """
    hateoas_url = 'foo'
    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/getHateoasUrl':
        return {
                'status_code': 404,
                }

    with httmock.HTTMock(handler):
      self.slap.initializeConnection('http://%s' % self.id())
    self.assertEqual(None, getattr(self.slap, '_hateoas_navigator', None))


class TestComputer(SlapMixin):
  """
  Tests slapos.slap.slap.Computer class functionality
  """

  def test_computer_getComputerPartitionList_no_partition(self):
    """
    Asserts that calling Computer.getComputerPartitionList without Computer
    Partitions returns empty list
    """
    computer_guid = self._getTestComputerId()
    slap = self.slap
    slap.initializeConnection(self.server_url)

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
          'computer_reference' in qs and \
          'computer_partition_reference' in qs:
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_reference'][0],
            qs['computer_partition_reference'][0])
        return {
                'status_code': 200,
                'content': dumps(slap_partition)
                }
      elif url.path == '/getFullComputerInformation' and 'computer_id' in qs:
        slap_computer = slapos.slap.Computer(qs['computer_id'][0])
        slap_computer._software_release_list = []
        slap_computer._computer_partition_list = []
        return {
                'status_code': 200,
                'content': dumps(slap_computer)
                }
      elif url.path == '/requestComputerPartition':
        return {'status_code': 408}
      else:
        return {'status_code': 404}

    with httmock.HTTMock(handler):
      computer = self.slap.registerComputer(computer_guid)
      self.assertEqual(computer.getComputerPartitionList(), [])

  def _test_computer_empty_computer_guid(self, computer_method):
    """
    Helper method checking if calling Computer method with empty id raises
    early.
    """
    self.slap.initializeConnection(self.server_url)

    def handler(url, req):
      # Shouldn't even be called
      self.assertFalse(True)

    with httmock.HTTMock(handler):
      computer = self.slap.registerComputer(None)
      self.assertRaises(slapos.slap.NotFoundError,
                        getattr(computer, computer_method))

  def test_computer_getComputerPartitionList_empty_computer_guid(self):
    """
    Asserts that calling getComputerPartitionList with empty
    computer_guid raises early, before calling master.
    """
    self._test_computer_empty_computer_guid('getComputerPartitionList')

  def test_computer_getSoftwareReleaseList_empty_computer_guid(self):
    """
    Asserts that calling getSoftwareReleaseList with empty
    computer_guid raises early, before calling master.
    """
    self._test_computer_empty_computer_guid('getSoftwareReleaseList')

  def test_computer_getComputerPartitionList_only_partition(self):
    """
    Asserts that calling Computer.getComputerPartitionList with only
    Computer Partitions returns empty list
    """
    self.computer_guid = self._getTestComputerId()
    partition_id = 'PARTITION_01'
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and qs == {
                'computer_reference': [self.computer_guid],
                'computer_partition_reference': [partition_id]
                }:
        partition = slapos.slap.ComputerPartition(self.computer_guid, partition_id)
        return {
                'status_code': 200,
                'content': dumps(partition)
                }
      elif url.path == '/getFullComputerInformation' and 'computer_id' in qs:
        slap_computer = slapos.slap.Computer(qs['computer_id'][0])
        slap_computer._computer_partition_list = []
        return {
                'status_code': 200,
                'content': dumps(slap_computer)
                }
      else:
        return {'status_code': 400}

    with httmock.HTTMock(handler):
      self.computer = self.slap.registerComputer(self.computer_guid)
      self.partition = self.slap.registerComputerPartition(self.computer_guid,
                                                           partition_id)
      self.assertEqual(self.computer.getComputerPartitionList(), [])

  @unittest.skip("Not implemented")
  def test_computer_reportUsage_non_valid_xml_raises(self):
    """
    Asserts that calling Computer.reportUsage with non DTD
    (not defined yet) XML raises (not defined yet) exception
    """

    self.computer_guid = self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    self.computer = self.slap.registerComputer(self.computer_guid)
    non_dtd_xml = """<xml>
<non-dtd-parameter name="xerxes">value<non-dtd-parameter name="xerxes">
</xml>"""
    self.assertRaises(UndefinedYetException,
                      self.computer.reportUsage,
                      non_dtd_xml)

  @unittest.skip("Not implemented")
  def test_computer_reportUsage_valid_xml_invalid_partition_raises(self):
    """
    Asserts that calling Computer.reportUsage with DTD (not defined
    yet) XML which refers to invalid partition raises (not defined yet)
    exception
    """
    self.computer_guid = self._getTestComputerId()
    partition_id = 'PARTITION_01'
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    self.computer = self.slap.registerComputer(self.computer_guid)
    self.partition = self.slap.registerComputerPartition(self.computer_guid,
                                                         partition_id)
    # XXX: As DTD is not defined currently proper XML is not known
    bad_partition_dtd_xml = """<xml>
<computer-partition id='ANOTHER_PARTITION>96.5% CPU</computer-partition>
</xml>"""
    self.assertRaises(UndefinedYetException,
                      self.computer.reportUsage,
                      bad_partition_dtd_xml)


class RequestWasCalled(Exception):
  pass


class TestComputerPartition(SlapMixin):
  """
  Tests slapos.slap.slap.ComputerPartition class functionality
  """

  def test_request_sends_request(self):
    partition_id = 'PARTITION_01'

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
          'computer_reference' in qs and \
          'computer_partition_reference' in qs:
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_reference'][0],
            qs['computer_partition_reference'][0])
        return {
                'status_code': 200,
                'content': dumps(slap_partition)
                }
      elif url.path == '/getComputerInformation' and 'computer_id' in qs:
        slap_computer = slapos.slap.Computer(qs['computer_id'][0])
        slap_computer._software_release_list = []
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_id'][0],
            partition_id)
        slap_computer._computer_partition_list = [slap_partition]
        return {
                'status_code': 200,
                'content': dumps(slap_computer)
                }
      elif url.path == '/requestComputerPartition':
        raise RequestWasCalled
      else:
        return {
                'status_code': 404
                }

    with httmock.HTTMock(handler):
      self.computer_guid = self._getTestComputerId()
      self.slap = slapos.slap.slap()
      self.slap.initializeConnection(self.server_url)
      computer_partition = self.slap.registerComputerPartition(
          self.computer_guid, partition_id)
      self.assertRaises(RequestWasCalled,
                        computer_partition.request,
                        'http://server/new/' + self._getTestComputerId(),
                        'software_type', 'myref')

  def test_request_not_raises(self):
    partition_id = self.id()

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
          'computer_reference' in qs and \
          'computer_partition_reference' in qs:
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_reference'][0],
            qs['computer_partition_reference'][0])
        return {
                'status_code': 200,
                'content': dumps(slap_partition)
                }
      elif url.path == '/getComputerInformation' and 'computer_id' in qs:
        slap_computer = slapos.slap.Computer(qs['computer_id'][0])
        slap_computer._software_release_list = []
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_id'][0],
            partition_id)
        slap_computer._computer_partition_list = [slap_partition]
        return {
                'status_code': 200,
                'content': dumps(slap_computer)
                }
      elif url.path == '/requestComputerPartition':
        return {'status_code': 408}
      else:
        return {'status_code': 404}

    self.computer_guid = self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    with httmock.HTTMock(handler):
      computer_partition = self.slap.registerComputerPartition(
          self.computer_guid, partition_id)
      requested_partition = computer_partition.request(
          'http://server/new/' + self._getTestComputerId(),
          'software_type',
          'myref')
      self.assertIsInstance(requested_partition, slapos.slap.ComputerPartition)

  def test_request_raises_later(self):
    partition_id = self.id()

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
              'computer_reference' in qs and \
              'computer_partition_reference' in qs:
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_reference'][0],
            qs['computer_partition_reference'][0])
        return {
                'status_code': 200,
                'content': dumps(slap_partition)
                }
      elif url.path == '/getComputerInformation' and 'computer_id' in qs:
        slap_computer = slapos.slap.Computer(qs['computer_id'][0])
        slap_computer._software_release_list = []
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_id'][0],
            partition_id)
        slap_computer._computer_partition_list = [slap_partition]
        return {
                'status_code': 200,
                'content': dumps(slap_computer)
                }
      elif url.path == '/requestComputerPartition':
        return {'status_code': 408}
      else:
        return {'status_code': 404}

    self.computer_guid = self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    with httmock.HTTMock(handler):
      computer_partition = self.slap.registerComputerPartition(
          self.computer_guid, partition_id)
      requested_partition = computer_partition.request(
          'http://server/new/' + self._getTestComputerId(),
          'software_type',
          'myref')
      self.assertIsInstance(requested_partition, slapos.slap.ComputerPartition)
      # as request method does not raise, accessing data raises
      self.assertRaises(slapos.slap.ResourceNotReady,
                        requested_partition.getId)

  def test_request_fullfilled_work(self):
    partition_id = 'PARTITION_01-%s' % self.id()
    requested_partition_id = 'PARTITION_02-%s' % self.id()
    computer_guid = self._getTestComputerId()

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
              'computer_reference' in qs and \
              'computer_partition_reference' in qs:
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_reference'][0],
            qs['computer_partition_reference'][0])
        return {
                'status_code': 200,
                'content': dumps(slap_partition)
                }
      elif url.path == '/getComputerInformation' and 'computer_id' in qs:
        slap_computer = slapos.slap.Computer(qs['computer_id'][0])
        slap_computer._software_release_list = []
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_id'][0],
            partition_id)
        slap_computer._computer_partition_list = [slap_partition]
        return {
                'status_code': 200,
                'content': dumps(slap_computer)
                }
      elif url.path == '/requestComputerPartition':
        from slapos.slap.slap import SoftwareInstance
        slap_partition = SoftwareInstance(
            slap_computer_id=computer_guid,
            slap_computer_partition_id=requested_partition_id)
        return {
                'status_code': 200,
                'content': dumps(slap_partition)
                }
      else:
        return {'status_code': 404}


    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)

    with httmock.HTTMock(handler):
      computer_partition = self.slap.registerComputerPartition(
          computer_guid, partition_id)
      requested_partition = computer_partition.request(
          'http://server/new/' + self._getTestComputerId(),
          'software_type',
          'myref')
      self.assertIsInstance(requested_partition, slapos.slap.ComputerPartition)
      # as request method does not raise, accessing data in case when
      # request was done works correctly
      self.assertEqual(requested_partition_id, requested_partition.getId())

  def test_request_with_slapgrid_request_transaction(self):
    from slapos.slap.slap import COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME
    partition_id = self.id()
    instance_root = tempfile.mkdtemp()
    partition_root = os.path.join(instance_root, partition_id)
    os.mkdir(partition_root)
    os.environ['SLAPGRID_INSTANCE_ROOT'] = instance_root
    transaction_file_name = COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME % partition_id
    transaction_file_path = os.path.join(partition_root, transaction_file_name)

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
           'computer_reference' in qs and \
           'computer_partition_reference' in qs:
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_reference'][0],
            qs['computer_partition_reference'][0])
        return {
                'status_code': 200,
                'content': dumps(slap_partition)
                }
      elif url.path == '/getComputerInformation' and 'computer_id' in qs:
        slap_computer = slapos.slap.Computer(qs['computer_id'][0])
        slap_computer._software_release_list = []
        slap_partition = slapos.slap.ComputerPartition(
            qs['computer_id'][0],
            partition_id)
        slap_computer._computer_partition_list = [slap_partition]
        return {
                'status_code': 200,
                'content': dumps(slap_computer)
                }
      elif url.path == '/requestComputerPartition':
        raise RequestWasCalled
      else:
        return {
                'status_code': 404
                }

    with httmock.HTTMock(handler):
      self.computer_guid = self._getTestComputerId()
      self.slap = slapos.slap.slap()
      self.slap.initializeConnection(self.server_url)
      computer_partition = self.slap.registerComputerPartition(
          self.computer_guid, partition_id)

      self.assertTrue(os.path.exists(transaction_file_path))
      with open(transaction_file_path, 'r') as f:
        content = f.read()
        self.assertEqual(content, '')
      self.assertRaises(RequestWasCalled,
                        computer_partition.request,
                        'http://server/new/' + self._getTestComputerId(),
                        'software_type', 'myref')
      self.assertTrue(os.path.exists(transaction_file_path))
      with open(transaction_file_path, 'r') as f:
        content_list = f.read().splitlines()
        self.assertEqual(content_list, ['myref'])

      # Not override
      computer_partition = self.slap.registerComputerPartition(
          self.computer_guid, partition_id)
      self.assertTrue(os.path.exists(transaction_file_path))
      with open(transaction_file_path, 'r') as f:
        content_list = f.read().splitlines()
        self.assertEqual(content_list, ['myref'])

      # Request a second instance
      self.assertRaises(RequestWasCalled,
                        computer_partition.request,
                        'http://server/new/' + self._getTestComputerId(),
                        'software_type', 'mysecondref')
      with open(transaction_file_path, 'r') as f:
        content_list = f.read().splitlines()
        self.assertEqual(sorted(content_list), ['myref', 'mysecondref'])

  def test_request_validate_request_parameter(self):

    def handler(url, req):
      if url.path.endswith('/software.cfg.json'):
        return json.dumps(
          {
              "name": "Test Software",
              "description": "Dummy software for Test",
              "serialisation": "json-in-xml",
              "software-type": {
                  'default': {
                      "title": "Default",
                      "description": "Default type",
                      "request": "instance-default-input-schema.json",
                      "response": "instance-default-output-schema.json",
                      "index": 0
                  },
              }
          })
      if url.path.endswith('/instance-default-input-schema.json'):
        return json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema",
                "description": "Simple instance parameters schema for tests",
                "required": ["foo"],
                "properties": {
                    "foo": {
                        "$ref": "./schemas-definitions.json#/foo"
                    }
                },
                "type": "object"
            })
      if url.path.endswith('/schemas-definitions.json'):
        return json.dumps({"foo": {"type": "string", "const": "bar"}})
      raise ValueError(404)

    with httmock.HTTMock(handler):
      with mock.patch.object(warnings, 'warn') as warn:
        cp = slapos.slap.ComputerPartition('computer_id', 'partition_id')
        cp._connection_helper = mock.Mock()
        cp._connection_helper.POST.side_effect = slapos.slap.ResourceNotReady
        cp.request(
            'https://example.com/software.cfg', 'default', 'reference',
            partition_parameter_kw={'foo': 'bar'})
      warn.assert_not_called()

    with httmock.HTTMock(handler):
      with mock.patch.object(warnings, 'warn') as warn:
        cp = slapos.slap.ComputerPartition('computer_id', 'partition_id')
        cp._connection_helper = mock.Mock()
        cp._connection_helper.POST.side_effect = slapos.slap.ResourceNotReady
        cp.request(
            'https://example.com/software.cfg', 'default', 'reference',
            partition_parameter_kw={'foo': 'baz'})
      if PY3:
        warn.assert_called_with(
          "Request parameters do not validate against schema definition:\n"
          "'bar' was expected\n\n"
          "Failed validating 'const' in schema['properties']['foo']:\n"
          "    {'const': 'bar', 'type': 'string'}\n\n"
          "On instance['foo']:\n    'baz'", UserWarning
        )
      else: # BBB
        warn.assert_called_with(
          "Request parameters do not validate against schema definition:\n"
          "u'bar' was expected\n\n"
          "Failed validating u'const' in schema[u'properties'][u'foo']:\n"
          "    {u'const': u'bar', u'type': u'string'}\n\n"
          "On instance[u'foo']:\n    'baz'", UserWarning
        )

  def test_request_validate_request_parameter_broken_software_release_schema(self):
    """Corner case tests for incorrect software release schema, these should
    not prevent the request (mostly for backward compatibility)
    """
    def wrong_software_cfg_schema(url, req):
      if url.path.endswith('/software.cfg.json'):
        return "wrong"
      raise ValueError(404)

    def wrong_instance_parameter_schema(url, req):
      if url.path.endswith('/software.cfg.json'):
        return json.dumps(
          {
              "name": "Test Software",
              "description": "Dummy software for Test",
              "serialisation": "json-in-xml",
              "software-type": {
                  'default': {
                      "title": "Default",
                      "description": "Default type",
                      "request": "instance-default-input-schema.json",
                      "response": "instance-default-output-schema.json",
                      "index": 0
                  },
              }
          })
      if url.path.endswith('/instance-default-input-schema.json'):
        return "wrong"
      raise ValueError(404)

    def invalid_instance_parameter_schema(url, req):
      if url.path.endswith('/software.cfg.json'):
        return json.dumps(
          {
              "name": "Test Software",
              "description": "Dummy software for Test",
              "serialisation": "json-in-xml",
              "software-type": {
                  'default': {
                      "title": "Default",
                      "description": "Default type",
                      "request": "instance-default-input-schema.json",
                      "response": "instance-default-output-schema.json",
                      "index": 0
                  },
              }
          })
      if url.path.endswith('/instance-default-input-schema.json'):
        return json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema",
                "description": "Invalid json schema",
                "required": {"wrong": True},
                "properties": {
                    ["wrong schema"]
                },
                "type": "object"
            })
      raise ValueError(404)

    def broken_reference(url, req):
      if url.path.endswith('/software.cfg.json'):
        return json.dumps(
          {
              "name": "Test Software",
              "description": "Dummy software for Test",
              "serialisation": "json-in-xml",
              "software-type": {
                  'default': {
                      "title": "Default",
                      "description": "Default type",
                      "request": "instance-default-input-schema.json",
                      "response": "instance-default-output-schema.json",
                      "index": 0
                  },
              }
          })
      if url.path.endswith('/instance-default-input-schema.json'):
        return json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema",
                "description": "Simple instance parameters schema for tests",
                "required": ["foo"],
                "properties": {
                    "foo": {
                        "$ref": "broken"
                    }
                },
                "type": "object"
            })
      raise ValueError(404)

    for handler, warning_expected in (
        (broken_reference, True),
        (wrong_software_cfg_schema, False),
        (wrong_instance_parameter_schema, True),
        (invalid_instance_parameter_schema, True),
    ):
      with httmock.HTTMock(handler):
        with mock.patch.object(warnings, 'warn') as warn:
          cp = slapos.slap.ComputerPartition('computer_id', 'partition_id')
          cp._connection_helper = mock.Mock()
          cp._connection_helper.POST.side_effect = slapos.slap.ResourceNotReady
          cp.request(
              'https://example.com/software.cfg', 'default', 'reference',
              partition_parameter_kw={'foo': 'bar'})
        if warning_expected:
          warn.assert_called()
        else:
          warn.assert_not_called()

  def _test_new_computer_partition_state(self, state):
    """
    Helper method to automate assertions of failing states on new Computer
    Partition
    """
    computer_guid = self._getTestComputerId()
    partition_id = self.id()
    slap = self.slap
    slap.initializeConnection(self.server_url)

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
              qs['computer_reference'][0] == computer_guid and \
              qs['computer_partition_reference'][0] == partition_id:
        partition = slapos.slap.ComputerPartition(
            computer_guid, partition_id)
        return {
                'status_code': 200,
                'content': dumps(partition)
                }
      else:
        return {'status_code': 404}


    with httmock.HTTMock(handler):
      computer_partition = self.slap.registerComputerPartition(
          computer_guid, partition_id)
      self.assertRaises(slapos.slap.NotFoundError,
                        getattr(computer_partition, state))

  def test_started_new_ComputerPartition_raises(self):
    """
    Asserts that calling ComputerPartition.started on new partition raises
    (not defined yet) exception
    """
    self._test_new_computer_partition_state('started')

  def test_stopped_new_ComputerPartition_raises(self):
    """
    Asserts that calling ComputerPartition.stopped on new partition raises
    (not defined yet) exception
    """
    self._test_new_computer_partition_state('stopped')

  def test_error_new_ComputerPartition_works(self):
    """
    Asserts that calling ComputerPartition.error on new partition works
    """
    computer_guid = self._getTestComputerId()
    partition_id = self.id()
    slap = self.slap
    slap.initializeConnection(self.server_url)

    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/registerComputerPartition' and \
              qs['computer_reference'][0] == computer_guid and \
              qs['computer_partition_reference'][0] == partition_id:
        partition = slapos.slap.ComputerPartition(
            computer_guid, partition_id)
        return {
                'statu_code': 200,
                'content': dumps(partition)
                }
      elif url.path == '/softwareInstanceError':
        parsed_qs_body = parse.parse_qs(req.body)
        # XXX: why do we have computer_id and not computer_reference?
        # XXX: why do we have computer_partition_id and not
        # computer_partition_reference?
        if (parsed_qs_body['computer_id'][0] == computer_guid and \
                parsed_qs_body['computer_partition_id'][0] == partition_id and \
                parsed_qs_body['error_log'][0] == 'some error'):
          return {'status_code': 200}

      return {'status_code': 404}


    with httmock.HTTMock(handler):
      computer_partition = slap.registerComputerPartition(
          computer_guid, partition_id)
      # XXX: Interface does not define return value
      computer_partition.error('some error')

  def _test_setConnectionDict(
    self, connection_dict, slave_reference=None, connection_xml=None,
    getConnectionParameterDict=None, connection_parameter_hash=None):
    getInstanceParameter = []
    if connection_parameter_hash is not None:
      getInstanceParameter = [
        {
          'slave_reference': slave_reference,
          'connection-parameter-hash': connection_parameter_hash
        }
      ]
    with \
        mock.patch.object(
          slapos.slap.ComputerPartition, '__init__', return_value=None), \
        mock.patch.object(
          slapos.slap.ComputerPartition, 'getConnectionParameterDict',
          return_value=getConnectionParameterDict or {}), \
        mock.patch.object(
          slapos.slap.ComputerPartition, 'getInstanceParameter',
          return_value=getInstanceParameter):
      partition = slapos.slap.ComputerPartition()
      partition._connection_helper = mock.Mock()
      partition._computer_id = 'COMP-0'
      partition._partition_id = 'PART-0'
      partition._connection_helper.POST = mock.Mock()
      partition.setConnectionDict(
        connection_dict, slave_reference=slave_reference)
      if connection_xml:
        connection_xml = connection_xml.encode() if PY3 else connection_xml
        partition._connection_helper.POST.assert_called_with(
          'setComputerPartitionConnectionXml',
          data={
            'slave_reference': slave_reference,
            'connection_xml': connection_xml,
            'computer_partition_id': 'PART-0',
            'computer_id': 'COMP-0'})
      else:
        partition._connection_helper.POST.assert_not_called()

  def test_setConnectionDict(self):
    self._test_setConnectionDict(
      {'a': 'b'},
      connection_xml='<marshal><dictionary id="i2"><string>a</string>'
                     '<string>b</string></dictionary></marshal>')

  def test_setConnectionDict_optimised(self):
    self._test_setConnectionDict(
      {'a': 'b'},
      getConnectionParameterDict={'a': 'b'},
      connection_xml=False)

  def test_setConnectionDict_optimised_tricky(self):
    self._test_setConnectionDict(
      {u'a': u'b', 'b': '', 'c': None},
      getConnectionParameterDict={'a': 'b', 'b': None, 'c': 'None'},
      connection_xml=False)

  def test_setConnectionDict_update(self):
    self._test_setConnectionDict(
      {'a': 'b'},
      getConnectionParameterDict={'b': 'b'},
      connection_xml='<marshal><dictionary id="i2"><string>a</string>'
                     '<string>b</string></dictionary></marshal>')

  def test_setConnectionDict_slave(self):
    self._test_setConnectionDict(
      {'a': 'b'},
      slave_reference='SLAVE-0',
      connection_xml='<marshal><dictionary id="i2"><string>a</string>'
                     '<string>b</string></dictionary></marshal>')

  def test_setConnectionDict_slave_expired_hash(self):
    self._test_setConnectionDict(
      {'a': 'b'},
      slave_reference='SLAVE-0',
      connection_parameter_hash='mess',
      connection_xml='<marshal><dictionary id="i2"><string>a</string>'
                     '<string>b</string></dictionary></marshal>')

  def test_setConnectionDict_slave_hash(self):
    self._test_setConnectionDict(
      {'a': 'b'},
      slave_reference='SLAVE-0',
      connection_parameter_hash=calculate_dict_hash({'a': 'b'}),
      connection_xml=False)

  def test_setConnectionDict_slave_hash_tricky(self):
    self._test_setConnectionDict(
      {u'a': u'b', 'b': '', 'c': None},
      slave_reference='SLAVE-0',
      connection_parameter_hash=calculate_dict_hash({
        'a': 'b', 'b': None, 'c': 'None'}),
      connection_xml=False)


class TestSoftwareRelease(SlapMixin):
  """
  Tests slap.SoftwareRelease class functionality
  """

  def _test_new_software_release_state(self, state):
    """
    Helper method to automate assertions of failing states on new Software
    Release
    """
    self.software_release_uri = 'http://server/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    software_release = self.slap.registerSoftwareRelease(
        self.software_release_uri)
    method = getattr(software_release, state)
    self.assertRaises(NameError, method)

  def test_available_new_SoftwareRelease_raises(self):
    """
    Asserts that calling SoftwareRelease.available on new software release
    raises NameError exception
    """
    self._test_new_software_release_state('available')

  def test_building_new_SoftwareRelease_raises(self):
    """
    Asserts that calling SoftwareRelease.building on new software release
    raises NameError exception
    """
    self._test_new_software_release_state('building')

  def test_error_new_SoftwareRelease_works(self):
    """
    Asserts that calling SoftwareRelease.error on software release works
    """
    computer_guid = self._getTestComputerId()
    software_release_uri = 'http://server/' + self._getTestComputerId()
    slap = self.slap
    slap.initializeConnection(self.server_url)

    def handler(url, req):
      qs = parse.parse_qs(req.body)
      if url.path == '/softwareReleaseError' and \
              qs['computer_id'][0] == computer_guid and \
              qs['url'][0] == software_release_uri and \
              qs['error_log'][0] == 'some error':
        return {
                'status_code': 200
                }
      return {'status_code': 404}


    with httmock.HTTMock(handler):
      software_release = self.slap.registerSoftwareRelease(software_release_uri)
      software_release._computer_guid = computer_guid
      software_release.error('some error')


class TestOpenOrder(SlapMixin):
  def test_request_sends_request(self):
    software_release_uri = 'http://server/new/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    # XXX: Interface lack registerOpenOrder method declaration
    open_order = self.slap.registerOpenOrder()

    def handler(url, req):
      if url.path == '/requestComputerPartition':
        raise RequestWasCalled

    with httmock.HTTMock(handler):
      self.assertRaises(RequestWasCalled,
                        open_order.request,
                        software_release_uri, 'myrefe')

  @unittest.skip('unclear what should be returned')
  def test_request_not_raises(self):
    software_release_uri = 'http://server/new/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    # XXX: Interface lack registerOpenOrder method declaration

    def handler(url, req):
      if url.path == '/requestComputerPartition':
        pass
        # XXX what to do here?

    with httmock.HTTMock(handler):
      open_order = self.slap.registerOpenOrder()
      computer_partition = open_order.request(software_release_uri, 'myrefe')
      self.assertIsInstance(computer_partition, slapos.slap.ComputerPartition)

  def test_request_raises_later(self):
    software_release_uri = 'http://server/new/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    # XXX: Interface lack registerOpenOrder method declaration
    open_order = self.slap.registerOpenOrder()

    def handler(url, req):
      return {'status_code': 408}

    with httmock.HTTMock(handler):
      computer_partition = open_order.request(software_release_uri, 'myrefe')
      self.assertIsInstance(computer_partition, slapos.slap.ComputerPartition)

      self.assertRaises(slapos.slap.ResourceNotReady,
                        computer_partition.getId)

  def test_request_fullfilled_work(self):
    software_release_uri = 'http://server/new/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    # XXX: Interface lack registerOpenOrder method declaration
    open_order = self.slap.registerOpenOrder()
    computer_guid = self._getTestComputerId()
    requested_partition_id = self.id()

    def handler(url, req):
      from slapos.slap.slap import SoftwareInstance
      slap_partition = SoftwareInstance(
          slap_computer_id=computer_guid,
          slap_computer_partition_id=requested_partition_id)
      return {
              'status_code': 200,
              'content': dumps(slap_partition)
              }

    with httmock.HTTMock(handler):
      computer_partition = open_order.request(software_release_uri, 'myrefe')
      self.assertIsInstance(computer_partition, slapos.slap.ComputerPartition)
      self.assertEqual(requested_partition_id, computer_partition.getId())


  def test_request_getConnectionParameter(self):
    """ Backward compatibility API for slapproxy older them 1.0.1 """
    software_release_uri = 'http://server/new/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    # XXX: Interface lack registerOpenOrder method declaration
    open_order = self.slap.registerOpenOrder()
    computer_guid = self._getTestComputerId()
    requested_partition_id = self.id()

    def handler(url, req):
      from slapos.slap.slap import SoftwareInstance
      slap_partition = SoftwareInstance(
          _connection_dict = {"url": 'URL_CONNECTION_PARAMETER'},
          slap_computer_id=computer_guid,
          slap_computer_partition_id=requested_partition_id)
      return {
              'status_code': 200,
              'content': dumps(slap_partition)
              }


    with httmock.HTTMock(handler):
      computer_partition = open_order.request(software_release_uri, 'myrefe')
      self.assertIsInstance(computer_partition, slapos.slap.ComputerPartition)
      self.assertEqual(requested_partition_id, computer_partition.getId())
      self.assertEqual("URL_CONNECTION_PARAMETER",
                       computer_partition.getConnectionParameter('url'))


  def test_request_connection_dict_backward_compatibility(self):
    """ Backward compatibility API for slapproxy older them 1.0.1 """
    software_release_uri = 'http://server/new/' + self._getTestComputerId()
    self.slap = slapos.slap.slap()
    self.slap.initializeConnection(self.server_url)
    # XXX: Interface lack registerOpenOrder method declaration
    open_order = self.slap.registerOpenOrder()
    computer_guid = self._getTestComputerId()
    requested_partition_id = self.id()

    def handler(url, req):
      from slapos.slap.slap import SoftwareInstance
      slap_partition = SoftwareInstance(
          connection_xml="""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="url">URL_CONNECTION_PARAMETER</parameter>
</instance>""",
          slap_computer_id=computer_guid,
          slap_computer_partition_id=requested_partition_id)
      return {
              'status_code': 200,
              'content': dumps(slap_partition)
              }

    with httmock.HTTMock(handler):
      computer_partition = open_order.request(software_release_uri, 'myrefe')
      self.assertIsInstance(computer_partition, slapos.slap.ComputerPartition)
      self.assertEqual(requested_partition_id, computer_partition.getId())
      self.assertEqual("URL_CONNECTION_PARAMETER",
                       computer_partition.getConnectionParameter('url'))

  def test_getInformation(self):
    self.slap = slapos.slap.slap()
    parameter_dict = {
      "param1": "value1",
      "param2_dict": {
        "param2_param1": "",
        "param2_param2_dict": {},
        "param2_param3_dict": {"param": "value"}
        }
      }

    link_keys = {
        "type": {
          "href": "urn:jio:get:portal_types/Instance Tree",
          "name": "Instance Tree"
          },
        }
    instance_tree_info_dict = {
        "connection_parameter_list": {
          "title": "my_connection_parameter_dict",
          "default": [
            {
              "connection_key": "key1",
              "connection_value": "value1"
              },
            {
              "connection_key": "key2",
              "connection_value": "value2"
              },
            ],
          "key": "field_my_connection_parameter_list",
          "type": "StringField"
          },
        "title": {
            "title": "Title",
            "default": "myrefe",
            "key": "field_my_title",
            "type": "StringField"
            },
        "text_content": {
            "title": "Parameter XML",
            "default": dict2xml({'_': json.dumps(parameter_dict)}),
            "key": "field_my_text_content",
            "type": "TextAreaField"
            },
        "slap_state": {
            "title": "Slap State",
            "default": "stop_requested",
            "key": "field_my_slap_state",
            "type": "StringField"
            },
        "source_title": {
            "title": "Current Organisation",
            "default": "",
            "key": "field_my_source_title",
            "type": "StringField"
            },
        "url_string": {
            "title": "Url String",
            "default": "https://lab.nexedi.com/nexedi/slapos/raw/1.0.115/software/kvm/software.cfg",
            "key": "field_my_url_string",
            "type": "StringField"
            }
        }
    view_dict = {}
    for k in instance_tree_info_dict:
      view_dict["my_%s" % k] = instance_tree_info_dict[k]
    view_dict["_embedded"] = {
        "form_definition": {
          "update_action_title": "",
          "_debug": "traverse",
          "pt": "form_view_editable",
          "title": "InstanceTree_viewAsHateoas",
          "_links": {
            "portal": {
                "href": "urn:jio:get:erp5",
                "name": "ERP5"
                },
            },
          "action": "InstanceTree_editWebMode",
          "update_action": ""
        }
      }
    view_dict["form_id"] = {
        "title": "form_id",
        "default": "InstanceTree_viewAsHateoas",
        "key": "form_id",
        "type": "StringField"
        }
    view_dict["_links"] = {
        "traversed_document": {
          "href": "urn:jio:get:instance_tree_module/my_refe_id",
          "name": "instance_tree_module/my_refe_id",
          "title": "myrefe"
          },
        "self": {
          "href": "https://localhost/instance_tree_module/my_refe_id/InstanceTree_viewAsHateoas"
          },
        "form_definition": {
          "href": "urn:jio:get:portal_skins/slapos_hal_json_style/InstanceTree_viewAsHateoas",
          "name": "InstanceTree_viewAsHateoas"
          }
        }
    hateoas_url = "/custom_hateoas_url"
    def handler(url, req):
      qs = parse.parse_qs(url.query)
      if url.path == '/getHateoasUrl':
        return {
            'status_code': 200,
            'content': "http://localhost" + hateoas_url
            }
      elif url.path == hateoas_url:
        return {
            'status_code': 200,
            'content': {
              "default_view": "view",
              "_links": {
                "traverse": {
                  "href": "https://localhost/SLAPTEST_getHateoas?mode=traverse{&relative_url,view}",
                  "name": "Traverse",
                  "templated": True
                  },
                "raw_search": {
                  "href": "https://localhost/SLAPTEST_getHateoas?mode=search{&query,select_list*,limit*,group_by*,sort_on*,local_roles*,selection_domain*}",
                  "name": "Raw Search",
                  "templated": True
                  },
                },
              "_debug": "root",
              "title": "Hateoas"
              }
            }
      elif url.path == '/SLAPTEST_getHateoas':
        if ("mode=search" in url.query):
          return {
              'status_code': 200,
              'content': {
                "_sort_on": "",
                "_embedded": {
                  "contents": [
                    {
                      "_links": {
                        "self": {
                          "href": "urn:jio:get:instance_tree_module/my_refe_id"
                          }
                        },
                      "relative_url": "instance_tree_module/my_refe_id",
                      "title": "myrefe"
                      }
                    ]
                  },
                "_debug": "search",
                "_limit": "200",
                "_local_roles": "",
                "_query": "portal_type:\"Instance Tree\" AND validation_state:validated AND title:=\"myrefe\"",
                "_select_list": [
                  "title",
                  "relative_url"
                  ],
                "_links": {
                  "self": {
                    "href": "https://localhost/SLAPTEST_getHateoas"
                    },
                  "portal": {
                    "href": "urn:jio:get:erp5",
                    "name": "ERP5"
                    },
                  "site_root": {
                    "href": "urn:jio:get:web_site_module/hateoas",
                    "name": "Hateoas"
                    }
                  },
                "_group_by": "",
                "_selection_domain": ""
                }
              }

        elif ("mode=traverse" in url.query):
          return {
              'status_code': 200,
              'content': {
                "_embedded": {
                  "_view": view_dict
                  },
                "_links": link_keys,
                "_debug": "traverse",
                "title": "myrefe"
                }
              }

    with httmock.HTTMock(handler):
      self.slap.initializeConnection('http://%s' % self.id())
      open_order = self.slap.registerOpenOrder()
      computer_guid = self._getTestComputerId()
      requested_partition_id = self.id()
      software_instance = open_order.getInformation('myrefe')
      self.assertIsInstance(software_instance, slapos.slap.SoftwareInstance)
      for key in instance_tree_info_dict:
        if key not in link_keys:
          self.assertEqual(getattr(software_instance, '_' + key), instance_tree_info_dict[key]["default"])
      self.assertEqual(software_instance._parameter_dict, {'_': parameter_dict})
      self.assertEqual(software_instance._requested_state, instance_tree_info_dict['slap_state']["default"])
      self.assertEqual(software_instance._connection_dict, instance_tree_info_dict['connection_parameter_list']["default"])
      self.assertEqual(software_instance._software_release_url, instance_tree_info_dict['url_string']["default"])


class TestSoftwareProductCollection(SlapMixin):
  def setUp(self):
    SlapMixin.setUp(self)
    self.real_getSoftwareReleaseListFromSoftwareProduct =\
        slapos.slap.slap.getSoftwareReleaseListFromSoftwareProduct

    def fake_getSoftwareReleaseListFromSoftwareProduct(inside_self, software_product_reference):
      return self.getSoftwareReleaseListFromSoftwareProduct_response
    slapos.slap.slap.getSoftwareReleaseListFromSoftwareProduct =\
        fake_getSoftwareReleaseListFromSoftwareProduct

    self.product_collection = slapos.slap.SoftwareProductCollection(
        logging.getLogger(), slapos.slap.slap())

  def tearDown(self):
    slapos.slap.slap.getSoftwareReleaseListFromSoftwareProduct =\
        self.real_getSoftwareReleaseListFromSoftwareProduct

  def test_get_product(self):
    """
    Test that the get method (aliased to __getattr__) returns the first element
    of the list given by getSoftwareReleaseListFromSoftwareProduct (i.e the
    best one).
    """
    self.getSoftwareReleaseListFromSoftwareProduct_response = ['0', '1', '2']
    self.assertEqual(
      self.product_collection.get('random_reference'),
      self.getSoftwareReleaseListFromSoftwareProduct_response[0]
    )

  def test_get_product_empty_product(self):
    """
    Test that the get method (aliased to __getattr__) raises if no
    Software Release is related to the Software Product, or if the
    Software Product does not exist.
    """
    self.getSoftwareReleaseListFromSoftwareProduct_response = []
    self.assertRaises(
      AttributeError,
      self.product_collection.get, 'random_reference',
    )

  def test_get_product_getattr(self):
    """
    Test that __getattr__ method is bound to get() method.
    """
    self.getSoftwareReleaseListFromSoftwareProduct_response = ['0']
    self.product_collection.foo
    self.assertEqual(
      self.product_collection.__getattr__,
      self.product_collection.get
    )
    self.assertEqual(self.product_collection.foo, '0')
