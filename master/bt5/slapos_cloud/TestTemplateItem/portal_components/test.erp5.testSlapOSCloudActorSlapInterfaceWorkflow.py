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


class TestSlapOSCorePersonRequest(SlapOSTestCaseMixin):

  require_certificate = 1
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)

    self.project = self.addProject()
    person_user = self.makePerson(self.project)
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
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
    )

    # software_title is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )

    # software_type is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )

    # instance_xml is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )

    # instance_xml is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )

    # sla_xml is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )

    # shared is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      state=state,
      project_reference=self.project.getReference()
    )

    # state is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      project_reference=self.project.getReference()
    )

    # project_reference is mandatory
    self.assertRaises(TypeError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared
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
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
    )

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title="started",
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="started",
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
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
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
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
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
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
    self.assertEqual("HOSTSUBS-%s" % instance_tree.getId(),
                      instance_tree.getReference())
    self.assertEqual("validated", instance_tree.getValidationState())
    self.assertEqual(person.getRelativeUrl(),
                     instance_tree.getDestinationSection())

  def test_Person_requestSoftwareInstance_InstanceTreeNotReindexed(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
    )

  def test_Person_requestSoftwareInstance_updateInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
    )
    instance_tree = person.REQUEST.get('request_instance_tree')
    # instance_tree_reference = instance_tree.getReference()

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

    try:
      person.requestSoftwareInstance(
        software_release=software_release2,
        software_title=software_title,
        software_type=software_type2,
        instance_xml=instance_xml2,
        sla_xml=sla_xml2,
        shared=shared2,
        state=state2,
        project_reference=self.project.getReference()
      )
    except NotImplementedError:
      pass
    else:
      raise AssertionError('User is not supposed to change the release/type/shared')

    self.assertEqual(software_release,
                      instance_tree.getUrlString())
    self.assertEqual(software_title, instance_tree.getTitle())
    self.assertEqual(software_type, instance_tree.getSourceReference())
    self.assertEqual(instance_xml, instance_tree.getTextContent())
    self.assertEqual(sla_xml, instance_tree.getSlaXml())
    self.assertEqual(shared, instance_tree.getRootSlave())
    self.assertEqual("start_requested", instance_tree.getSlapState())
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
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
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
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
    shared = True

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="stopped",
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
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
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
    shared = True

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state="stopped",
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
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
      project_reference=self.project.getReference()
    )
    instance_tree2 = person.REQUEST.get('request_instance_tree')
    self.assertEqual("start_requested", instance_tree2.getSlapState())
    self.assertNotEqual(instance_tree.getRelativeUrl(),
                         instance_tree2.getRelativeUrl())


class TestSlapOSCoreWorkgroupRequest(SlapOSTestCaseMixin):

  def test_Workgroup_requestSoftwareInstance_createInstanceTree(self):
    project = self.addProject()
    workgroup = self.portal.workgroup_module.newContent(
      portal_type='Workgroup'
    )
    self.tic()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
    shared = True
    state = "started"

    workgroup.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=project.getReference()
    )
    instance_tree = workgroup.REQUEST.get('request_instance_tree')
    self.assertEqual(software_release,
                      instance_tree.getUrlString())
    self.assertEqual(software_title, instance_tree.getTitle())
    self.assertEqual(software_type, instance_tree.getSourceReference())
    self.assertEqual(instance_xml, instance_tree.getTextContent())
    self.assertEqual(sla_xml, instance_tree.getSlaXml())
    self.assertEqual(shared, instance_tree.getRootSlave())
    self.assertEqual("start_requested", instance_tree.getSlapState())
    self.assertEqual("HOSTSUBS-%s" % instance_tree.getId(),
                      instance_tree.getReference())
    self.assertEqual("validated", instance_tree.getValidationState())
    self.assertEqual(workgroup.getRelativeUrl(),
                     instance_tree.getDestinationSection())


