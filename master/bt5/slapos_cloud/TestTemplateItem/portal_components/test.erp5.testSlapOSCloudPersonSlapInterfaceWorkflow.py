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
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager

class TestSlapOSCorePersonRequest(SlapOSTestCaseMixin):

  launch_caucase = 1
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)

    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_Person_requestSoftwareInstance_requiredParameter(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True
    state = "started"

    self.assertRaises(TypeError, person.requestSoftwareInstance)

    # software_release is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )

    # software_title is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )

    # software_type is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )

    # instance_xml is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )

    # instance_xml is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )

    # sla_xml is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      shared=shared,
      state=state,
    )

    # shared is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      state=state,
    )

    # state is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
    )

  def test_Person_requestSoftwareInstance_acceptedState(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True

    # Only started, stopped, destroyed
    self.assertRaises(ValueError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="foo",
    )

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title="started",
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="started",
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    self.assertEqual("start_requested", instance_tree.getSlapState())

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title="stopped",
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="stopped",
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    self.assertEqual("stop_requested", instance_tree.getSlapState())

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title="destroyed",
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="destroyed",
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    self.assertEqual(None, instance_tree)

  def test_Person_requestSoftwareInstance_returnInstanceTreeUrl(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True
    state = "started"

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    self.assertEqual("Instance Tree",
                      instance_tree.getPortalType())

  def test_Person_requestSoftwareInstance_createInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True
    state = "started"

    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_hosting_subscription_reference',
                       id_generator='uid')

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    self.assertEqual(software_release,
                      instance_tree.getUrlString())
    self.assertEqual(software_title, instance_tree.getTitle())
    self.assertEqual(software_type, instance_tree.getSourceReference())
    self.assertEqual(instance_xml, instance_tree.getTextContent())
    self.assertEqual(sla_xml, instance_tree.getSlaXml())
    self.assertEqual(shared, instance_tree.getRootSlave())
    self.assertEqual("start_requested", instance_tree.getSlapState())
    self.assertEqual("HOSTSUBS-%s" % (previous_id+1),
                      instance_tree.getReference())
    self.assertEqual("validated", instance_tree.getValidationState())

  def test_Person_requestSoftwareInstance_InstanceTreeNotReindexed(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True
    state = "started"

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )
    transaction.commit()

    self.assertRaises(NotImplementedError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )

  @expectedFailure
  def test_Person_requestSoftwareInstance_updateInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True
    state = "started"

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    instance_tree_reference = instance_tree.getReference()

    transaction.commit()
    self.tic()

    software_release2 = self.generateNewSoftwareReleaseUrl()
    software_type2 = "test2"
    instance_xml2 = """<?xml version='1.0' encoding='utf-8'?>
<instance>

</instance>"""
    sla_xml2 = """<?xml version='1.0' encoding='utf-8'?>
<instance>

</instance>"""
    shared2 = False
    state2 = "stopped"

    person.requestSoftwareInstance(
      software_release=software_release2,
      software_title=software_title,
      software_type=software_type2,
      instance_xml=instance_xml2,
      sla_xml=sla_xml2,
      shared=shared2,
      state=state2,
    )

    instance_tree2 = person.REQUEST.get('request_instance_tree')
    self.assertEqual(instance_tree.getRelativeUrl(),
                      instance_tree2.getRelativeUrl())
    self.assertEqual(instance_tree_reference,
                      instance_tree2.getReference())

    self.assertEqual(software_release2,
                      instance_tree.getUrlString())
    self.assertEqual(software_title, instance_tree.getTitle())
    self.assertEqual(software_type2, instance_tree.getSourceReference())
    self.assertEqual(instance_xml2, instance_tree.getTextContent())
    self.assertEqual(sla_xml2, instance_tree.getSlaXml())
    self.assertEqual(shared2, instance_tree.getRootSlave())
    self.assertEqual("stop_requested", instance_tree.getSlapState())
    self.assertEqual("validated", instance_tree.getValidationState())

  def test_Person_requestSoftwareInstance_duplicatedInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True
    state = "started"

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    transaction.commit()
    instance_tree2 = instance_tree.Base_createCloneDocument(
                                                                batch_mode=1)
    instance_tree2.validate()

    transaction.commit()
    self.tic()

    self.assertRaises(NotImplementedError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )

  def test_Person_requestSoftwareInstance_InstanceTreeNewTitle(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
</instance>"""
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
</instance>"""
    shared = True
    state = "started"

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
    )
    instance_tree = person.REQUEST.get('request_instance_tree')

    transaction.commit()

    software_release2 = self.generateNewSoftwareReleaseUrl()
    software_title2 = "test2"
    software_type2 = "test2"
    instance_xml2 = """<?xml version='1.0' encoding='utf-8'?>
<instance>

</instance>"""
    sla_xml2 = """<?xml version='1.0' encoding='utf-8'?>
<instance>

</instance>"""
    shared2 = False
    state2 = "stopped"

    person.requestSoftwareInstance(
      software_release=software_release2,
      software_title=software_title2,
      software_type=software_type2,
      instance_xml=instance_xml2,
      sla_xml=sla_xml2,
      shared=shared2,
      state=state2,
    )

    instance_tree2 = person.REQUEST.get('request_instance_tree')
    self.assertNotEqual(instance_tree.getRelativeUrl(),
                      instance_tree2.getRelativeUrl())
    self.assertNotEqual(instance_tree.getReference(),
                      instance_tree2.getReference())

    self.assertEqual(software_release2,
                      instance_tree2.getUrlString())
    self.assertEqual(software_title2, instance_tree2.getTitle())
    self.assertEqual(software_type2, instance_tree2.getSourceReference())
    self.assertEqual(instance_xml2, instance_tree2.getTextContent())
    self.assertEqual(sla_xml2, instance_tree2.getSlaXml())
    self.assertEqual(shared2, instance_tree2.getRootSlave())
    self.assertEqual("stop_requested", instance_tree2.getSlapState())
    self.assertEqual("validated", instance_tree2.getValidationState())

  def test_Person_requestSoftwareInstance_deletedInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="stopped",
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    transaction.commit()
    self.tic()

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="destroyed",
    )
    instance_tree2 = person.REQUEST.get('request_instance_tree')
    self.assertEqual(None, instance_tree2)
    self.assertEqual("destroy_requested", instance_tree.getSlapState())

  def test_Person_requestSoftwareInstance_noConflictWithDeletedInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = "test"
    shared = True

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="stopped",
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    transaction.commit()
    self.tic()
    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="destroyed",
    )
    self.assertEqual("destroy_requested", instance_tree.getSlapState())
    transaction.commit()
    self.tic()

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="started",
    )
    instance_tree2 = person.REQUEST.get('request_instance_tree')
    self.assertEqual("start_requested", instance_tree2.getSlapState())
    self.assertNotEqual(instance_tree.getRelativeUrl(),
                         instance_tree2.getRelativeUrl())

