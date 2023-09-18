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
from erp5.component.document.SoftwareInstance import SoftwareInstance, \
  DisconnectedSoftwareTree, CyclicSoftwareTree
from Products.ERP5Type.Utils import str2unicode
import transaction
from cryptography import x509
from cryptography.x509.oid import NameOID

class TestSlapOSCoreInstanceSlapInterfaceWorkflow(SlapOSTestCaseMixin):
  """Tests instance.requestInstance"""

  require_certificate = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    new_id = self.generateNewId()
    self.project = self.addProject()

    self.request_kw = dict(
        software_release=self.generateNewSoftwareReleaseUrl(),
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        shared=False,
        state="started",
        project_reference=self.project.getReference()
    )

    # prepare part of tree
    instance_tree = portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    self.software_instance = portal.software_instance_module\
        .newContent(portal_type="Software Instance")

    instance_tree.edit(
        title=self.request_kw['software_title'],
        reference="TESTHS-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        root_slave=self.request_kw['shared'],
        successor=self.software_instance.getRelativeUrl(),
        follow_up_value=self.project
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
        specialise=instance_tree.getRelativeUrl(),
        follow_up_value=self.project,
        ssl_key='foo',
        ssl_certificate='bar'
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


  def test_request_tree_disconnected(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C

    Them force C to be disconnected:

    A
    |
    A
    |
    B C


    When A requests C the request should fail.
    """
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

    self.tic()  # in order to recalculate tree

    self.software_instance.setSuccessorList([B_instance.getRelativeUrl()])
    self.tic()  # in order to recalculate tree

    self.assertRaises(DisconnectedSoftwareTree, self.software_instance.requestInstance, **request_kw)

    # Just re-set sucessor fixes the problem    
    self.software_instance.setSuccessorList([B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])
    self.tic()  # in order to recalculate tree

    self.software_instance.requestInstance(**request_kw)
    C1_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertEqual(C_instance.getRelativeUrl(), C1_instance.getRelativeUrl())

  def test_request_check_cycle(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |
    B
    |
    C
    |
    D

    Them force D to request A to be cycled (dupplicated successor related):

    A
    |
    A
    |\
    B D
    |/
    C

    In normal conditions there is no raise because either DisconnectedSoftwareTree is raised before,
    so we hot patch the checkConnected to ensure we get the proper raise 
    """
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    B_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')


    request_kw['software_title'] = self.generateNewSoftwareTitle()
    C_instance.requestInstance(**request_kw)
    D_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl()])

    self.assertSameSet(
        B_instance.getSuccessorList(), [C_instance.getRelativeUrl()])

    self.assertSameSet(
        C_instance.getSuccessorList(), [D_instance.getRelativeUrl()])

    self.tic()  # in order to recalculate tree
    
    def checkConnected(self, graph, root):
      "Patch and return skip"
      return

    checkConnected_original = SoftwareInstance.checkConnected
    try:
      SoftwareInstance.checkConnected = checkConnected
      request_kw['software_title'] = B_instance.getTitle()
      self.assertRaises(CyclicSoftwareTree, D_instance.requestInstance, **request_kw)
    finally:
      SoftwareInstance.checkConnected = checkConnected_original
  

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

  def test_request_tree_edit_parameters_change_not_indexed(self):
    """Checks tree change forced by request

    For a tree like:

    A
    |
    A
    |\
    B C
    |
    D

    When C requests D tree in a while C requests D, but before indexation,
    the system shall disallow the operation."""
    request_kw = self.request_kw.copy()

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    B_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    self.software_instance.requestInstance(**request_kw)
    C_instance = self.software_instance.REQUEST.get('request_instance')

    request_kw['software_title'] = self.generateNewSoftwareTitle()
    B_instance.requestInstance(**request_kw)
    D_instance = self.software_instance.REQUEST.get('request_instance')

    self.assertSameSet(
        self.software_instance.getSuccessorList(),
        [B_instance.getRelativeUrl(), C_instance.getRelativeUrl()])

    self.assertSameSet(
        B_instance.getSuccessorList(), [D_instance.getRelativeUrl()])

    # Ensure all is indexed first
    self.tic()
  
    # B edits twice w/o a problem w/o indexation problems
    request_kw['instance_xml'] = self.generateSafeXml()
    B_instance.requestInstance(**request_kw)
    
    transaction.commit()
    C_instance.requestInstance(**request_kw)
    
    transaction.commit()
    self.assertSameSet(
        C_instance.getSuccessorList(), [D_instance.getRelativeUrl()])

    self.assertSameSet(
        B_instance.getSuccessorList(), [])


    # B request must fails since indexation didnt finished up properly
    # which would lead to dupplicated set on sucessor
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
  require_certificate = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    new_id = self.generateNewId()
    self.project = self.addProject()

    self.request_kw = dict(
        software_release=self.generateNewSoftwareReleaseUrl(),
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        shared=False,
        state="started",
        project_reference=self.project.getReference()
    )

    # prepare part of tree
    self.instance_tree = portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    self.software_instance = portal.software_instance_module\
        .newContent(portal_type="Software Instance")

    self.instance_tree.edit(
        title=self.request_kw['software_title'],
        reference="TESTHS-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        root_slave=self.request_kw['shared'],
        successor=self.software_instance.getRelativeUrl(),
        follow_up_value=self.project
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
        specialise=self.instance_tree.getRelativeUrl(),
        follow_up_value=self.project,
        ssl_key='foo',
        ssl_certificate='bar'
    )
    self.portal.portal_workflow._jumpToStateFor(self.software_instance, 'start_requested')
    self.software_instance.validate()
    self.tic()

    person_user = self.makePerson(self.project)
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
    self.assertNotEqual(certificate_login.getCsrId(), None)
    ssl_certificate = x509.load_pem_x509_certificate(self.software_instance.getSslCertificate())
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = [i.value for i in ssl_certificate.subject if i.oid == NameOID.COMMON_NAME][0]
    self.assertEqual(str2unicode(certificate_login.getReference()), cn)
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
    self.assertNotEqual(certificate_login.getCsrId(), None)

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
    self.assertNotEqual(another_certificate_login.getCsrId(), None)

    self.assertEqual(certificate_login.getValidationState(), 'invalidated')
    self.assertNotEqual(certificate_login.getReference(),
      another_certificate_login.getReference())
    self.assertNotEqual(certificate_login.getCsrId(),
      another_certificate_login.getCsrId())

