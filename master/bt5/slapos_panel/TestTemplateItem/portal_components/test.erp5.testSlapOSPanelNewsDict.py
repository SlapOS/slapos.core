# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2026 Nexedi SA and Contributors.
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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, \
  TemporaryAlarmScript
from six.moves.urllib.parse import unquote
from six.moves.urllib.parse import urlencode
import json


def fakeStopRequestedSlapState():
  return "stop_requested"

def fakeDestroyRequestedSlapState():
  return "destroy_requested"

class TestPanelNewsDictMixin(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    #self.project = self.addProject()

  def assertNewsDictConsistency(self, news_dict, document):
    """ Assert if news dict contains portal type and reference
      common values expected from getAccessStatus call)"""

    self.assertEqual(news_dict['portal_type'], document.getPortalType())
    self.assertEqual(news_dict['reference'], document.getReference())

class TestBase_getNewsDictFromComputeNodeList(TestPanelNewsDictMixin):

  def test_Base_getNewsDictFromComputeNodeList(self):
    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title='TESTCOMPUTERNODE-%s' % self.generateNewId())
    compute_node.validate()
    self.tic()

    news_dict = compute_node.Base_getNewsDictFromComputeNodeList(
      compute_node_list=[compute_node])
    self.assertNewsDictConsistency(news_dict, compute_node)
    self.assertIn(compute_node.getReference(), news_dict['compute_node'])

  def test_Base_getNewsDictFromComputeNodeList_multiple_nodes(self):
    compute_node1 = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title='TESTCOMPUTERNODE-%s' % self.generateNewId())
    compute_node1.setReference('REFNODE1-%s' % self.generateNewId())
    compute_node1.validate()
    compute_node2 = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title='TESTCOMPUTERNODE-%s' % self.generateNewId())
    compute_node2.setReference('REFNODE2-%s' % self.generateNewId())
    compute_node2.validate()
    self.tic()

    news_dict = compute_node1.Base_getNewsDictFromComputeNodeList(
      compute_node_list=[compute_node1, compute_node2])
    self.assertEqual(len(news_dict['compute_node']), 2)
    self.assertIn(compute_node1.getReference(), news_dict['compute_node'])
    self.assertIn(compute_node2.getReference(), news_dict['compute_node'])