class TestSlapOSCorePersonRequestComputeNode(SlapOSTestCaseMixin):

  def generateNewComputeNodeTitle(self):
    return 'My Comp %s' % self.generateNewId()

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_request_requiredParameter(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    # compute_node_title is mandatory
    self.assertRaises(TypeError, person.requestComputeNode)

    # if provided does not raise
    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(compute_node_title=compute_node_title)

  def test_request(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

  def test_request_createdComputeNode(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_computer_reference',
                       id_generator='uid')

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)
    self.assertEqual(compute_node_title, compute_node.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url, compute_node.absolute_url())
    self.assertEqual(compute_node_reference, compute_node.getReference())
    self.assertEqual('COMP-%s' % (previous_id + 1), compute_node.getReference())
    self.assertEqual('validated', compute_node.getValidationState())
    self.assertEqual('open/personal', compute_node.getAllocationScope())
    self.assertEqual('close', compute_node.getCapacityScope())

  def test_request_notReindexedCompute(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(compute_node_title=compute_node_title)
    transaction.commit()
    self.assertRaises(NotImplementedError, person.requestComputeNode,
                      compute_node_title=compute_node_title)

  def test_multiple_request_createdComputeNode(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    previous_id = self.getPortalObject().portal_ids\
        .generateNewId(id_group='slap_computer_reference',
                       id_generator='uid')

    compute_node_title = self.generateNewComputeNodeTitle()
    compute_node_title2 = self.generateNewComputeNodeTitle()
    person.requestComputeNode(compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)
    self.assertEqual(compute_node_title, compute_node.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url, compute_node.absolute_url())
    self.assertEqual(compute_node_reference, compute_node.getReference())
    self.assertEqual('COMP-%s' % (previous_id + 1), compute_node.getReference())
    self.assertEqual('validated', compute_node.getValidationState())
    self.assertEqual('open/personal', compute_node.getAllocationScope())
    self.assertEqual('close', compute_node.getCapacityScope())

    self.tic()

    # request again the same compute_node
    person.requestComputeNode(compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)
    self.assertEqual(compute_node_title, compute_node.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url, compute_node.absolute_url())
    self.assertEqual(compute_node_reference, compute_node.getReference())
    self.assertEqual('COMP-%s' % (previous_id + 1), compute_node.getReference())
    self.assertEqual('validated', compute_node.getValidationState())
    self.assertEqual('open/personal', compute_node.getAllocationScope())
    self.assertEqual('close', compute_node.getCapacityScope())

    # and now another one
    person.requestComputeNode(compute_node_title=compute_node_title2)

    # check what is returned via request
    compute_node_url2 = person.REQUEST.get('compute_node')
    compute_node_absolute_url2 = person.REQUEST.get('compute_node_url')
    compute_node_reference2 = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url2)
    self.assertNotEqual(None, compute_node_absolute_url2)
    self.assertNotEqual(None, compute_node_reference2)

    # check that compute_nodes are really different objects
    self.assertNotEqual(compute_node_url2, compute_node_url)

    # check that title is ok
    compute_node2 = person.restrictedTraverse(compute_node_url2)
    self.assertEqual(compute_node_title2, compute_node2.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url2, compute_node2.absolute_url())
    self.assertEqual(compute_node_reference2, compute_node2.getReference())
    self.assertEqual('COMP-%s' % (previous_id + 2), compute_node2.getReference())
    self.assertEqual('validated', compute_node2.getValidationState())
    self.assertEqual('open/personal', compute_node2.getAllocationScope())
    self.assertEqual('close', compute_node2.getCapacityScope())

  def test_request_duplicatedComputeNode(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)

    sm = getSecurityManager()
    try:
      self.login()
      compute_node2 = compute_node.Base_createCloneDocument(batch_mode=1)
      compute_node2.validate()
    finally:
      setSecurityManager(sm)
    self.tic()

    self.assertRaises(NotImplementedError, person.requestComputeNode,
                      compute_node_title=compute_node_title)


class TestSlapOSCorePersonRequestProject(SlapOSTestCaseMixin):

  def generateNewProjectTitle(self):
    return 'My Project %s' % self.generateNewId()

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_Person_requestProject_title_is_mandatoty(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestProject)

  def test_Person_requestProject(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    project_title = self.generateNewProjectTitle()
    person.requestProject(project_title=project_title)

    self.tic()
    self.login()
    # check what is returned via request
    project_relative_url = person.REQUEST.get('project_relative_url')
    project_reference = person.REQUEST.get('project_reference')

    self.assertNotEqual(None, project_relative_url)
    self.assertNotEqual(None, project_reference)
    
    project = person.restrictedTraverse(project_relative_url)
    self.assertEqual(project.getTitle(), project_title)
    self.assertEqual(project.getValidationState(), "validated")
    self.assertEqual(project.getDestinationDecision(), person.getRelativeUrl())


  def test_Person_requestProject_duplicated(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    project_title = self.generateNewProjectTitle()
    person.requestProject(project_title=project_title)
    self.tic()
    self.login()

    # check what is returned via request
    project_relative_url = person.REQUEST.get('project_relative_url')
    project_reference = person.REQUEST.get('project_reference')

    self.assertNotEqual(None, project_relative_url)
    self.assertNotEqual(None, project_reference)

    project = person.restrictedTraverse(project_relative_url)
    self.assertEqual(project.getTitle(), project_title)
    self.assertEqual(project.getValidationState(), "validated")
    self.assertEqual(project.getDestinationDecision(), person.getRelativeUrl())

    project2 = project.Base_createCloneDocument(batch_mode=1)
    project2.validate()
    self.tic()

    self.login(person.getUserId())
    self.assertRaises(NotImplementedError, person.requestProject,
                      project_title=project_title)

  def test_Person_requestProject_request_again(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    project_title = self.generateNewProjectTitle()
    person.requestProject(project_title=project_title)

    # check what is returned via request
    project_relative_url = person.REQUEST.get('project_relative_url')
    project_reference = person.REQUEST.get('project_reference')

    self.assertNotEqual(None, project_relative_url)
    self.assertNotEqual(None, project_reference)

    self.tic()
    self.login()
    # check what is returned via request
    person.REQUEST.set('project_relative_url', None)
    person.REQUEST.set('project_reference', None)

    self.login(person.getUserId())
    person.requestProject(project_title=project_title)

    # check what is returned via request
    same_project_relative_url = person.REQUEST.get('project_relative_url')
    same_project_reference = person.REQUEST.get('project_reference')

    self.assertEqual(same_project_relative_url, project_relative_url)
    self.assertEqual(same_project_reference, project_reference)



class TestSlapOSCorePersonRequestOrganisation(SlapOSTestCaseMixin):

  def generateNewOrganisationTitle(self):
    return 'My Organisation %s' % self.generateNewId()

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_Person_requestOrganisation_title_is_mandatoty(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestOrganisation)

  def test_Person_requestOrganisation(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestOrganisation(organisation_title=organisation_title)

    self.tic()
    self.login()
    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)
    
    organisation = person.restrictedTraverse(organisation_relative_url)
    self.assertEqual(organisation.getTitle(), organisation_title)
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertEqual(organisation.getRoleId(), "client")
    self.assertIn("O-", organisation.getReference())


  def test_Person_requestOrganisation_duplicated(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestOrganisation(organisation_title=organisation_title)
    self.tic()
    self.login()

    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)

    organisation = person.restrictedTraverse(organisation_relative_url)
    self.assertEqual(organisation.getTitle(), organisation_title)
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertEqual(organisation.getRoleId(), "client")
    self.assertIn("O-", organisation.getReference())

    organisation2 = organisation.Base_createCloneDocument(batch_mode=1)
    organisation2.validate()
    self.tic()

    self.login(person.getUserId())
    self.assertRaises(NotImplementedError, person.requestOrganisation,
                      organisation_title=organisation_title)

  def test_Person_requestOrganisation_request_again(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestOrganisation(organisation_title=organisation_title)

    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)

    self.tic()
    self.login()
    # check what is returned via request
    person.REQUEST.set('organisation_relative_url', None)

    self.login(person.getUserId())
    person.requestOrganisation(organisation_title=organisation_title)

    # check what is returned via request
    same_organisation_relative_url = person.REQUEST.get('organisation_relative_url')
    self.assertEqual(same_organisation_relative_url, organisation_relative_url)


  def test_Person_requestOrganisation_dont_conflict_with_site(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestOrganisation(organisation_title=organisation_title)
    self.tic()
    self.login()

    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)

    organisation = person.restrictedTraverse(organisation_relative_url)
    self.assertEqual(organisation.getTitle(), organisation_title)
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertEqual(organisation.getRoleId(), "client")
    self.assertIn("O-", organisation.getReference())

    organisation2 = organisation.Base_createCloneDocument(batch_mode=1)
    organisation2.edit(role="host")
    organisation2.validate()
    
    person.REQUEST.set('organisation_relative_url', None)

    self.tic() 

    self.login(person.getUserId())
    person.requestOrganisation(organisation_title=organisation_title)

    self.tic()
    self.login()
    # check what is returned via request
    same_organisation_relative_url = person.REQUEST.get('organisation_relative_url')
    self.assertEqual(same_organisation_relative_url, organisation_relative_url)

class TestSlapOSCorePersonRequestSite(SlapOSTestCaseMixin):

  def generateNewOrganisationTitle(self):
    return 'My Site %s' % self.generateNewId()

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_Person_requestSite_title_is_mandatoty(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestSite)

  def test_Person_requestSite(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestSite(organisation_title=organisation_title)

    self.tic()
    self.login()
    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)
    
    organisation = person.restrictedTraverse(organisation_relative_url)
    self.assertEqual(organisation.getTitle(), organisation_title)
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertEqual(organisation.getRoleId(), "host")
    self.assertIn("SITE-", organisation.getReference())


  def test_Person_requestSite_duplicated(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestSite(organisation_title=organisation_title)
    self.tic()
    self.login()

    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)

    organisation = person.restrictedTraverse(organisation_relative_url)
    self.assertEqual(organisation.getTitle(), organisation_title)
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertEqual(organisation.getRoleId(), "host")
    self.assertIn("SITE-", organisation.getReference())

    organisation2 = organisation.Base_createCloneDocument(batch_mode=1)
    organisation2.validate()
    self.tic()

    self.login(person.getUserId())
    self.assertRaises(NotImplementedError, person.requestSite,
                      organisation_title=organisation_title)

  def test_Person_requestSite_request_again(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestSite(organisation_title=organisation_title)

    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)

    self.tic()
    self.login()
    # check what is returned via request
    person.REQUEST.set('organisation_relative_url', None)

    self.login(person.getUserId())
    person.requestSite(organisation_title=organisation_title)

    # check what is returned via request
    same_organisation_relative_url = person.REQUEST.get('organisation_relative_url')
    self.assertEqual(same_organisation_relative_url, organisation_relative_url)


  def test_Person_requestSite_dont_conflict_with_site(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    organisation_title = self.generateNewOrganisationTitle()
    person.requestSite(organisation_title=organisation_title)
    self.tic()
    self.login()

    # check what is returned via request
    organisation_relative_url = person.REQUEST.get('organisation_relative_url')

    self.assertNotEqual(None, organisation_relative_url)

    organisation = person.restrictedTraverse(organisation_relative_url)
    self.assertEqual(organisation.getTitle(), organisation_title)
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertEqual(organisation.getRoleId(), "host")
    self.assertIn("SITE-", organisation.getReference())

    organisation2 = organisation.Base_createCloneDocument(batch_mode=1)
    organisation2.edit(role="client")
    organisation2.validate()
    
    person.REQUEST.set('organisation_relative_url', None)

    self.tic() 

    self.login(person.getUserId())
    person.requestSite(organisation_title=organisation_title)

    self.tic()
    self.login()
    # check what is returned via request
    same_organisation_relative_url = person.REQUEST.get('organisation_relative_url')
    self.assertEqual(same_organisation_relative_url, organisation_relative_url)

class TestSlapOSCorePersonRequestNetwork(SlapOSTestCaseMixin):

  def generateNewNetworkTitle(self):
    return 'My Network %s' % self.generateNewId()

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_Person_requestNetwork_title_is_mandatoty(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestNetwork)

  def test_Person_requestNetwork(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    network_title = self.generateNewNetworkTitle()
    person.requestNetwork(network_title=network_title)

    self.tic()
    self.login()
    # check what is returned via request
    network_relative_url = person.REQUEST.get('computer_network_relative_url')

    self.assertNotEqual(None, network_relative_url)
    
    network = person.restrictedTraverse(network_relative_url)
    self.assertEqual(network.getSourceAdministration(),
                    person.getRelativeUrl())
    self.assertEqual(network.getTitle(), network_title)
    self.assertEqual(network.getValidationState(), "validated")
    self.assertIn("NET-", network.getReference())


  def test_Person_requestNetwork_duplicated(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    network_title = self.generateNewNetworkTitle()
    person.requestNetwork(network_title=network_title)
    self.tic()
    self.login()

    # check what is returned via request
    network_relative_url = person.REQUEST.get('computer_network_relative_url')

    self.assertNotEqual(None, network_relative_url)

    network = person.restrictedTraverse(network_relative_url)
    self.assertEqual(network.getSourceAdministration(),
                    person.getRelativeUrl())
    self.assertEqual(network.getTitle(), network_title)
    self.assertEqual(network.getValidationState(), "validated")
    self.assertIn("NET-", network.getReference())

    network2 = network.Base_createCloneDocument(batch_mode=1)
    network2.validate()
    self.tic()

    self.login(person.getUserId())
    self.assertRaises(NotImplementedError, person.requestNetwork,
                      network_title=network_title)

  def test_Person_requestNetwork_request_again(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    network_title = self.generateNewNetworkTitle()
    person.requestNetwork(network_title=network_title)

    # check what is returned via request
    network_relative_url = person.REQUEST.get('computer_network_relative_url')

    self.assertNotEqual(None, network_relative_url)

    self.tic()
    self.login()
    # check what is returned via request
    person.REQUEST.set('computer_network_relative_url', None)

    self.login(person.getUserId())
    person.requestNetwork(network_title=network_title)

    # check what is returned via request
    same_network_relative_url = person.REQUEST.get('computer_network_relative_url')
    self.assertEqual(same_network_relative_url, network_relative_url)


class TestSlapOSCorePersonRequestToken(SlapOSTestCaseMixin):

  def generateNewTokenUrl(self):
    return 'https://%s.no.where/%s' % (
      self.generateNewId(),
      self.generateNewId())

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass
  
  def test_Person_requestToken_requested_url_is_mandatory(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestToken)

  def test_Person_requestToken(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    request_url = self.generateNewTokenUrl()
    person.requestToken(request_url=request_url)

    self.tic()
    self.login()
    # check what is returned via request
    token_id = person.REQUEST.get('token')

    self.assertNotEqual(None, token_id)
    
    token = self.portal.access_token_module[token_id]
    self.assertEqual(token.getAgent(),
                    person.getRelativeUrl())
    self.assertEqual(token.getUrlString(), request_url)
    self.assertEqual(token.getValidationState(), "validated")
    self.assertEqual(
      token.getPortalType(), "One Time Restricted Access Token")
    self.assertEqual(token.getUrlMethod(), "POST")



class TestSlapOSCorePersonNotify(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.person = self.makePerson()
    self.tic()

  def beforeTearDown(self):
    pass
  
  def test_Person_notify_mandatory_argument(self):
    self.assertRaises(TypeError, self.person.notify)
    self.assertRaises(TypeError, self.person.notify, support_request_title="a")
    self.assertRaises(TypeError, self.person.notify, support_request_title="a", support_request_description="b")

  def test_Person_notify_unknown_aggregate(self):
    self.assertRaises(KeyError, self.person.notify,
     support_request_title="a", support_request_description="b", aggregate="c")

  def test_Person_notify_computer_node(self):
    compute_node, _ = self._makeComputeNode()
    self._test_Person_notify(compute_node)

  def test_Person_notify_instance_tree(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person
    )
    self._test_Person_notify(instance_tree)

  def test_Person_notify_software_installation(self):
    self._makeComputeNode()
    software_installation = self.portal\
       .software_installation_module.template_software_installation\
       .Base_createCloneDocument(batch_mode=1)
    software_installation.edit(
       url_string=self.generateNewSoftwareReleaseUrl(),
       aggregate=self.compute_node.getRelativeUrl(),
       reference='TESTSOFTINSTS-%s' % self.generateNewId(),
       title='Start requested for %s' % self.compute_node.getUid()
     )
    software_installation.validate()
    software_installation.requestStart()
    self._test_Person_notify(software_installation)

  def _test_Person_notify(self, aggregate_value):

    # Step 1: Notify
    self.person.notify(
      support_request_title="A",
      support_request_description="B",
      aggregate=aggregate_value.getRelativeUrl()
    )

    # Step 2: Check return
    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertNotEqual(None, support_request_relative_url)
    support_request_in_progress = self.person.REQUEST.get(
      "support_request_in_progress", None) 
    self.assertEqual(support_request_in_progress, support_request_relative_url)

    support_request = self.portal.restrictedTraverse(support_request_in_progress)
    self.assertEqual(support_request.getSimulationState(),
                     "validated")
    self.assertEqual(support_request.getTitle(), "A")
    self.assertEqual(support_request.getDescription(), "B")
    self.assertNotEqual(support_request.getStartDate(), None)
    self.assertEqual(support_request.getDestinationDecision(),
      self.person.getRelativeUrl())
    self.assertEqual(support_request.getAggregateValue(),
      aggregate_value)
    self.assertEqual(support_request.getResource(),
      "service_module/slapos_crm_monitoring")

    # Step 3: Reset REQUEST and check in progress before catalog
    self.person.REQUEST.set(
       "support_request_relative_url", None)
    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertEqual(None, support_request_relative_url)

    self.person.notify(
      support_request_title="A",
      support_request_description="B",
      aggregate=aggregate_value.getRelativeUrl()
    )

    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertNotEqual(None, support_request_relative_url)
 
    self.assertEqual(support_request_in_progress, support_request_relative_url)

    self.tic()

    # Step 4: Reset parameters and check if the support request is got again.
    self.person.REQUEST.set(
       "support_request_relative_url", None)
    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertEqual(None, support_request_relative_url)
    support_request_in_progress = self.person.REQUEST.set(
      "support_request_in_progress", None)
    support_request_in_progress = self.person.REQUEST.set(
      "support_request_in_progress", None) 
    self.assertEqual(support_request_in_progress, None)

    self.commit()
    self.person.notify(
      support_request_title="A",
      support_request_description="B",
      aggregate=aggregate_value.getRelativeUrl()
    )

    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertNotEqual(None, support_request_relative_url)
    support_request_in_progress = self.person.REQUEST.get(
      "support_request_in_progress", None) 
    self.assertEqual(support_request_in_progress, support_request_relative_url)
  
    # Check if it is the same Support Request as before
    self.assertEqual(support_request.getRelativeUrl(),
      support_request_relative_url)

    # Step 5: Retry the same thing, but now on suspended state
    support_request.suspend()

    self.tic()
    self.person.REQUEST.set(
       "support_request_relative_url", None)
    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertEqual(None, support_request_relative_url)
    support_request_in_progress = self.person.REQUEST.set(
      "support_request_in_progress", None)
    support_request_in_progress = self.person.REQUEST.set(
      "support_request_in_progress", None) 
    self.assertEqual(support_request_in_progress, None)

    self.commit()
    self.person.notify(
      support_request_title="A",
      support_request_description="B",
      aggregate=aggregate_value.getRelativeUrl()
    )

    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertNotEqual(None, support_request_relative_url)
    support_request_in_progress = self.person.REQUEST.get(
      "support_request_in_progress", None) 
    self.assertEqual(support_request_in_progress, support_request_relative_url)
  

    # Check if it is the same Support Request as before and still suspended
    self.assertEqual(support_request.getRelativeUrl(),
      support_request_relative_url)
    self.assertEqual(support_request.getSimulationState(), "suspended")

    # Step 6: If the support request is closed, create indeed a new one.
    support_request.invalidate()
    self.tic()

    self.person.REQUEST.set("support_request_relative_url", None)
    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertEqual(None, support_request_relative_url)
    support_request_in_progress = self.person.REQUEST.set(
      "support_request_in_progress", None)
    support_request_in_progress = self.person.REQUEST.set(
      "support_request_in_progress", None) 
    self.assertEqual(support_request_in_progress, None)

    self.commit()
    self.person.notify(
      support_request_title="A",
      support_request_description="B",
      aggregate=aggregate_value.getRelativeUrl()
    )

    support_request_relative_url = self.person.REQUEST.get(
       "support_request_relative_url", None) 
    self.assertNotEqual(None, support_request_relative_url)
    support_request_in_progress = self.person.REQUEST.get(
      "support_request_in_progress", None) 
    self.assertEqual(support_request_in_progress, support_request_relative_url)

    # Check if it is the another Support Request
    self.assertEqual(support_request.getSimulationState(), "invalidated")

    self.assertNotEqual(support_request.getRelativeUrl(),
      support_request_relative_url)