class TestSlapOSCorePersonWithWorkgroupRequest(SlapOSTestCaseMixin):

  require_certificate = 1
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)

    self.project = self.addProject()
    person_user = self.makePerson(self.project)

    self.workgroup = self.portal.workgroup_module.newContent(
      portal_type='Workgroup'
    )
    self.workgroup.newContent(
      portal_type='Assignment',
      destination_project_value=self.project,
      function='customer'
    ).open()
    self.workgroup.validate()

    person_user.newContent(
      portal_type='Assignment',
      destination_value=self.workgroup,
    ).open()

    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_PersonWithWorkgroup_requestSoftwareInstance_createInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
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
      project_reference=self.project.getReference()
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
    self.assertEqual("HOSTSUBS-%s" % instance_tree.getId(),
                      instance_tree.getReference())
    self.assertEqual("validated", instance_tree.getValidationState())
    self.assertEqual(self.workgroup.getRelativeUrl(),
                     instance_tree.getDestinationSection())

  def test_PersonWithWorkgroup_requestSoftwareInstance_updateWorkgroupInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
    shared = True
    state = "started"

    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title=software_title,
      destination_section_value=self.workgroup,
      follow_up_value=self.project,
      root_slave=shared,
      source_reference=software_type,
      url_string=software_release,
    )
    instance_tree.edit(reference="HOSTSUBS-%s" % instance_tree.getId())
    self.portal.portal_workflow._jumpToStateFor(instance_tree, 'validated')

    self.tic()

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )
    instance_tree2 = person.REQUEST.get('request_instance_tree')
    self.assertEqual(software_release,
                      instance_tree2.getUrlString())
    self.assertEqual(software_title, instance_tree2.getTitle())
    self.assertEqual(software_type, instance_tree2.getSourceReference())
    self.assertEqual(instance_xml, instance_tree2.getTextContent())
    self.assertEqual(sla_xml, instance_tree2.getSlaXml())
    self.assertEqual(shared, instance_tree2.getRootSlave())
    self.assertEqual("start_requested", instance_tree2.getSlapState())
    self.assertEqual("HOSTSUBS-%s" % instance_tree2.getId(),
                      instance_tree2.getReference())
    self.assertEqual("validated", instance_tree2.getValidationState())
    self.assertEqual(self.workgroup.getRelativeUrl(),
                     instance_tree2.getDestinationSection())

    self.assertEqual(instance_tree.getRelativeUrl(),
                      instance_tree2.getRelativeUrl())

  def test_PersonWithWorkgroup_requestSoftwareInstance_updatePersonInstanceTree(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
    shared = True
    state = "started"

    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title=software_title,
      destination_section_value=person,
      follow_up_value=self.project,
      root_slave=shared,
      source_reference=software_type,
      url_string=software_release,
    )
    instance_tree.edit(reference="HOSTSUBS-%s" % instance_tree.getId())
    self.portal.portal_workflow._jumpToStateFor(instance_tree, 'validated')

    self.tic()

    person.requestSoftwareInstance(
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )
    instance_tree2 = person.REQUEST.get('request_instance_tree')
    self.assertEqual(software_release,
                      instance_tree2.getUrlString())
    self.assertEqual(software_title, instance_tree2.getTitle())
    self.assertEqual(software_type, instance_tree2.getSourceReference())
    self.assertEqual(instance_xml, instance_tree2.getTextContent())
    self.assertEqual(sla_xml, instance_tree2.getSlaXml())
    self.assertEqual(shared, instance_tree2.getRootSlave())
    self.assertEqual("start_requested", instance_tree2.getSlapState())
    self.assertEqual("HOSTSUBS-%s" % instance_tree2.getId(),
                      instance_tree2.getReference())
    self.assertEqual("validated", instance_tree2.getValidationState())
    self.assertEqual(person.getRelativeUrl(),
                     instance_tree2.getDestinationSection())

    self.assertEqual(instance_tree.getRelativeUrl(),
                      instance_tree2.getRelativeUrl())

  def test_PersonWithWorkgroup_requestSoftwareInstance_raiseIfTwoCustomerWorkgroups(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.login()
    workgroup2 = self.portal.workgroup_module.newContent(
      portal_type='Workgroup'
    )
    workgroup2.newContent(
      portal_type='Assignment',
      destination_project_value=self.project,
      function='customer'
    ).open()
    workgroup2.validate()

    person.newContent(
      portal_type='Assignment',
      destination_value=workgroup2,
    ).open()

    self.tic()

    # Login as user
    self.login(person.getUserId())

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
    shared = True
    state = "started"

    self.tic()

    self.assertRaises(ValueError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )

  def test_PersonWithWorkgroup_requestSoftwareInstance_raiseIfTwoInstanceTreeFound(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    software_release = self.generateNewSoftwareReleaseUrl()
    software_title = "test"
    software_type = "test"
    instance_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance>
    </instance>
    """
    sla_xml = """<?xml version="1.0" encoding="utf-8"?>
    <instance />
    """
    shared = True
    state = "started"

    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title=software_title,
      destination_section_value=person,
      follow_up_value=self.project,
      root_slave=shared,
      source_reference=software_type,
      url_string=software_release,
    )
    instance_tree.edit(reference="HOSTSUBS-%s" % instance_tree.getId())
    self.portal.portal_workflow._jumpToStateFor(instance_tree, 'validated')

    instance_tree2 = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title=software_title,
      destination_section_value=self.workgroup,
      follow_up_value=self.project,
      root_slave=shared,
      source_reference=software_type,
      url_string=software_release,
    )
    instance_tree2.edit(reference="HOSTSUBS-%s" % instance_tree2.getId())
    self.portal.portal_workflow._jumpToStateFor(instance_tree2, 'validated')

    self.tic()

    self.assertRaises(NotImplementedError, person.requestSoftwareInstance,
      software_release=software_release,
      software_title=software_title,
      software_type=software_type,
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      state=state,
      project_reference=self.project.getReference()
    )