class TestDocument_getNewsDict(TestPanelNewsDictMixin):

  def test_Document_getNewsDict_node(self, portal_type='Compute Node'):
    node = self.portal.compute_node_module.newContent(
      portal_type=portal_type,
      title='TESTNODE-%s' % self.generateNewId())
    node.validate()
    self.tic()

    news_dict = node.Document_getNewsDict()
    self.assertNewsDictConsistency(news_dict, node)

  def test_Document_getNewsDict_remote_node(self):
    self.test_Document_getNewsDict_node(portal_type='Remote Node')

  def test_Document_getNewsDict_instance_node(self):
    self.test_Document_getNewsDict_node(portal_type='Instance Node')

  def test_Document_getNewsDict_instance_tree(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()
    self.tic()

    news_dict = instance_tree.Document_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance_tree)

  def test_Document_getNewsDict_computer_network(self):
    network = self.portal.computer_network_module.newContent(
      portal_type='Computer Network')
    network.validate()
    self.tic()

    news_dict = network.Document_getNewsDict()
    self.assertNewsDictConsistency(news_dict, network)

  def test_Document_getNewsDict_unsupported(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    self.assertRaises(ValueError, person.Document_getNewsDict)

class TestSoftwareInstallation_getNewsDict(TestPanelNewsDictMixin):

  def test_SoftwareInstallation_getNewsDict(self):
    software_installation = self.portal.software_installation_module.newContent(
      portal_type='Software Installation')
    software_installation.validate()
    self.tic()

    news_dict = software_installation.SoftwareInstallation_getNewsDict()
    self.assertNewsDictConsistency(news_dict, software_installation)

class TestInstanceTree_getNewsDict(TestPanelNewsDictMixin):

  def test_InstanceTree_getNewsDict(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()
    self.tic()

    news_dict = instance_tree.InstanceTree_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance_tree)
    self.assertEqual(news_dict['title'], instance_tree.getTitle())
    self.assertEqual(news_dict['instance'], [])

  def test_InstanceTree_getNewsDict_slave(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.setRootSlave(1)
    instance_tree.validate()
    self.tic()

    news_dict = instance_tree.InstanceTree_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance_tree)
    self.assertEqual(news_dict['title'], instance_tree.getTitle())
    self.assertEqual(news_dict['instance'], [])
    self.assertEqual(news_dict['is_slave'], 1)

  def test_InstanceTree_getNewsDict_stopped(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()
    self.tic()

    instance_tree.getSlapState = fakeStopRequestedSlapState
    news_dict = instance_tree.InstanceTree_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance_tree)
    self.assertEqual(news_dict['title'], instance_tree.getTitle())
    self.assertEqual(news_dict['instance'], [])
    self.assertEqual(news_dict['is_stopped'], 1)

  def test_InstanceTree_getNewsDict_destroyed(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()
    self.tic()

    instance_tree.getSlapState = fakeDestroyRequestedSlapState
    news_dict = instance_tree.InstanceTree_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance_tree)
    self.assertEqual(news_dict['title'], instance_tree.getTitle())
    self.assertEqual(news_dict['instance'], [])
    self.assertEqual(news_dict['is_destroyed'], 1)

  def test_InstanceTree_getNewsDict_with_instance(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    news_dict = instance_tree.InstanceTree_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance_tree)
    self.assertEqual(news_dict['title'], instance_tree.getTitle())
    self.assertEqual(len(news_dict['instance']), 1)

    self.assertEqual(
      news_dict['instance'][0]['portal_type'], 'Software Instance')
    self.assertEqual(
      news_dict['instance'][0]['reference'], instance.getReference())

  def test_InstanceTree_getNewsDict_with_slave_instance(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Slave Instance',
      title='TESTSLAVE-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    news_dict = instance_tree.InstanceTree_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance_tree)
    self.assertEqual(news_dict['title'], instance_tree.getTitle())
    self.assertEqual(news_dict['instance'], [])

  def test_InstanceTree_getNewsDict_with_two_instance(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance1 = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance1.edit(specialise_value=instance_tree)
    instance1.validate()

    instance2 = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance2.edit(specialise_value=instance_tree)
    instance2.validate()
    self.tic()

    news_dict = instance_tree.InstanceTree_getNewsDict()
    self.assertEqual(len(news_dict['instance']), 2)

class TestComputerNetwork_getNewsDict(TestPanelNewsDictMixin):

  def test_ComputerNetwork_getNewsDict(self):
    network = self.portal.computer_network_module.newContent(
      portal_type='Computer Network')
    network.validate()

    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title='TESTCOMPUTERNODE-%s' % self.generateNewId())
    compute_node.validate()
    compute_node.setSubordinationValue(network)
    self.tic()

    news_dict = network.ComputerNetwork_getNewsDict()
    self.assertNewsDictConsistency(news_dict, network)
    self.assertEqual(len(news_dict['compute_node']), 1)
    self.assertNewsDictConsistency(
        news_dict['compute_node'][compute_node.getReference()], compute_node)

  def test_ComputerNetwork_getNewsDict_no_data(self):
    network = self.portal.computer_network_module.newContent(
      portal_type='Computer Network')
    network.validate()
    self.tic()

    news_dict = network.ComputerNetwork_getNewsDict()
    self.assertEqual(news_dict['compute_node'], {})
    self.assertNewsDictConsistency(news_dict, network)

class TestSoftwareInstance_getNewsDict(TestPanelNewsDictMixin):

  def test_SoftwareInstance_getNewsDict(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    news_dict = instance.SoftwareInstance_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance)
    self.assertIn('monitor_url', news_dict)

  def test_SoftwareInstance_getNewsDict_no_data(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    news_dict = instance.SoftwareInstance_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance)
    self.assertIn('monitor_url', news_dict)

  def test_SoftwareInstance_getNewsDict_slave(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Slave Instance',
      title='TESTSLAVE-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    news_dict = instance.SoftwareInstance_getNewsDict()
    self.assertEqual(news_dict['is_slave'], 1)
    self.assertNewsDictConsistency(news_dict, instance)
    self.assertIn('monitor_url', news_dict)

  def test_SoftwareInstance_getNewsDict_stopped(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    instance.getSlapState = fakeStopRequestedSlapState
    news_dict = instance.SoftwareInstance_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance)
    self.assertEqual(news_dict['is_stopped'], 1)
    self.assertIn('monitor_url', news_dict)

  def test_SoftwareInstance_getNewsDict_destroyed(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    instance.getSlapState = fakeDestroyRequestedSlapState
    news_dict = instance.SoftwareInstance_getNewsDict()
    self.assertNewsDictConsistency(news_dict, instance)
    self.assertEqual(news_dict['is_destroyed'], 1)
    self.assertIn('monitor_url', news_dict)

class TestBase_getStatusMonitorUrl(TestPanelNewsDictMixin):

  def test_Base_getStatusMonitorUrl_instance_tree(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()
    self.tic()

    with TemporaryAlarmScript(
        self.portal,
        'InstanceTree_getMonitorParameterDict',
        "{'username': 'testuser', 'password': 'testpass', 'url': 'https://monitor.example.com'}",
        attribute=False):
      url = unquote(instance_tree.Base_getStatusMonitorUrl())
      self.assertIn('ojsm_landing', url)
      self.assertIn('testuser', url)
      self.assertIn('testpass', url)
      self.assertIn('https://monitor.example.com', url)
      self.assertIn('Instance Tree', url)

  def test_Base_getStatusMonitorUrl_software_instance(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title='TESTSOFTINST-%s' % self.generateNewId())
    instance.edit(specialise_value=instance_tree)
    instance.validate()
    self.tic()

    with TemporaryAlarmScript(
        self.portal,
        'InstanceTree_getMonitorParameterDict',
        "{'username': 'testuser', 'password': 'testpass', 'url': 'https://monitor.example.com'}",
        attribute=False):
      url = unquote(instance.Base_getStatusMonitorUrl())
      self.assertIn('ojsm_landing', url)
      self.assertIn('testuser', url)
      self.assertIn('Software Instance', url)

  def test_Base_getStatusMonitorUrl_no_params(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    instance_tree.validate()
    self.tic()

    with TemporaryAlarmScript(
        self.portal,
        'InstanceTree_getMonitorParameterDict',
        "{}",
        attribute=False):
      url = instance_tree.Base_getStatusMonitorUrl()
      self.assertEqual(url, '')

class TestInstanceTree_getMonitorParameterDict(TestPanelNewsDictMixin):

  def _make_frag_url(self, url, username, password):
    return "#" + urlencode({"url": url, "username": username, "password": password})

  def _make_conn_xml(self, params):
    xml = '<?xml version="1.0" encoding="utf-8"?><instance>'
    for k, v in params.items():
      v = v.replace('&', '&amp;')
      xml += '<parameter id="' + k + '">' + v + '</parameter>'
    xml += '</instance>'
    return xml

  def _createInstanceTree(self, title=None, reference=None):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree')
    if title:
      instance_tree.setTitle(title)
    if reference:
      instance_tree.setReference(reference)
    instance_tree.validate()
    return instance_tree

  def _createRootInstance(self, instance_tree, connection_xml=None):
    title = instance_tree.getTitle()
    if not title:
      title = 'TESTINSTANCE-%s' % self.generateNewId()
      instance_tree.setTitle(title)
    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title=title)
    instance.edit(
     specialise_value=instance_tree,
     connection_xml=connection_xml)
    instance.validate()
    instance_tree.setSuccessorValue(instance)
    return instance

  def test_InstanceTree_getMonitorParameterDict_fragment_url(self):
    instance_tree = self._createInstanceTree(title='TESTFRAG-%s' % self.generateNewId())
    frag = self._make_frag_url('http://monitor.example.com/public/feeds', 'testuser', 'testpass')
    conn_xml = self._make_conn_xml({'monitor-setup-url': frag})
    self._createRootInstance(instance_tree, connection_xml=conn_xml)
    self.tic()

    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(result['username'], 'testuser')
    self.assertEqual(result['password'], 'testpass')
    self.assertEqual(unquote(result['url']), 'http://monitor.example.com/public/feeds')

  def test_InstanceTree_getMonitorParameterDict_direct_params(self):
    instance_tree = self._createInstanceTree(title='TESTDIRECT-%s' % self.generateNewId())
    conn_xml = self._make_conn_xml({
      'monitor-setup-url': 'http://dummy.example.com',
      'monitor-user': 'directuser',
      'monitor-password': 'directpass',
      'monitor-base-url': 'http://monitor.example.com',
    })
    self._createRootInstance(instance_tree, connection_xml=conn_xml)
    self.tic()

    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(result['username'], 'directuser')
    self.assertEqual(result['password'], 'directpass')
    self.assertEqual(result['url'], 'http://monitor.example.com/public/feeds')

  def test_InstanceTree_getMonitorParameterDict_destroyed(self):
    instance_tree = self._createInstanceTree(title='TESTDESTROYED-%s' % self.generateNewId())
    self.tic()
    instance_tree.getSlapState = fakeDestroyRequestedSlapState
    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(result, {})

  def test_InstanceTree_getMonitorParameterDict_no_root_instance(self):
    instance_tree = self._createInstanceTree(title='TESTNOROOT-%s' % self.generateNewId())
    self.tic()
    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(result, {})

  def test_InstanceTree_getMonitorParameterDict_root_instance_destroyed(self):
    instance_tree = self._createInstanceTree(title='TESTROOTDEST-%s' % self.generateNewId())
    self._createRootInstance(instance_tree)
    self.tic()
    instance_tree.getSlapState = fakeDestroyRequestedSlapState
    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(result, {})

  def test_InstanceTree_getMonitorParameterDict_no_monitor_setup_url(self):
    instance_tree = self._createInstanceTree(title='TESTNOURL-%s' % self.generateNewId())
    conn_xml = self._make_conn_xml({'status': 'good'})
    self._createRootInstance(instance_tree, connection_xml=conn_xml)
    self.tic()

    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(result, {})

  def test_InstanceTree_getMonitorParameterDict_json_format(self):
    instance_tree = self._createInstanceTree(title='TESTJSON-%s' % self.generateNewId())
    inner = {'monitor-setup-url': 'http://example.com#url=http://monitor.test.com&username=jsonuser&password=jsonpass'}
    conn_xml = self._make_conn_xml({'_': json.dumps(inner)})
    self._createRootInstance(instance_tree, connection_xml=conn_xml)
    self.tic()

    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(result['username'], 'jsonuser')
    self.assertEqual(result['password'], 'jsonpass')
    self.assertEqual(unquote(result['url']), 'http://monitor.test.com')

  def test_InstanceTree_getMonitorParameterDict_special_chars(self):
    instance_tree = self._createInstanceTree(title='TESTSPECIAL-%s' % self.generateNewId())
    frag = self._make_frag_url('http://monitor.example.com/feeds', 'user&name', 'pass&word')
    conn_xml = self._make_conn_xml({'monitor-setup-url': frag})
    self._createRootInstance(instance_tree, connection_xml=conn_xml)
    self.tic()

    result = instance_tree.InstanceTree_getMonitorParameterDict()
    self.assertEqual(unquote(result['username']), 'user&name')
    self.assertEqual(unquote(result['password']), 'pass&word')
    self.assertEqual(unquote(result['url']), 'http://monitor.example.com/feeds')
