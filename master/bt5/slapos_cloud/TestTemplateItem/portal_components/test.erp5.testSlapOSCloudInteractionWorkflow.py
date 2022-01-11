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


class TestSlapOSCoreSlapOSCloudInteractionWorkflow(SlapOSTestCaseMixin):

  def check_Instance_validate(self, portal_type):
    project = self.addProject()
    self.person_user = self.makePerson(project)
    self.login(self.person_user.getUserId())

    # Instance Tree required for security.
    hs = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title="HS %s for %s" % (self.new_id, self.person_user.getReference()),
      reference="TESTHS-%s" % self.new_id,
      destination_reference="TESTHS-%s" % self.new_id,
      destination_section=self.person_user.getRelativeUrl(),
      follow_up_value=project
      )

    instance = self.portal.software_instance_module.newContent(
      portal_type=portal_type,
      title="Instance %s for %s" % (self.new_id, self.person_user.getReference()),
      reference="TESTINST-%s" % self.new_id,
      specialise_value=hs,
      follow_up_value=project
    )

    if portal_type == "Software Instance":
      self._addCertificateLogin(instance)
    self.tic()

    def verify_activeSense_call(self):
      if self.getRelativeUrl() == 'portal_alarms/slapos_allocate_instance':
        instance.portal_workflow.doActionFor(instance, action='edit_action',
          comment='activeSense triggered')
      else:
        return self.activeSense_call()

    from Products.ERP5Type.Document.Alarm import Alarm #pylint: disable=import-error

    Alarm.activeSense_call = Alarm.activeSense
    Alarm.activeSense = verify_activeSense_call
    try:
      instance.validate()
      self.tic()
    finally:
      Alarm.activeSense = Alarm.activeSense_call
    self.assertEqual(
        'activeSense triggered',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_SoftwareInstance_validate(self):
    return self.check_Instance_validate("Software Instance")

  def test_SlaveInstance_validate(self):
    return self.check_Instance_validate("Slave Instance")

  def check_SoftwareInstallation_changeState(self, method_id):
    project = self.addProject()
    self.person_user = self.makePerson(project)
    self.addProjectProductionManagerAssignment(self.person_user, project)
    self.tic()
    self.login(self.person_user.getUserId())
    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title="Compute Node %s for %s" % (self.new_id, self.person_user.getReference()),
      reference="TESTCOMP-%s" % self.new_id,
      follow_up_value=project
    )
    self._addCertificateLogin(compute_node)

    installation = self.portal.software_installation_module.newContent(
      portal_type='Software Installation',
      title="Installation %s for %s" % (self.new_id, self.person_user.getReference()),
      aggregate_value=compute_node,
      follow_up_value=project
      )
    self.tic()

    def verify_reindexObject_call(self, *args, **kw):
      if self.getRelativeUrl() == compute_node.getRelativeUrl():
        compute_node.portal_workflow.doActionFor(compute_node, action='edit_action',
          comment='reindexObject triggered on %s' % method_id)
      else:
        return self.reindexObject_call(*args, **kw)

    from Products.ERP5Type.Base import Base
    Base.reindexObject_call = Base._reindexObject
    Base._reindexObject = verify_reindexObject_call
    try:
      getattr(installation, method_id)()
      self.tic()
    finally:
      Base._reindexObject = Base.reindexObject_call
    self.assertEqual(
        'reindexObject triggered on %s' % method_id,
        compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_SoftwareInstallation_changeState_onStart(self):
    return self.check_SoftwareInstallation_changeState('requestStart')

  def test_SoftwareInstallation_changeState_onDestroy(self):
    return self.check_SoftwareInstallation_changeState('requestDestroy')

  def check_SoftwareInstance_changeState(self, method_id):
    project = self.addProject()
    self.person_user = self.makePerson(project)
    self.addProjectProductionManagerAssignment(self.person_user, project)

    new_id = self.generateNewId()
    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title="Compute Node %s for %s" % (new_id, self.person_user.getReference()),
      reference="TESTCOMP-%s" % new_id,
      follow_up_value=project
    )
    self._addCertificateLogin(compute_node)

    partition = compute_node.newContent(
      portal_type='Compute Partition',
      title="Partition Compute Node %s for %s" % (new_id,
        self.person_user.getReference()),
      reference="TESTPART-%s" % new_id)

    self.login(self.person_user.getUserId())

    instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance",
      title="Instance %s for %s" % (new_id, self.person_user.getReference()),
      reference="TESTINST-%s" % new_id,
      aggregate_value=partition,
      destination_reference="TESTINST-%s" % new_id,
      ssl_certificate="foo",
      ssl_key="bar",
      follow_up_value=project
      )

    request_kw = dict(
      software_release='http://example.org',
      software_type='http://example.org',
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
    )
    if method_id == 'requestDestroy':
      instance.requestStop(**request_kw)
    self.tic()

    def verify_reindexObject_call(self, *args, **kw):
      if self.getRelativeUrl() == partition.getRelativeUrl():
        partition.portal_workflow.doActionFor(partition, action='edit_action',
          comment='reindexObject triggered on %s' % method_id)
      else:
        return self.reindexObject_call(*args, **kw)

    # Replace activeSense by a dummy method
    from Products.ERP5Type.Base import Base
    Base.reindexObject_call = Base._reindexObject
    Base._reindexObject = verify_reindexObject_call
    try:
      getattr(instance, method_id)(**request_kw)
      self.tic()
    finally:
      Base._reindexObject = Base.reindexObject_call
    self.assertEqual(
        'reindexObject triggered on %s' % method_id,
        partition.workflow_history['edit_workflow'][-1]['comment'])

  def test_SoftwareInstance_changeState_onStart(self):
    return self.check_SoftwareInstance_changeState("requestStart")

  def test_SoftwareInstance_changeState_onStop(self):
    return self.check_SoftwareInstance_changeState("requestStop")

  def test_SoftwareInstance_changeState_onDestroy(self):
    return self.check_SoftwareInstance_changeState("requestDestroy")

  def check_change_instance_parameter(self, portal_type, method_id):
    project = self.addProject()
    self.person_user = self.makePerson(project)
    self.login(self.person_user.getUserId())

    instance = self.portal.software_instance_module.newContent(
      portal_type=portal_type,
      title="Instance %s for %s" % (self.new_id, self.person_user.getReference()),
      reference="TESTINST-%s" % self.new_id,
      destination_reference="TESTINST-%s" % self.new_id,
      ssl_certificate="foo",
      ssl_key="bar",
      follow_up_value=project
      )

    self.tic()
    self.assertEqual(None,
      instance.workflow_history['instance_slap_interface_workflow'][-1]['action'])

    instance.edit(**{method_id: self.generateSafeXml()})
    self.tic()
    self.assertEqual('bang',
      instance.workflow_history['instance_slap_interface_workflow'][-1]['action'])

  def test_change_instance_parameter_onInstanceUrlString(self):
    return self.check_change_instance_parameter("Software Instance",
                                                'url_string')

  def test_change_instance_parameter_onInstanceTextContent(self):
    return self.check_change_instance_parameter("Software Instance",
                                                'text_content')

  def test_change_instance_parameter_onInstanceSourceReference(self):
    return self.check_change_instance_parameter("Software Instance",
                                                'source_reference')

  def test_change_instance_parameter_onInstanceSlaXML(self):
    return self.check_change_instance_parameter("Software Instance",
                                                'sla_xml')

  def test_change_instance_parameter_onSlaveUrlString(self):
    return self.check_change_instance_parameter("Slave Instance",
                                                'url_string')

  def test_change_instance_parameter_onSlaveTextContent(self):
    return self.check_change_instance_parameter("Slave Instance",
                                                'text_content')

  def test_change_instance_parameter_onSlaveSourceReference(self):
    return self.check_change_instance_parameter("Slave Instance",
                                                'source_reference')

  def test_change_instance_parameter_onSlaveSlaXML(self):
    return self.check_change_instance_parameter("Slave Instance",
                                                'sla_xml')

  def test_SoftwareInstance_setSuccessorList(self):
    portal_type = "Software Instance"

    project = self.addProject()
    self.person_user = self.makePerson(project)
    self.login(self.person_user.getUserId())

    new_id = self.generateNewId()
    instance3 = self.portal.software_instance_module.newContent(
      portal_type=portal_type,
      title="Instance %s for %s" % (new_id, self.person_user.getReference()),
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      ssl_certificate="foo",
      ssl_key="bar",
      follow_up_value=project
      )

    new_id = self.generateNewId()
    instance2 = self.portal.software_instance_module.newContent(
      portal_type=portal_type,
      title="Instance %s for %s" % (new_id, self.person_user.getReference()),
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      ssl_certificate="foo",
      ssl_key="bar",
      successor_value=instance3,
      follow_up_value=project
      )

    new_id = self.generateNewId()
    instance1 = self.portal.software_instance_module.newContent(
      portal_type=portal_type,
      title="Instance %s for %s" % (new_id, self.person_user.getReference()),
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      ssl_certificate="foo",
      ssl_key="bar",
      successor_value=instance2,
      follow_up_value=project
      )

    self.tic()

    def verify_reindexObject_call(self, *args, **kw):
      if self.getRelativeUrl() in (instance2.getRelativeUrl(),
                                   instance3.getRelativeUrl()):
        self.portal_workflow.doActionFor(instance1, action='edit_action',
          comment='reindexObject triggered')
      else:
        return self.reindexObject_call(*args, **kw)

    # Replace activeSense by a dummy method
    from Products.ERP5Type.Base import Base
    Base.reindexObject_call = Base._reindexObject
    Base._reindexObject = verify_reindexObject_call
    try:
      instance1.edit(successor_value=instance3)
      self.tic()
    finally:
      Base._reindexObject = Base.reindexObject_call
    self.assertEqual(
        'reindexObject triggered',
        instance1.workflow_history['edit_workflow'][-1]['comment'])
    self.assertEqual(
        'reindexObject triggered',
        instance1.workflow_history['edit_workflow'][-2]['comment'])
    self.assertEqual(
        None,
        instance1.workflow_history['edit_workflow'][-3]['comment'])
