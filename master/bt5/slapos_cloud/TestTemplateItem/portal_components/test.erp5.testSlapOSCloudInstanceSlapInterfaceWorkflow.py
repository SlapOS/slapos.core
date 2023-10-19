# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
import transaction
from unittest import expectedFailure
from time import sleep
from zExceptions import Unauthorized
from cryptography import x509
from cryptography.x509.oid import NameOID

class TestSlapOSCoreInstanceSlapInterfaceWorkflow(SlapOSTestCaseMixin):
  """Tests instance.requestInstance"""
  
  launch_caucase = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    new_id = self.generateNewId()

    self.request_kw = dict(
        software_release=self.generateNewSoftwareReleaseUrl(),
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        shared=False,
        state="started"
    )

    # prepare part of tree
    instance_tree = portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    self.software_instance = portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)

    instance_tree.edit(
        title=self.request_kw['software_title'],
        reference="TESTHS-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        root_slave=self.request_kw['shared'],
        successor=self.software_instance.getRelativeUrl()
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(instance_tree, 'start_requested')

    self.software_instance.edit(
        title=self.request_kw['software_title'],
        reference="TESTSI-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=instance_tree.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(self.software_instance, 'start_requested')
    self.software_instance.validate()
    self.tic()

    # Login as new Software Instance
    self.login(self.software_instance.getUserId())

  def beforeTearDown(self):
    transaction.abort()
    if 'request_instance' in self.software_instance.REQUEST:
      self.software_instance.REQUEST['request_instance'] = None

  def test_request_requiredParameter(self):
    good_request_kw = self.request_kw.copy()
    # in order to have unique requested title
    good_request_kw['software_title'] = self.generateNewSoftwareTitle()

    # check that correct request does not raise
    self.software_instance.requestInstance(**good_request_kw)

    # substract parameters
    request_kw = good_request_kw.copy()
    request_kw.pop('software_release')
    self.assertRaises(KeyError, self.software_instance.requestInstance,
                      **request_kw)

    request_kw = good_request_kw.copy()
    request_kw.pop('software_title')
    self.assertRaises(KeyError, self.software_instance.requestInstance,
                      **request_kw)

    request_kw = good_request_kw.copy()
    request_kw.pop('software_type')
    self.assertRaises(KeyError, self.software_instance.requestInstance,
                      **request_kw)

    request_kw = good_request_kw.copy()
    request_kw.pop('instance_xml')
    self.assertRaises(KeyError, self.software_instance.requestInstance,
                      **request_kw)

    request_kw = good_request_kw.copy()
    request_kw.pop('sla_xml')
    self.assertRaises(KeyError, self.software_instance.requestInstance,
                      **request_kw)

    request_kw = good_request_kw.copy()
    request_kw.pop('shared')
    self.assertRaises(KeyError, self.software_instance.requestInstance,
                      **request_kw)

    request_kw = good_request_kw.copy()
    request_kw.pop('state')
    self.assertRaises(KeyError, self.software_instance.requestInstance,
                      **request_kw)

  def test_request_createdInstance(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()

    # check that correct request does not raise
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertNotEqual(None, requested_instance)

    self.assertEqual(request_kw['software_title'],
                     requested_instance.getTitle())
    self.assertEqual('Software Instance',
                     requested_instance.getPortalType())
    self.assertEqual('validated',
                     requested_instance.getValidationState())
    self.assertEqual('start_requested',
                     requested_instance.getSlapState())
    self.assertEqual(request_kw['software_release'],
                     requested_instance.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
                     requested_instance.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
                     requested_instance.getSlaXml())
    self.assertEqual(request_kw['software_type'],
                     requested_instance.getSourceReference())

  def test_request_sameTitle(self):
    # check that correct request does not raise
    self.assertRaises(ValueError, self.software_instance.requestInstance,
                      **self.request_kw)

  def test_request_shared_True(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()
    request_kw['shared'] = True

    # check that correct request does not raise
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertNotEqual(None, requested_instance)

    self.assertEqual(request_kw['software_title'],
                     requested_instance.getTitle())
    self.assertEqual('Slave Instance',
                     requested_instance.getPortalType())
    self.assertEqual('validated',
                     requested_instance.getValidationState())
    self.assertEqual('start_requested',
                     requested_instance.getSlapState())
    self.assertEqual(request_kw['software_release'],
                     requested_instance.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
                     requested_instance.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
                     requested_instance.getSlaXml())
    self.assertEqual(request_kw['software_type'],
                     requested_instance.getSourceReference())

  def test_request_shared_unsupported(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()
    request_kw['shared'] = 'True'

    self.assertRaises(ValueError, self.software_instance.requestInstance,
                      **request_kw)

  def test_request_unindexed(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()

    # check that correct request does not raise
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertNotEqual(None, requested_instance)

    self.assertEqual(request_kw['software_title'],
        requested_instance.getTitle())
    self.assertEqual('Software Instance',
        requested_instance.getPortalType())
    self.assertEqual('validated',
        requested_instance.getValidationState())
    self.assertEqual('start_requested',
        requested_instance.getSlapState())
    self.assertEqual(request_kw['software_release'],
        requested_instance.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
        requested_instance.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
        requested_instance.getSlaXml())
    self.assertEqual(request_kw['software_type'],
        requested_instance.getSourceReference())

    transaction.commit()

    self.assertRaises(NotImplementedError, self.software_instance.requestInstance,
        **request_kw)

  def test_request_double(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()

    # check that correct request does not raise
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertNotEqual(None, requested_instance)

    self.assertEqual(request_kw['software_title'],
        requested_instance.getTitle())
    self.assertEqual('Software Instance',
        requested_instance.getPortalType())
    self.assertEqual('validated',
        requested_instance.getValidationState())
    self.assertEqual('start_requested',
        requested_instance.getSlapState())
    self.assertEqual(request_kw['software_release'],
        requested_instance.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
        requested_instance.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
        requested_instance.getSlaXml())
    self.assertEqual(request_kw['software_type'],
        requested_instance.getSourceReference())

    self.tic()

    # check that correct request does not raise
    self.software_instance.requestInstance(**request_kw)

    requested_instance2 = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertNotEqual(None, requested_instance2)
    self.assertEqual(requested_instance2.getRelativeUrl(),
      requested_instance.getRelativeUrl())

    self.assertEqual(request_kw['software_title'],
        requested_instance2.getTitle())
    self.assertEqual('Software Instance',
        requested_instance2.getPortalType())
    self.assertEqual('validated',
        requested_instance2.getValidationState())
    self.assertEqual('start_requested',
        requested_instance2.getSlapState())
    self.assertEqual(request_kw['software_release'],
        requested_instance2.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
        requested_instance2.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
        requested_instance2.getSlaXml())
    self.assertEqual(request_kw['software_type'],
        requested_instance2.getSourceReference())

  def test_request_duplicated(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()

    duplicate = self.software_instance.Base_createCloneDocument(batch_mode=1)
    duplicate.edit(
        reference='TESTSI-%s' % self.generateNewId(),
        title=request_kw['software_title'])
    duplicate.validate()
    self.portal.portal_workflow._jumpToStateFor(duplicate, 'start_requested')

    duplicate2 = self.software_instance.Base_createCloneDocument(batch_mode=1)
    duplicate2.edit(
        reference='TESTSI-%s' % self.generateNewId(),
        title=request_kw['software_title'])
    duplicate2.validate()
    self.portal.portal_workflow._jumpToStateFor(duplicate2, 'start_requested')

    self.software_instance.getSpecialiseValue(
        portal_type='Instance Tree').edit(
            successor_list=[
                duplicate.getRelativeUrl(),
                duplicate2.getRelativeUrl(),
                self.software_instance.getRelativeUrl()
            ]
        )
    self.tic()

    self.assertRaises(ValueError, self.software_instance.requestInstance,
        **request_kw)

  def test_request_destroyed_state(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()
    request_kw['state'] = 'destroyed'

    # check that correct request does not raise
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    # requesting with destroyed state shall not create new instance
    self.assertEqual(None, requested_instance)

  def test_request_two_different(self):
    request_kw = self.request_kw.copy()
    # in order to have unique requested title
    request_kw['software_title'] = self.generateNewSoftwareTitle()

    # check that correct request does not raise
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()

    self.software_instance.requestInstance(**request_kw)

    requested_instance2 = self.software_instance.REQUEST.get(
        'request_instance')

    self.assertNotEqual(requested_instance.getRelativeUrl(),
      requested_instance2.getRelativeUrl())

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl()])

  def test_request_tree_change_indexed(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C

    When B requests C tree shall change to:

    A
    |
    A
    |
    B
    |
    C"""
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])

    self.tic() # in order to recalculate tree

    B_instance.requestInstance(**request_kw)
    C1_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertEqual(C_instance.getRelativeUrl(), C1_instance.getRelativeUrl())

    self.assertSameSet(self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl()])
    self.assertSameSet(B_instance.getSuccessorList(),
        [C_instance.getRelativeUrl()])

  def test_request_tree_change_not_indexed(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C

    When B requests C tree in next transaction, but before indexation,
    the system shall disallow the operation."""
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])

    transaction.commit()

    self.assertRaises(NotImplementedError, B_instance.requestInstance,
        **request_kw)

  @expectedFailure
  def test_request_tree_change_same_transaction(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C

    When B requests C tree in the same transaction the system shall
    disallow the operation."""
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])

    self.assertRaises(NotImplementedError, B_instance.requestInstance,
        **request_kw)

  def test_request_started_stopped_destroyed(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertNotEqual(None, requested_instance)

    self.assertEqual(request_kw['software_title'],
        requested_instance.getTitle())
    self.assertEqual('Software Instance',
        requested_instance.getPortalType())
    self.assertEqual('validated',
        requested_instance.getValidationState())
    self.assertEqual('start_requested',
        requested_instance.getSlapState())
    self.assertEqual(request_kw['software_release'],
        requested_instance.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
        requested_instance.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
        requested_instance.getSlaXml())
    self.assertEqual(request_kw['software_type'],
        requested_instance.getSourceReference())

    self.tic()

    request_kw['state'] = 'stopped'
    self.software_instance.requestInstance(**request_kw)
    requested_instance2 = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertNotEqual(None, requested_instance2)
    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())

    self.assertEqual(request_kw['software_title'],
        requested_instance2.getTitle())
    self.assertEqual('Software Instance',
        requested_instance2.getPortalType())
    self.assertEqual('validated',
        requested_instance2.getValidationState())
    self.assertEqual('stop_requested',
        requested_instance2.getSlapState())
    self.assertEqual(request_kw['software_release'],
        requested_instance2.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
        requested_instance2.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
        requested_instance2.getSlaXml())
    self.assertEqual(request_kw['software_type'],
        requested_instance2.getSourceReference())

    self.tic()

    request_kw['state'] = 'destroyed'
    self.software_instance.requestInstance(**request_kw)
    requested_instance3 = self.software_instance.REQUEST.get(
        'request_instance')
    self.assertEqual(None, requested_instance3)

    # in case of destruction instance is not returned, so fetch it
    # directly form document
    requested_instance3 = self.software_instance.getSuccessorValue(
        portal_type='Software Instance')
    self.assertEqual(request_kw['software_title'],
        requested_instance3.getTitle())
    self.assertEqual('Software Instance',
        requested_instance3.getPortalType())
    self.assertEqual('validated',
        requested_instance3.getValidationState())
    self.assertEqual('destroy_requested',
        requested_instance3.getSlapState())
    self.assertEqual(request_kw['software_release'],
        requested_instance3.getUrlString())
    self.assertEqual(request_kw['instance_xml'],
        requested_instance3.getTextContent())
    self.assertEqual(request_kw['sla_xml'],
        requested_instance3.getSlaXml())
    self.assertEqual(request_kw['software_type'],
        requested_instance3.getSourceReference())

  def _countBang(self, document):
    return len([q for q in document.workflow_history[
        'instance_slap_interface_workflow'] if q['action'] == 'bang'])

  def test_request_started_no_bang(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(requested_instance)
    self.software_instance.requestInstance(**request_kw)
    requested_instance2 = self.software_instance.REQUEST.get(
        'request_instance')
    transaction.commit()

    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())
    self.assertEqual(bang_amount, self._countBang(requested_instance))

  def test_request_stopped_bang(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(requested_instance)

    request_kw['state'] = 'stopped'
    self.software_instance.requestInstance(**request_kw)
    transaction.commit()
    requested_instance2 = self.software_instance.REQUEST.get(
        'request_instance')

    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())
    self.assertEqual(bang_amount+1, self._countBang(requested_instance))

  def test_request_destroyed_bang(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(requested_instance)

    request_kw['state'] = 'destroyed'
    self.software_instance.requestInstance(**request_kw)
    transaction.commit()
    requested_instance2 = self.software_instance.getSuccessorValue(
        portal_type='Software Instance')

    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())
    self.assertEqual(bang_amount+1, self._countBang(requested_instance))

  def test_request_tree_change_indexed_shared(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C

    When B requests C tree shall change to:

    A
    |
    A
    |
    B
    |
    C"""
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    request_kw['shared'] = True
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])

    self.tic() # in order to recalculate tree

    B_instance.requestInstance(**request_kw)
    C1_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertEqual(C_instance.getRelativeUrl(), C1_instance.getRelativeUrl())

    self.assertSameSet(self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl()])
    self.assertSameSet(B_instance.getSuccessorList(),
        [C_instance.getRelativeUrl()])

  def test_request_tree_change_not_indexed_shared(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C

    When B requests C tree in next transaction, but before indexation,
    the system shall disallow the operation."""
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    request_kw['shared'] = True
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])

    transaction.commit()

    self.assertRaises(NotImplementedError, B_instance.requestInstance,
        **request_kw)

  @expectedFailure
  def test_request_tree_change_same_transaction_shared(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C

    When B requests C tree in the same transaction the system shall
    disallow the operation."""
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    request_kw['shared'] = True
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])

    self.assertRaises(NotImplementedError, B_instance.requestInstance,
        **request_kw)

  def test_request_software_release_bang(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(requested_instance)

    request_kw['software_release'] = self.generateNewSoftwareReleaseUrl()
    self.software_instance.requestInstance(**request_kw)
    requested_instance2 = self.software_instance.getSuccessorValue(
        portal_type='Software Instance')

    transaction.commit()

    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())
    self.assertEqual(request_kw['software_release'],
        requested_instance2.getUrlString())
    self.assertEqual(bang_amount+1, self._countBang(requested_instance))

  def test_request_software_type_bang(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(requested_instance)

    request_kw['software_type'] = self.generateNewSoftwareReleaseUrl()
    self.software_instance.requestInstance(**request_kw)
    requested_instance2 = self.software_instance.getSuccessorValue(
        portal_type='Software Instance')

    transaction.commit()

    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())
    self.assertEqual(request_kw['software_type'],
        requested_instance2.getSourceReference())
    self.assertEqual(bang_amount+1, self._countBang(requested_instance))

  def test_request_instance_xml_bang(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(requested_instance)

    request_kw['instance_xml'] = self.generateSafeXml()
    self.software_instance.requestInstance(**request_kw)
    requested_instance2 = self.software_instance.getSuccessorValue(
        portal_type='Software Instance')

    transaction.commit()

    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())
    self.assertEqual(request_kw['instance_xml'],
        requested_instance2.getTextContent())
    self.assertEqual(bang_amount+1, self._countBang(requested_instance))

  def test_request_sla_xml_bang(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(requested_instance)

    request_kw['sla_xml'] = self.generateSafeXml()
    self.software_instance.requestInstance(**request_kw)
    requested_instance2 = self.software_instance.getSuccessorValue(
        portal_type='Software Instance')

    transaction.commit()

    self.assertEqual(requested_instance.getRelativeUrl(),
        requested_instance2.getRelativeUrl())
    self.assertEqual(request_kw['sla_xml'],
        requested_instance2.getSlaXml())
    self.assertEqual(bang_amount+1, self._countBang(requested_instance))

  def test_update_connection_bang_requester(self):
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)

    requested_instance = self.software_instance.REQUEST.get(
        'request_instance')

    self.tic()

    bang_amount = self._countBang(self.software_instance)

    connection_xml = self.generateSafeXml()
    requested_instance.updateConnection(connection_xml=connection_xml)

    transaction.commit()

    self.assertEqual(bang_amount+1, self._countBang(self.software_instance))


class TestSlapOSCoreInstanceSlapInterfaceWorkflowTransfer(SlapOSTestCaseMixin):
  """Tests instance.requestTransfer"""
  launch_caucase = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    new_id = self.generateNewId()

    self.request_kw = dict(
        software_release=self.generateNewSoftwareReleaseUrl(),
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        shared=False,
        state="started"
    )

    # prepare part of tree
    self.instance_tree = portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    self.software_instance = portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)

    self.instance_tree.edit(
        title=self.request_kw['software_title'],
        reference="TESTHS-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        root_slave=self.request_kw['shared'],
        successor=self.software_instance.getRelativeUrl()
    )
    self.instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(self.instance_tree, 'start_requested')

    self.software_instance.edit(
        title=self.request_kw['software_title'],
        reference="TESTSI-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=self.instance_tree.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(self.software_instance, 'start_requested')
    self.software_instance.validate()
    self.tic()

    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    transaction.abort()
    if 'request_instance' in self.software_instance.REQUEST:
      self.software_instance.REQUEST['request_instance'] = None

  def _makeProject(self):
    project = self.portal.project_module.newContent()
    project.edit(reference="TESTPROJ-%s" % project.getId())
    project.validate()

    self.tic()
    return project

  def _makeOrganisation(self):
    organisation = self.portal.organisation_module.newContent()
    organisation.edit(reference="TESTSITE-%s" % organisation.getId())
    organisation.validate()

    self.tic()
    return organisation

  def test_RequesterInstance_requestTransfer_Unauthorized(self):
    destination_section = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    
    self.login()
    self.assertRaises(Unauthorized, self.instance_tree.requestTransfer, 
      destination=None,
      destination_project=None)

    self.login(destination_section.getUserId())
    self.assertRaises(Unauthorized, self.instance_tree.requestTransfer, 
      destination=None,
      destination_project=None)

    self.login()
    other_user = self.makePerson(user=1)
    self.assertEqual(1 , len(other_user.objectValues(portal_type="ERP5 Login")))

    self.instance_tree.setDestinationSectionValue(destination_section)
    self.tic()

    self.assertRaises(Unauthorized, self.instance_tree.requestTransfer, 
      destination=None,
      destination_project=None)
    self.login(other_user.getUserId())
    self.assertRaises(Unauthorized, self.instance_tree.requestTransfer, 
      destination=None,
      destination_project=None)

    self.login(destination_section.getUserId())
    self.assertEqual(self.instance_tree.requestTransfer(
      destination=None,
      destination_project=None), None)

  def test_RequesterInstance_requestTransfer_project(self):
    destination_section = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.instance_tree.setDestinationSectionValue(destination_section)

    self.login()
    project = self._makeProject()
    other_project = self._makeProject()
    self.tic()

    self.login(destination_section.getUserId())
    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), None)
    self.assertEqual(self.instance_tree.Item_getCurrentSiteValue(), None)

    # Place in a project    
    self.assertEqual(self.instance_tree.requestTransfer(
      destination=None,
      destination_project=project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(
      self.instance_tree.Item_getCurrentProjectValue(), project)
    self.assertEqual(
      self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(
      self.instance_tree.Item_getCurrentSiteValue(), None)

    self.assertEqual(1,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    self.login(destination_section.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.instance_tree.requestTransfer(
      destination=None,
      destination_project=None), None)
    self.tic()

    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), project)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(2,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # Place in another project    
    self.assertEqual(self.instance_tree.requestTransfer(
      destination=None,
      destination_project=other_project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(self.instance_tree.Item_getCurrentSiteValue(), None)

    self.assertEqual(3,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(destination_section.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.instance_tree.requestTransfer(
      destination_project=None,
      destination=None), None)
    self.tic()

    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(self.instance_tree.Item_getCurrentSiteValue(), None)

    self.assertEqual(4,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_RequesterInstance_requestTransfer_owner(self):
    destination_section = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.instance_tree.setDestinationSectionValue(destination_section)

    self.login()
    organisation = self._makeOrganisation()
    other_organisation = self._makeOrganisation()
    self.tic()

    self.login(destination_section.getUserId())

    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), None)

    self.assertEqual(self.instance_tree.requestTransfer(
       destination=organisation.getRelativeUrl(),
       destination_project=None), None)

    self.tic()
    
    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(self.instance_tree.Item_getCurrentSiteValue(), organisation)

    self.assertEqual(1,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    self.login(destination_section.getUserId())

    self.assertEqual(self.instance_tree.requestTransfer(
      destination_project=None,
      destination=None), None)
    self.tic()

    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(self.instance_tree.Item_getCurrentSiteValue(), organisation)

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # Place in another project    
    self.assertEqual(self.instance_tree.requestTransfer(
      destination_project=None,
      destination=other_organisation.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(self.instance_tree.Item_getCurrentSiteValue(), other_organisation)

    self.assertEqual(3,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(destination_section.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.instance_tree.requestTransfer(
      destination_project=None,
      destination=None), None)
    self.tic()

    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(self.instance_tree.Item_getCurrentSiteValue(), other_organisation)

    self.assertEqual(4,
      len(self.instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_generateCertificate(self):
    self.login()
    self.software_instance.setSslKey(None)
    self.software_instance.setSslCertificate(None)
    self.software_instance.setDestinationReference(None)

    self.software_instance.generateCertificate()
    self.assertNotEqual(self.software_instance.getSslKey(), None)
    self.assertNotEqual(self.software_instance.getSslCertificate(), None)

    certificate_login_list = self.software_instance.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]

    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getSourceReference(), None)
    ssl_certificate = x509.load_pem_x509_certificate(self.software_instance.getSslCertificate())
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = [i.value for i in ssl_certificate.subject if i.oid == NameOID.COMMON_NAME][0]
    self.assertEqual(certificate_login.getReference().decode("UTF-8"), cn)

    self.assertRaises(ValueError, self.software_instance.generateCertificate)

  def test_revokeCertificate(self):
    self.login()
    self.assertRaises(ValueError, self.software_instance.revokeCertificate)
    certificate_login_list = self.software_instance.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 0)

  def test_revokeAndGenerateCertificate(self):
    self.login()

    ssl_key = self.software_instance.getSslKey()
    ssl_certificate = self.software_instance.getSslCertificate()

    self.assertNotEqual(self.software_instance.getSslKey(), None)
    self.assertNotEqual(self.software_instance.getSslCertificate(), None)

    self.assertRaises(ValueError, self.software_instance.revokeCertificate)

    self.software_instance.generateCertificate()
    self.assertNotEqual(self.software_instance.getSslKey(), None)
    self.assertNotEqual(self.software_instance.getSslCertificate(), None)

    certificate_login_list = self.software_instance.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]
    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getSourceReference(), None)

    self.assertNotEqual(self.software_instance.getSslKey(),
      ssl_key)
    self.assertNotEqual(self.software_instance.getSslCertificate(),
      ssl_certificate)

    ssl_key = self.software_instance.getSslKey()
    ssl_certificate = self.software_instance.getSslCertificate()

    self.software_instance.revokeCertificate()
    self.software_instance.generateCertificate()
    self.assertNotEqual(self.software_instance.getSslKey(), None)
    self.assertNotEqual(self.software_instance.getSslCertificate(), None)

    self.assertNotEqual(self.software_instance.getSslKey(),
      ssl_key)
    self.assertNotEqual(self.software_instance.getSslCertificate(),
      ssl_certificate)

    certificate_login_list = self.software_instance.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 2)
    another_certificate_login = [ i for i in certificate_login_list
                                   if i.getId() != certificate_login.getId()][0]

    self.assertEqual(another_certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(another_certificate_login.getReference(), None)
    self.assertNotEqual(another_certificate_login.getSourceReference(), None)

    self.assertEqual(certificate_login.getValidationState(), 'invalidated')
    self.assertNotEqual(certificate_login.getReference(),
      another_certificate_login.getReference())
    self.assertNotEqual(certificate_login.getSourceReference(),
      another_certificate_login.getSourceReference())

