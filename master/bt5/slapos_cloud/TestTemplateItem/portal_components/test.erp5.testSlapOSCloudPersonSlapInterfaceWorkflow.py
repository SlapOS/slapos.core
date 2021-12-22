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
    self.assertEqual('open', compute_node.getCapacityScope())

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
    self.assertEqual('open', compute_node.getCapacityScope())

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
    self.assertEqual('open', compute_node.getCapacityScope())

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
    self.assertEqual('open', compute_node2.getCapacityScope())

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