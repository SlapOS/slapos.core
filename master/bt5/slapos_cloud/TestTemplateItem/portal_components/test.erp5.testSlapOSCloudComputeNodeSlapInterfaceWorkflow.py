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
from Products.ERP5Type.Utils import str2unicode
import transaction
from Products.ERP5Type.Errors import UnsupportedWorkflowMethod
from cryptography import x509
from cryptography.x509.oid import NameOID

class TestSlapOSCoreComputeNodeSlapInterfaceWorkflow(SlapOSTestCaseMixin):

  require_certificate = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()
    # Clone compute_node document
    self.compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    new_id = self.generateNewId()
    self.compute_node.edit(
      title="compute node %s" % (new_id, ),
      reference="TESTCOMP-%s" % (new_id, ),
      follow_up_value=self.project
    )
    self.compute_node.validate()
    self.tic()

  def beforeTearDown(self):
    SlapOSTestCaseMixin.beforeTearDown(self)
    self.portal.REQUEST['compute_node_key'] = None
    self.portal.REQUEST['compute_node_certificate'] = None

  def _getCommonNameList(self, ssl_certificate):
    cn_list = [i.value for i in ssl_certificate.subject \
                 if i.oid == NameOID.COMMON_NAME and i.value != "erp5-user"]

    self.assertEqual(len(cn_list), 1)
    return cn_list[0]


  def test_generateCertificate(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]
    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getCsrId(), None)

    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(certificate_login.getReference()), cn)

  def test_generateCertificate_twice(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    self.assertEqual(None, self.compute_node.getSourceReference())

    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]
    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getCsrId(), None)

    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(certificate_login.getReference()), cn)

    self.assertRaises(ValueError, self.compute_node.generateCertificate)
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))

  def test_approveComputeNodeRegistration(self):
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
    self.tic()
    self.login(self.person_user.getUserId())
    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title="Compute Node %s for %s" % (self.new_id, self.person_user.getReference()),
      reference="TESTCOMP-%s" % self.new_id,
      follow_up_value=self.project
    )
    compute_node.approveComputeNodeRegistration()
    self.assertEqual('open', compute_node.getAllocationScope())
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
    self._makeComplexComputeNode(self.project)
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
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
    self.tic()
    self.login(self.person_user.getUserId())
    self.assertRaises(TypeError, self.compute_node.requestSoftwareRelease,
        state='available')
    transaction.abort()

  def test_requestSoftwareRelease_state_required(self):
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.assertRaises(TypeError, self.compute_node.requestSoftwareRelease,
        software_release_url=url)
    transaction.abort()

  def test_requestSoftwareRelease_available(self):
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
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
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
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
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
    self.tic()
    self.login(self.person_user.getUserId())
    url = self.generateNewSoftwareReleaseUrl()
    self.compute_node.requestSoftwareRelease(software_release_url=url,
        state='available')
    self.tic()
    self.cleanUpRequest()
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
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
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

  def test_requestSoftwareRelease_same_transaction(self):
    self.person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(self.person_user, self.project)
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
    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]
    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getCsrId(), None)

    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(certificate_login.getReference()), cn)

    self.assertNotEqual(certificate_login.getReference(),
                        self.compute_node.getReference())

    self.compute_node.revokeCertificate()
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))

    self.assertEqual(certificate_login.getValidationState(), 'invalidated')

  def test_revokeCertificateNoCertificate(self):
    self.login(self.compute_node.getUserId())
    self.assertRaises(ValueError, self.compute_node.revokeCertificate)
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertEqual(None, self.compute_node.getSourceReference())
    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 0)

  def test_revokeCertificate_twice(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)
    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]
    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getCsrId(), None)
    self.assertNotEqual(certificate_login.getReference(),
                        self.compute_node.getReference())

    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(certificate_login.getReference()), cn)
    self.compute_node.revokeCertificate()
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))

    self.assertEqual(certificate_login.getValidationState(), 'invalidated')

    self.assertRaises(ValueError, self.compute_node.revokeCertificate)
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    self.assertEqual(certificate_login.getValidationState(), 'invalidated')

  def test_renewCertificate(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)

    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]
    source_reference = certificate_login.getCsrId()

    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getCsrId(), None)
    self.assertNotEqual(certificate_login.getReference(),
                        self.compute_node.getReference())

    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(certificate_login.getReference()), cn)

    # TODO: Should we check for csr_id
    #self.assertTrue(certificate_login.getCsrId() in compute_node_certificate)
    self.assertNotEqual(None, source_reference)

    self.compute_node.revokeCertificate()
    self.compute_node.generateCertificate()
    
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(compute_node_key, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(compute_node_certificate, self.portal.REQUEST.get('compute_node_certificate'))

    self.assertEqual(certificate_login.getValidationState(), 'invalidated')
    self.assertEqual(certificate_login.getCsrId(), source_reference)
    self.assertNotEqual(certificate_login.getReference(), None)

    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 2)
    new_certificate_login = [i for i in certificate_login_list \
      if i.getId() != certificate_login.getId()][0]
    
    source_reference = certificate_login.getCsrId()
    self.assertEqual(new_certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(new_certificate_login.getReference(), None)
    self.assertNotEqual(new_certificate_login.getReference(),
      certificate_login.getReference())
  
    self.assertNotEqual(new_certificate_login.getCsrId(), None)
    self.assertNotEqual(new_certificate_login.getCsrId(),
      certificate_login.getCsrId())
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = [i.value for i in ssl_certificate.subject if i.oid == NameOID.COMMON_NAME][-1]
    self.assertEqual(str2unicode(new_certificate_login.getReference()), cn)
    self.assertNotEqual(str2unicode(certificate_login.getReference()), cn)
    self.assertNotEqual(certificate_login.getReference(),
                        self.compute_node.getReference())

  def test_renewCertificate_twice(self):
    self.login(self.compute_node.getUserId())
    self.compute_node.generateCertificate()
    compute_node_key = self.portal.REQUEST.get('compute_node_key')
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    self.assertNotEqual(None, compute_node_key)
    self.assertNotEqual(None, compute_node_certificate)

    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 1)
    certificate_login = certificate_login_list[0]
    source_reference = certificate_login.getCsrId()

    self.assertEqual(certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(certificate_login.getReference(), None)
    self.assertNotEqual(certificate_login.getCsrId(), None)

    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(certificate_login.getReference()), cn)
    self.assertNotEqual(certificate_login.getReference(),
                        self.compute_node.getReference())
    self.assertNotEqual(None, source_reference)

    self.compute_node.revokeCertificate()
    self.compute_node.generateCertificate()

    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(compute_node_key, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(compute_node_certificate, self.portal.REQUEST.get('compute_node_certificate'))

    self.assertEqual(certificate_login.getValidationState(), 'invalidated')
    self.assertEqual(certificate_login.getCsrId(), source_reference)
    self.assertNotEqual(certificate_login.getReference(), None)

    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 2)
    new_certificate_login = [i for i in certificate_login_list \
      if i.getId() != certificate_login.getId()][0]
    
    source_reference = certificate_login.getCsrId()
    self.assertEqual(new_certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(new_certificate_login.getReference(), None)
    self.assertNotEqual(new_certificate_login.getReference(),
      certificate_login.getReference())
  
    self.assertNotEqual(new_certificate_login.getCsrId(), None)
    self.assertNotEqual(new_certificate_login.getCsrId(),
      certificate_login.getCsrId())
    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(new_certificate_login.getReference()), cn)
    self.assertNotEqual(str2unicode(certificate_login.getReference()), cn)
    self.assertNotEqual(certificate_login.getReference(),
                        self.compute_node.getReference())

    self.compute_node.revokeCertificate()
    self.compute_node.generateCertificate()

    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(None, self.portal.REQUEST.get('compute_node_certificate'))
    self.assertNotEqual(compute_node_key, self.portal.REQUEST.get('compute_node_key'))
    self.assertNotEqual(compute_node_certificate, self.portal.REQUEST.get('compute_node_certificate'))

    self.assertEqual(new_certificate_login.getValidationState(), 'invalidated')
    self.assertNotEqual(new_certificate_login.getCsrId(), source_reference)
    self.assertNotEqual(new_certificate_login.getReference(), None)

    certificate_login_list = self.compute_node.objectValues(portal_type="Certificate Login")
    self.assertEqual(len(certificate_login_list), 3)

    third_certificate_login = [i for i in certificate_login_list \
      if i.getId() not in [certificate_login.getId(), new_certificate_login.getId()]][0]
    
    source_reference = new_certificate_login.getCsrId()
    self.assertEqual(third_certificate_login.getValidationState(), 'validated')
    self.assertNotEqual(third_certificate_login.getReference(), None)
    self.assertNotEqual(third_certificate_login.getReference(),
      certificate_login.getReference())
  
    self.assertNotEqual(third_certificate_login.getCsrId(), None)
    self.assertNotEqual(third_certificate_login.getCsrId(),
      new_certificate_login.getCsrId())

    compute_node_certificate = self.portal.REQUEST.get('compute_node_certificate')
    ssl_certificate = x509.load_pem_x509_certificate(compute_node_certificate)
    self.assertEqual(len(ssl_certificate.subject), 2)
    cn = self._getCommonNameList(ssl_certificate)
    self.assertEqual(str2unicode(third_certificate_login.getReference()), cn)
    self.assertNotEqual(str2unicode(new_certificate_login.getReference()), cn)
    self.assertNotEqual(third_certificate_login.getReference(),
                        self.compute_node.getReference())

    self.assertNotEqual(new_certificate_login.getReference(),
                        self.compute_node.getReference())

class TestSlapOSCoreComputeNodeSlapInterfaceWorkflowSupply(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    self.project = self.addProject()

    # Clone compute_node document
    compute_node = portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    # Clone person document
    person_user = self.makePerson(self.project, new_id=self.new_id, index=0)
    self.addProjectProductionManagerAssignment(person_user, self.project)
    self.tic()

    compute_node.edit(
      title="Compute Node %s for %s" % (self.new_id, person_user.getReference()),
      reference="TESTCOMP-%s" % self.new_id,
      follow_up_value=self.project
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
    self.cleanUpRequest()
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
    self.cleanUpRequest()
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
    self.cleanUpRequest()
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
    self.cleanUpRequest()
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
