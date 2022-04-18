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
from time import sleep
from zExceptions import Unauthorized
from unittest import expectedFailure
from Products.ERP5Type.Errors import UnsupportedWorkflowMethod


class TestSlapOSCoreComputeNodeSlapInterfaceWorkflow(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    # Clone compute_node document
    self.compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    self.compute_node.edit(
      title="compute node %s" % (new_id, ),
      reference="TESTCOMP-%s" % (new_id, )
    )
    self.compute_node.validate()
    self.tic()

  def beforeTearDown(self):
    SlapOSTestCaseMixin.beforeTearDown(self)
    self.portal.REQUEST['compute_node_key'] = None
    self.portal.REQUEST['compute_node_certificate'] = None

  def test_generateCertificate(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    self.assertNotEqual(None, self.compute_node.getDestinationReference())
    serial = '0x%x' % int(self.compute_node.getDestinationReference(), 16)
    self.assertTrue(serial in compute_node_certificate)
    self.assertTrue(self.compute_node.getReference() in compute_node_certificate.decode('string_escape'))

  def test_generateCertificate_twice(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    self.assertNotEqual(None, self.compute_node.getDestinationReference())
    serial = '0x%x' % int(self.compute_node.getDestinationReference(), 16)
    self.assertTrue(serial in compute_node_certificate)
    self.assertTrue(self.compute_node.getReference() in compute_node_certificate.decode('string_escape'))

    self.assertRaises(ValueError, self.compute_node.generateCertificate)
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))

  def test_approveComputeNodeRegistration(self):
    self.person_user = self.makePerson()
    self.login(self.person_user.getUserId())
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
      title="Compute Node %s for %s" % (self.new_id, self.person_user.getReference()),
      reference="TESTCOMP-%s" % self.new_id)
    compute_node.requestComputeNodeRegistration()
    compute_node.approveComputeNodeRegistration()
    self.assertEqual('open/personal', compute_node.getAllocationScope())
    self.assertEqual(self.person_user.getRelativeUrl(),
        compute_node.getSourceAdministration())
    self.assertEqual('validated', compute_node.getValidationState())

  def _countInstanceBang(self, instance, comment):
    return len([q for q in instance.workflow_history[
        'instance_slap_interface_workflow'] if q['action'] == 'bang' and \
            q['comment'] == comment])

  def _countComputeNodeeBang(self, compute_node, comment):
    return len([q for q in compute_node.workflow_history[
        'compute_node_slap_interface_workflow'] if q['action'] == \
            'report_compute_node_bang' and q['comment'] == comment])

  def test_reportComputeNodeBang(self):
    self._makeComplexComputeNode()
    self.login(self.compute_node.getUserId())
    comment = 'Bang from compute_node'
    started_instance = self.compute_node.partition1.getAggregateRelatedValue(
        portal_type='Software Instance')
    stopped_instance = self.compute_node.partition2.getAggregateRelatedValue(
        portal_type='Software Instance')
    destroyed_instance1 = self.compute_node.partition3.getAggregateRelatedValue(
        portal_type='Software Instance')
    destroyed_instance2 = self.compute_node.partition4.getAggregateRelatedValue(
        portal_type='Software Instance')

    # test sanity check -- do not trust _makeComplexComputeNode
    self.assertEqual('start_requested', started_instance.getSlapState())
    self.assertEqual('stop_requested', stopped_instance.getSlapState())
    self.assertEqual('destroy_requested', destroyed_instance1.getSlapState())
    self.assertEqual('destroy_requested', destroyed_instance2.getSlapState())

    # store counts before bang
    compute_node_bang_count = self._countComputeNodeeBang(self.compute_node, comment)
    started_instance_bang_count = self._countInstanceBang(started_instance,
        comment)
    stopped_instance_bang_count = self._countInstanceBang(stopped_instance,
        comment)
    destroyed_instance1_bang_count = self._countInstanceBang(
        destroyed_instance1, comment)
    destroyed_instance2_bang_count = self._countInstanceBang(
        destroyed_instance2, comment)

    self.compute_node.reportComputeNodeBang(comment=comment)
    self.tic()

    self.assertEqual(1+compute_node_bang_count,
        self._countComputeNodeeBang(self.compute_node, comment))
    self.assertEqual(1+started_instance_bang_count,
        self._countInstanceBang(started_instance, comment))
    self.assertEqual(1+stopped_instance_bang_count,
        self._countInstanceBang(stopped_instance, comment))
    self.assertEqual(destroyed_instance1_bang_count,
        self._countInstanceBang(destroyed_instance1, comment))
    self.assertEqual(destroyed_instance2_bang_count,
        self._countInstanceBang(destroyed_instance2, comment))

  def test_requestSoftwareRelease_software_release_url_required(self):
    self.person_user = self.makePerson()
    self.compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.tic()
    self.login(self.person_user.getUserId())
    self.assertRaises(TypeError, self.compute_node.requestSoftwareRelease,
        state='available')
    transaction.abort()

  def test_requestSoftwareRelease_state_required(self):
    self.person_user = self.makePerson()
    self.compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.assertRaises(TypeError, self.compute_node.requestSoftwareRelease,
        software_release_url=url)
    transaction.abort()

  def test_requestSoftwareRelease_available(self):
    self.person_user = self.makePerson()
    self.compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.compute_node.requestSoftwareRelease(software_release_url=url,
        state='available')
    self.tic()
    self.login()
    software_installation = self.compute_node.getAggregateRelatedValue(
        portal_type='Software Installation')
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual(url, software_installation.getUrlString())
    self.assertEqual('validated', software_installation.getValidationState())

  def test_requestSoftwareRelease_destroyed(self):
    self.person_user = self.makePerson()
    self.compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.compute_node.requestSoftwareRelease(software_release_url=url,
        state='destroyed')
    self.tic()
    self.login()
    software_installation = self.compute_node.getAggregateRelatedValue(
        portal_type='Software Installation')
    self.assertEqual(None, software_installation)

  def test_requestSoftwareRelease_available_destroyed(self):
    self.person_user = self.makePerson()
    self.compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.compute_node.requestSoftwareRelease(software_release_url=url,
        state='available')
    self.tic()
    self.login()
    software_installation = self.compute_node.getAggregateRelatedValue(
        portal_type='Software Installation')
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual(url, software_installation.getUrlString())
    self.assertEqual('validated', software_installation.getValidationState())

    self.login(self.person_user.getUserId())
    self.compute_node.requestSoftwareRelease(software_release_url=url,
        state='destroyed')

    self.tic()
    self.login()
    software_installation = self.compute_node.getAggregateRelatedValue(
        portal_type='Software Installation')
    self.assertEqual('destroy_requested', software_installation.getSlapState())
    self.assertEqual(url, software_installation.getUrlString())
    self.assertEqual('validated', software_installation.getValidationState())

  def test_requestSoftwareRelease_not_indexed(self):
    self.person_user = self.makePerson()
    self.compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.compute_node.requestSoftwareRelease(software_release_url=url,
        state='available')
    transaction.commit()
    self.assertRaises(NotImplementedError,
        self.compute_node.requestSoftwareRelease, software_release_url=url,
        state='available')
    transaction.abort()

  @expectedFailure
  def test_requestSoftwareRelease_same_transaction(self):
    self.person_user = self.makePerson()
    self.compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.compute_node.requestSoftwareRelease(software_release_url=url,
        state='available')
    self.assertRaises(NotImplementedError,
        self.compute_node.requestSoftwareRelease, software_release_url=url,
        state='available')
    transaction.abort()

  def test_revokeCertificate(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    self.assertNotEqual(None, self.compute_node.getDestinationReference())
    serial = '0x%x' % int(self.compute_node.getDestinationReference(), 16)
    self.assertTrue(serial in compute_node_certificate)
    self.assertTrue(self.compute_node.getReference() in compute_node_certificate.decode('string_escape'))

    self.compute_node.revokeCertificate()
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))

    self.assertEqual(None, self.compute_node.getDestinationReference())

  def test_revokeCertificateNoCertificate(self):
    self.login(self.compute_node.getUserId())
    self.assertRaises(ValueError, self.compute_node.revokeCertificate)
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertEqual(None, self.compute_node.getDestinationReference())

  def test_revokeCertificate_twice(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    self.assertNotEqual(None, self.compute_node.getDestinationReference())
    serial = '0x%x' % int(self.compute_node.getDestinationReference(), 16)
    self.assertTrue(serial in compute_node_certificate)
    self.assertTrue(self.compute_node.getReference() in compute_node_certificate.decode('string_escape'))

    self.compute_node.revokeCertificate()
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))

    self.assertEqual(None, self.compute_node.getDestinationReference())

    self.assertRaises(ValueError, self.compute_node.revokeCertificate)
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertEqual(None, self.compute_node.getDestinationReference())

  def test_renewCertificate(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    destination_reference = self.compute_node.getDestinationReference()

    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    self.assertNotEqual(None, destination_reference)
    serial = '0x%x' % int(self.compute_node.getDestinationReference(), 16)
    self.assertTrue(serial in compute_node_certificate)
    self.assertTrue(self.compute_node.getReference() in compute_node_certificate.decode('string_escape'))

    self.compute_node.revokeCertificate()
    self.compute_node.generateCertificate()
    
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(None, self.compute_node.getDestinationReference())

    self.assertNotEqual(compute_node_key, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(compute_node_certificate, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(destination_reference, self.compute_node.getDestinationReference())

  def test_renewCertificate_twice(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    destination_reference = self.compute_node.getDestinationReference()

    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    self.assertNotEqual(None, self.compute_node.getDestinationReference())
    serial = '0x%x' % int(self.compute_node.getDestinationReference(), 16)
    self.assertTrue(serial in compute_node_certificate)
    self.assertTrue(self.compute_node.getReference() in compute_node_certificate.decode('string_escape'))

    self.compute_node.revokeCertificate()
    self.compute_node.generateCertificate()
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(None, self.compute_node.getDestinationReference())

    self.assertNotEqual(compute_node_key, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(compute_node_certificate, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(destination_reference, self.compute_node.getDestinationReference())

    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    destination_reference = self.compute_node.getDestinationReference()

    self.compute_node.revokeCertificate()
    self.compute_node.generateCertificate()
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(None, self.compute_node.getDestinationReference())

    self.assertNotEqual(compute_node_key, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(compute_node_certificate, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(destination_reference, self.compute_node.getDestinationReference())

class TestSlapOSCoreComputeNodeSlapInterfaceWorkflowSupply(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()

    # Clone compute_node document
    compute_node = portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    # Clone person document
    person_user = self.makePerson(new_id=self.new_id, index=0)

    compute_node.edit(
      title="Compute Node %s for %s" % (self.new_id, person_user.getReference()),
      reference="TESTCOMP-%s" % self.new_id,
      source_administration=person_user.getRelativeUrl()
    )
    compute_node.validate()
    self.compute_node = compute_node

    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    if 'software_installation_url' in self.compute_node.REQUEST:
      self.compute_node.REQUEST['software_installation_url'] = None

  def test_supply_requiredParameter(self):
    software_release = self.generateNewSoftwareReleaseUrl()
    self.assertRaises(TypeError, self.compute_node.requestSoftwareRelease)
    self.assertRaises(TypeError, self.compute_node.requestSoftwareRelease,
        state="available")
    self.assertRaises(TypeError, self.compute_node.requestSoftwareRelease,
        software_release_url=software_release)
    self.assertRaises(ValueError, self.compute_node.requestSoftwareRelease,
        state="mana", software_release_url=software_release)

  def test_supply_available(self):
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

  def test_supply_destroyed(self):
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="destroyed",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertEqual(None, software_installation_url)

  def test_supply_available_nonIndexed(self):
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

    transaction.commit()

    self.assertRaises(NotImplementedError,
        self.compute_node.requestSoftwareRelease, state="available",
        software_release_url=software_release)

  def test_supply_available_destroyed_nonIndexed(self):
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

    transaction.commit()

    self.assertRaises(NotImplementedError,
        self.compute_node.requestSoftwareRelease, state="destroyed",
        software_release_url=software_release)

  def test_supply_available_createdSoftwareInstallation(self):
    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_software_installation_reference',
                       id_generator='uid')
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

  def test_multiple_supply_available_createdSoftwareInstallation(self):
    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_software_installation_reference',
                       id_generator='uid')
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

    self.tic()
    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url2 = self.compute_node.REQUEST.get(
        'software_installation_url')
    self.assertEqual(software_installation_url, software_installation_url2)

  def test_supply_available_destroyed(self):
    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_software_installation_reference',
                       id_generator='uid')
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

    self.tic()
    self.compute_node.requestSoftwareRelease(state="destroyed",
        software_release_url=software_release)

    software_installation_url2 = self.compute_node.REQUEST.get(
        'software_installation_url')
    self.assertEqual(software_installation_url, software_installation_url2)

    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url2)
    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('destroy_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

  def test_supply_available_destroyed_available(self):
    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_software_installation_reference',
                       id_generator='uid')
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

    self.tic()
    self.compute_node.requestSoftwareRelease(state="destroyed",
        software_release_url=software_release)

    software_installation_url2 = self.compute_node.REQUEST.get(
        'software_installation_url')
    self.assertEqual(software_installation_url, software_installation_url2)

    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url2)
    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('destroy_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

    self.tic()
    # XXX: This scenario shall be discussed...
    self.assertRaises(UnsupportedWorkflowMethod,
        self.compute_node.requestSoftwareRelease, state="available",
        software_release_url=software_release)

  def test_supply_available_destroyed_finalised_available(self):
    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_software_installation_reference',
                       id_generator='uid')
    software_release = self.generateNewSoftwareReleaseUrl()

    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)

    software_installation_url = self.compute_node.REQUEST.get(
        'software_installation_url')

    self.assertNotEqual(None, software_installation_url)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url)
    self.assertEqual(software_release, software_installation.getUrlString())

    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

    self.tic()
    self.compute_node.requestSoftwareRelease(state="destroyed",
        software_release_url=software_release)

    software_installation_url2 = self.compute_node.REQUEST.get(
        'software_installation_url')
    self.assertEqual(software_installation_url, software_installation_url2)

    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url2)
    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('destroy_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+1),
        software_installation.getReference())

    software_installation.invalidate()
    self.tic()
    self.compute_node.requestSoftwareRelease(state="available",
        software_release_url=software_release)
    software_installation_url3 = self.compute_node.REQUEST.get(
        'software_installation_url')
    self.assertNotEqual(software_installation_url, software_installation_url3)
    software_installation = self.compute_node.restrictedTraverse(
        software_installation_url3)
    self.assertEqual('Software Installation',
        software_installation.getPortalType())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual('SOFTINSTALL-%s' % (previous_id+2),
        software_installation.getReference())



class TestSlapOSCoreComputeNodeSlapInterfaceWorkflowTransfer(SlapOSTestCaseMixin):


  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()

    # Clone compute_node document
    compute_node = portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    # Clone person document
    person_user = self.makePerson(new_id=self.new_id, index=0)

    compute_node.edit(
      title="Compute Node %s for %s" % (self.new_id, person_user.getReference()),
      reference="TESTCOMP-%s" % self.new_id,
      source_administration=person_user.getRelativeUrl()
    )
    compute_node.validate()
    self.compute_node = compute_node

    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

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

  def test_Computer_requestTransfer_Unauthorized(self):
    source_administrator = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    site = self._makeOrganisation()
    
    self.login()
    self.assertRaises(Unauthorized, self.compute_node.requestTransfer,
      destination=site.getRelativeUrl(),
      destination_section=None,
      destination_project=None)

    self.login(source_administrator.getUserId())
    self.assertRaises(ValueError, self.compute_node.requestTransfer,
      destination=None,
      destination_section=None,
      destination_project=None)

    self.login()
    other_user = self.makePerson(user=1)
    self.assertEqual(1 , len(other_user.objectValues(portal_type="ERP5 Login")))

    self.compute_node.setSourceAdministrationValue(source_administrator)
    self.tic()

    self.assertRaises(Unauthorized, self.compute_node.requestTransfer,
      destination=None,
      destination_section=None,
      destination_project=None)

    self.login(other_user.getUserId())
    self.assertRaises(Unauthorized, self.compute_node.requestTransfer,
      destination=None,
      destination_section=None,
      destination_project=None)

    self.login(source_administrator.getUserId())
    self.assertEqual(self.compute_node.requestTransfer(
      destination=site.getRelativeUrl(),
      destination_section=None,
      destination_project=None), None)


  def test_Computer_requestTransfer_project(self):
    source_administrator = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.compute_node.setSourceAdministrationValue(source_administrator)

    self.login()
    project = self._makeProject()
    other_project = self._makeProject()
    site = self._makeOrganisation()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), None)

    # Place in a project    
    self.assertEqual(self.compute_node.requestTransfer(
      destination=site.getRelativeUrl(),
      destination_section=None,
      destination_project=project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), project)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    self.assertEqual(1,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)

    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_section=None,
      destination_project=None), None)
    self.tic()

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), project)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(2,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # Place in another project    
    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_section=None,
      destination_project=other_project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    self.assertEqual(3,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_section=None,
      destination_project=None), None)
    self.tic()

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    self.assertEqual(4,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_Computer_requestTransfer_owner(self):
    source_administrator = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.compute_node.setSourceAdministrationValue(source_administrator)

    self.login()
    organisation = self._makeOrganisation()
    other_organisation = self._makeOrganisation()
    site = self._makeOrganisation()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), None)

    self.assertEqual(self.compute_node.requestTransfer(
      destination=site.getRelativeUrl(),
      destination_project=None,
      destination_section=organisation.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), organisation)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    self.assertEqual(1,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    self.login(source_administrator.getUserId())

    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_section=None,
      destination_project=None), None)
    self.tic()

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # Place in another project    
    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_project=None,
      destination_section=other_organisation.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), other_organisation)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    self.assertEqual(3,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_section=None,
      destination_project=None), None)
    self.tic()

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    self.assertEqual(4,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_Computer_requestTransfer_site(self):
    source_administrator = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.compute_node.setSourceAdministrationValue(source_administrator)

    self.login()
    site = self._makeOrganisation()
    other_site = self._makeOrganisation()

    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), None)

    self.assertEqual(self.compute_node.requestTransfer(
      destination_section=None,
      destination_project=None,
      destination=site.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    self.assertEqual(1,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_section=None,
      destination_project=None), None)
    self.tic()

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), site)

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # Place in another project    
    self.assertEqual(self.compute_node.requestTransfer(
      destination_section=None,
      destination_project=None,
      destination=other_site.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), other_site)

    self.assertEqual(3,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # We don't remove from Project if destination project is not provided
    self.assertEqual(self.compute_node.requestTransfer(
      destination=None,
      destination_section=None,
      destination_project=None), None)
    self.tic()

    self.assertEqual(self.compute_node.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.compute_node.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(self.compute_node.Item_getCurrentSiteValue(), other_site)

    self.assertEqual(4,
      len(self.compute_node.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

