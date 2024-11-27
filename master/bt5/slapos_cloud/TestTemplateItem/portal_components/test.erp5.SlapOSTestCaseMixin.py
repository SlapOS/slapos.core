# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2018 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################
from Products.SlapOS.tests.testSlapOSMixin import \
  testSlapOSMixin

from DateTime import DateTime
from Products.ERP5Type.tests.utils import createZODBPythonScript
import transaction
import functools
from functools import wraps
from zLOG import LOG, INFO

def changeSkin(skin_name):
  def decorator(func):
    def wrapped(self, *args, **kwargs):
      default_skin = self.portal.portal_skins.default_skin
      self.portal.portal_skins.changeSkin(skin_name)
      self.app.REQUEST.set('portal_skin', skin_name)
      try:
        v = func(self, *args, **kwargs)
      finally:
        self.portal.portal_skins.changeSkin(default_skin)
        self.app.REQUEST.set('portal_skin', default_skin)
      return v
    return wrapped
  return decorator

def simulate(script_id, params_string, code_string):
  def upperWrap(f):
    @wraps(f)
    def decorated(self, *args, **kw):
      if script_id in self.portal.portal_skins.custom.objectIds():
        raise ValueError('Precondition failed: %s exists in custom' % script_id)
      createZODBPythonScript(self.portal.portal_skins.custom,
                          script_id, params_string, code_string)
      transaction.commit()
      try:
        result = f(self, *args, **kw)
      finally:
        if script_id in self.portal.portal_skins.custom.objectIds():
          self.portal.portal_skins.custom.manage_delObjects(script_id)
        transaction.commit()
      return result
    return decorated
  return upperWrap

def withAbort(func):
  @functools.wraps(func)
  def wrapped(self, *args, **kwargs):
    try:
      func(self, *args, **kwargs)
    finally:
      self.abort()
  return wrapped

def ensureConsistency(func):
  @functools.wraps(func)
  def wrapped(self, *args, **kwargs):
    document = func(self, *args, **kwargs)
    consistency_list = document.checkConsistency()
    assert not len(consistency_list), consistency_list
    return document

  return wrapped

class TemporaryAlarmScript(object):
  """
  Context manager for temporary alarm python scripts
  """
  def __init__(self, portal, script_name, fake_return="", attribute=None):
    self.script_name = script_name
    self.portal = portal
    self.fake_return = fake_return
    self.attribute = attribute

  def __enter__(self):
    if self.script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % self.script_name)
    if self.attribute is None:
      content = """portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by %s')
return %s""" % (self.script_name, self.fake_return)
    else:
      content = """portal_workflow = context.portal_workflow
context.edit(%s='Visited by %s')
return %s""" % (self.attribute, self.script_name, self.fake_return)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        self.script_name,
                        '*args, **kwargs',
                        '# Script body\n' + content)
    transaction.commit()

  def __exit__(self, exc_type, exc_value, traceback):
    if self.script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(self.script_name)
    transaction.commit()


class PinnedDateTime(object):
  """
  Context manager for changing the zope date
  """
  def __init__(self, testinstance, datetime):
    self.datetime = datetime
    self.testinstance = testinstance

  def __enter__(self):
    self.testinstance.pinDateTime(self.datetime)

  def __exit__(self, *args, **kw):
    self.testinstance.unpinDateTime()


class SlapOSTestCaseMixin(testSlapOSMixin):

  expected_html_payzen_redirect_page = None
  
  # Define few expected defaults
  expected_invoice_en_notification_message = 'A new invoice has been generated'

  # W/o notification messages the default is send message in english
  expected_invoice_zh_notification_message = 'A new invoice has been generated'

  # Allow customize extra bt5 and modules available on the deployed setup
  _custom_expected_module_list = []
  _custom_additional_bt5_list = []

  # Used by testSlapOSERP5GroupRoleSecurity.TestSlapOSGroupRoleSecurityCoverage for
  # search classes for assert overage
  security_group_role_test_id_list = ['test.erp5.testSlapOSERP5GroupRoleSecurity']

  def afterSetUp(self):
    testSlapOSMixin.afterSetUp(self)
    self.changeSkin('View')
    self.portal.portal_activities.unsubscribe()
    self.new_id = self.generateNewId()

  def beforeDumpExpectedConfiguration(self):
    """Overwrite this function on project context to tweak production focus tests"""
    pass

  def cleanUpRequest(self):
    """ set None some values that can cause problems in tests
    """
    for key in self.portal.REQUEST.keys():
      if key.endswith("_inProgress"):
        # Reset values set on script_ComputeNode_requestSoftwareReleaseChange
        self.portal.REQUEST.set(key, None)

  @ensureConsistency
  def _addAssignment(self, person, function, project=None, **kw):
    assignment = person.newContent(
      portal_type='Assignment',
      destination_project_value=project,
      function=function,
      **kw
    )
    assignment.open()
    return assignment

  def addAccountingManagerAssignment(self, person):
    # group is mandatory for accountant
    return self._addAssignment(person, 'accounting/manager', group='company')

  def addAccountingAgentAssignment(self, person):
    # group is mandatory for accountant
    return self._addAssignment(person, 'accounting/agent', group='company')

  def addSaleManagerAssignment(self, person):
    return self._addAssignment(person, 'sale/manager')

  def addSaleAgentAssignment(self, person):
    return self._addAssignment(person, 'sale/agent')

  def addProjectProductionAgentAssignment(self, person, project):
    return self._addAssignment(person, 'production/agent', project)

  def addProjectProductionManagerAssignment(self, person, project):
    return self._addAssignment(person, 'production/manager', project)

  def addProjectCustomerAssignment(self, person, project):
    return self._addAssignment(person, 'customer', project)

  def addProject(self, organisation=None, currency=None, person=None, is_accountable=False):
    assert organisation is None
    if person is None:
      assert not is_accountable
      project = self.portal.project_module.newContent(
        portal_type='Project',
        title='project-%s' % self.generateNewId()
      )
      project.validate()
      return project

    currency_relative_url = None
    if currency is not None:
      currency_relative_url = currency.getRelativeUrl()

    # Action to submit project subscription
    return person.Person_addVirtualMaster(
      'project-%s' % self.generateNewId(),
      is_accountable,
      is_accountable,
      currency_relative_url,
      batch=1).getRelativeUrl()
    """
    service = self.portal.restrictedTraverse('service_module/slapos_virtual_master_subscription')
    subscription_request = service.Resource_createSubscriptionRequest(person, None, None)
    self.tic()

    self.logout()

    return subscription_request.getAggregate()"""

  @ensureConsistency
  def _addERP5Login(self, document, **kw):
    if document.getPortalType() != "Person":
      raise ValueError("Only Person supports add ERP5 Login")

    login = document.newContent(
        portal_type="ERP5 Login",
        reference=document.getReference(),
        **kw)

    for _ in range(5):
      try:
        login.setPassword(document.Person_generatePassword())
        break
      except ValueError:
        # Skip the generated password wasnt acceptable let it try again.
        LOG("SlapOSTextCaseMixin._addERP5Login", INFO, "Set password failed, try few more times")
    login.validate()
    return login

  def _addCertificateLogin(self, document, **kw):
    login = document.newContent(
        portal_type="Certificate Login",
        reference=document.getReference(),
        **kw)
    login.validate()
    return login


  def makePerson(self, project, new_id=None, index=True, user=True):
    if new_id is None:
      new_id = self.generateNewId()
    # Clone person document
    person_user = self.portal.person_module\
                                 .newContent(portal_type="Person")
    person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
      default_email_text="live_test_%s@example.org" % new_id,
    )

    person_user.validate()
    self.addProjectCustomerAssignment(person_user, project)

    if user:
      login = self._addERP5Login(person_user)

    if index:
      transaction.commit()
      person_user.immediateReindexObject()
      if user:
        login.immediateReindexObject()

    return person_user

  def addInstanceTree(self, project=None, person=None, shared=False):
    # XXX supposed to replace _makeTree
    if project is None:
      project = self.addProject()
      self.tic()

    new_id = self.generateNewId()

    if person is None:
      person = self.makePerson(project, new_id=new_id, index=False)
    person_user = person

    request_kw = dict(
      software_release=self.generateNewSoftwareReleaseUrl(),
      software_title=self.generateNewSoftwareTitle(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateEmptyXml(),
      shared=shared,
      state="started",
      project_reference=project.getReference()
    )
 
    # As the software url does not match any service, and any trade condition
    # no instance is automatically created.
    # except if we fake Item_getSubscriptionStatus
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      person_user.requestSoftwareInstance(**request_kw)
    return person_user.REQUEST.get('request_instance_tree')

  def _makeTree(self, project):
    new_id = self.generateNewId()

    self.request_kw = dict(
        software_release=self.generateNewSoftwareReleaseUrl(),
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateEmptyXml(),
        shared=False,
        state="started",
        project_reference=project.getReference()
    )

    self.person_user = self.makePerson(project, new_id=new_id, index=False)
    self.commit()
    # prepare part of tree
    self.instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    self.software_instance = self.portal.software_instance_module\
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
        destination_section_value=self.person_user,
        follow_up_value=project
    )
    self.instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(self.instance_tree, 'start_requested')

    self.requested_software_instance = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    self.software_instance.edit(
        title=self.request_kw['software_title'],
        reference="TESTSI-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=self.instance_tree.getRelativeUrl(),
        successor=self.requested_software_instance.getRelativeUrl(),
        follow_up_value=project,
        ssl_key='foo',
        ssl_certificate='bar'
    )
    self.portal.portal_workflow._jumpToStateFor(self.software_instance, 'start_requested')
    self.software_instance.validate()

    self.requested_software_instance.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=self.instance_tree.getRelativeUrl(),
        follow_up_value=project,
        ssl_key='foo',
        ssl_certificate='bar'
    )
    self.portal.portal_workflow._jumpToStateFor(self.requested_software_instance, 'start_requested')
    self.requested_software_instance.validate()
    self.tic()

  def addComputeNodeAndPartition(self, project=None,
                                 portal_type='Compute Node'):
    # XXX replace _makeComputeNode
    if project is None:
      project = self.addProject()
      self.tic()

    edit_kw = {}
    if portal_type == 'Remote Node':
      # Be nice, and create remote user/project
      remote_project = self.addProject()
      remote_user = self.makePerson(remote_project)
      edit_kw['destination_project_value'] = remote_project
      edit_kw['destination_section_value'] = remote_user

    reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module.newContent(
      portal_type=portal_type,
      #allocation_scope=allocation_scope,
      reference=reference,
      title=reference,
      follow_up_value=project,
      **edit_kw
    )
    # The edit above will update capacity scope due the interaction workflow
    # The line above force capacity scope to be open, keeping the previous
    # behaviour.
    compute_node.edit(capacity_scope='open')
    compute_node.validate()

    reference = 'TESTPART-%s' % self.generateNewId()
    partition = compute_node.newContent(
      portal_type='Compute Partition',
      reference=reference,
      title=reference
    )
    partition.markFree()
    partition.validate()

    return compute_node, partition

  def _makeComputeNode(self, project, allocation_scope='open'):
    self.compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    reference = 'TESTCOMP-%s' % self.generateNewId()
    self.compute_node.edit(
      allocation_scope=allocation_scope,
      reference=reference,
      title=reference,
      follow_up_value=project
    )
    # The edit above will update capacity scope due the interaction workflow
    # The line above force capacity scope to be open, keeping the previous
    # behaviour.
    self.compute_node.edit(capacity_scope='open')
    self.compute_node.validate()
    reference = 'TESTPART-%s' % self.generateNewId()
    self.partition = self.compute_node.newContent(portal_type='Compute Partition',
      reference=reference,
      title=reference
    )
    self.partition.markFree()
    self.partition.validate()
    self.tic()

    return self.compute_node, self.partition

  def _makeComputerNetwork(self):
    reference = 'TESTCOMPNETWORK-%s' % self.generateNewId()
    self.computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        reference=reference,
        title=reference
    )
    self.computer_network.validate()
    self.tic()
    return self.computer_network

  def _makeComplexComputeNode(self, project, person=None, with_slave=False):
    for i in range(1, 5):
      id_ = 'partition%s' % i
      p = self.compute_node.newContent(portal_type='Compute Partition',
        id=id_,
        title=id_,
        reference=id_,
        default_network_address_ip_address='ip_address_%s' % i,
        default_network_address_netmask='netmask_%s' % i)
      p.markFree()
      p.validate()

    self.start_requested_software_installation = self.portal.software_installation_module\
        .newContent(portal_type="Software Installation")
    self.start_requested_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.compute_node.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Start requested for %s' % self.compute_node.getTitle(),
        follow_up_value=project
    )
    self.start_requested_software_installation.validate()
    self.start_requested_software_installation.requestStart()

    self.destroy_requested_software_installation = self.portal.software_installation_module\
        .newContent(portal_type="Software Installation")
    self.destroy_requested_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.compute_node.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Destroy requested for %s' % self.compute_node.getTitle(),
        follow_up_value=project
    )
    self.destroy_requested_software_installation.validate()
    self.destroy_requested_software_installation.requestStart()
    self.destroy_requested_software_installation.requestDestroy()

    self.destroyed_software_installation = self.portal.software_installation_module\
        .newContent(portal_type="Software Installation")
    self.destroyed_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.compute_node.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Destroyed for %s' % self.compute_node.getTitle(),
        follow_up_value=project
    )
    self.destroyed_software_installation.validate()
    self.destroyed_software_installation.requestStart()
    self.destroyed_software_installation.requestDestroy()
    self.destroyed_software_installation.invalidate()

    self.compute_node.partition1.markBusy()
    self.compute_node.partition2.markBusy()
    self.compute_node.partition3.markBusy()

    # prepare some trees
    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        destination_section_value=person,
        follow_up_value=project
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started',
      project_reference=project.getReference()
    )
    instance_tree.requestStart(**kw)
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.requestInstance(**kw)

    self.start_requested_software_instance = instance_tree.getSuccessorValue()
    self.start_requested_software_instance.edit(aggregate=self.compute_node.partition1.getRelativeUrl())

    if with_slave:
      instance_tree = self.portal.instance_tree_module\
          .newContent(portal_type="Instance Tree")
      instance_tree.validate()
      instance_tree.edit(
          title=self.generateNewSoftwareTitle(),
          reference="TESTSI-%s" % self.generateNewId(),
          destination_section_value=person,
          follow_up_value=project
      )
      slave_kw = dict(
        software_release=kw['software_release'],
        software_type=kw['software_type'],
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        shared=True,
        software_title=instance_tree.getTitle(),
        state='started',
        project_reference=project.getReference()
      )
      instance_tree.requestStart(**slave_kw)
      with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
        instance_tree.requestInstance(**slave_kw)

      self.start_requested_slave_instance = instance_tree.getSuccessorValue()
      self.start_requested_slave_instance.edit(aggregate=self.compute_node.partition1.getRelativeUrl())

    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        destination_section_value=person,
        follow_up_value=project
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='stopped',
      project_reference=project.getReference()
    )
    instance_tree.requestStop(**kw)
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.requestInstance(**kw)

    self.stop_requested_software_instance = instance_tree.getSuccessorValue()
    self.stop_requested_software_instance.edit(
        aggregate=self.compute_node.partition2.getRelativeUrl()
    )

    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        follow_up_value=project
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='stopped',
      project_reference=project.getReference()
    )
    instance_tree.requestStop(**kw)
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.requestInstance(**kw)

    kw['state'] = 'destroyed'
    instance_tree.requestDestroy(**kw)

    self.destroy_requested_software_instance = instance_tree.getSuccessorValue()
    self.destroy_requested_software_instance.requestDestroy(**kw)
    self.destroy_requested_software_instance.edit(
        aggregate=self.compute_node.partition3.getRelativeUrl()
    )

    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        follow_up_value=project
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='stopped',
      project_reference=project.getReference()
    )
    instance_tree.requestStop(**kw)
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.requestInstance(**kw)

    kw['state'] = 'destroyed'
    instance_tree.requestDestroy(**kw)

    self.destroyed_software_instance = instance_tree.getSuccessorValue()
    self.destroyed_software_instance.edit(
        aggregate=self.compute_node.partition4.getRelativeUrl()
    )
    self.destroyed_software_instance.requestDestroy(**kw)
    # Do not invalidate, as it will unlink the partition
    #self.destroyed_software_instance.invalidate()

    self.tic()
    if with_slave:
      # as slave is created in non usual way update its local roles
      self.start_requested_slave_instance.updateLocalRolesOnSecurityGroups()
      self.tic()
    self._cleaupREQUEST()

  def _makeSoftwareProduct(self, project, new_id=None, url=None, software_type='foobar'):
    if new_id is None:
      new_id = self.generateNewId()
    if url is None:
      url = self.generateNewSoftwareReleaseUrl()
    software_product = self.portal.software_product_module.newContent(
      reference='TESTSOFTPROD-%s' % new_id,
      title='Test software product %s' % new_id,
      follow_up_value=project
    )
    software_product.newContent(
      portal_type='Software Product Release Variation',
      url_string=url
    )
    software_product.newContent(
      portal_type='Software Product Type Variation',
      reference=software_type
    )
    software_product.publish()
    return software_product

  def _makeSoftwareRelease(self, software_product, url=None):
    if url is None:
      url = self.generateNewSoftwareReleaseUrl()
    return software_product.newContent(
      portal_type='Software Product Release Variation',
      url_string=url,
    )

  def _makeSoftwareType(self, software_product):
    return software_product.newContent(
      portal_type='Software Product Type Variation',
      url_string='type%s' % self.generateNewId(),
    )

  @simulate('Item_getSubscriptionStatus', '*args, **kwargs', 'return "subscribed"')
  def bootstrapAllocableInstanceTree(self, allocation_state='possible', shared=False, node="compute",
                                     is_accountable=False, base_price=None, has_organisation=False):
    if allocation_state not in ('impossible', 'possible', 'allocated'):
      raise ValueError('Not supported allocation_state: %s' % allocation_state)
    project = self.addProject(
      #is_accountable=is_accountable
    )
    person = self.makePerson(project)
    person.edit(
      # required to calculate the vat
      default_address_region='europe/west/france'
    )
    if has_organisation:
      organisation = self.portal.organisation_module.newContent(
        portal_type="Organisation",
        title="customer-seller-%s" % self.generateNewId()
      )
      organisation.validate()
      person.edit(career_subordination_value=organisation)
    software_product = self._makeSoftwareProduct(project)
    release_variation = software_product.contentValues(portal_type='Software Product Release Variation')[0]
    type_variation = software_product.contentValues(portal_type='Software Product Type Variation')[0]

    if is_accountable:
      currency = self.portal.currency_module.newContent(
        portal_type="Currency",
        title="test %s" % self.generateNewId()
      )
      currency.validate()
      seller_organisation = self.portal.organisation_module.newContent(
        portal_type="Organisation",
        title="seller-%s" % self.generateNewId(),
        # required to generate accounting report
        price_currency_value=currency,
        # required to calculate the vat
        default_address_region='europe/west/france'
      )
      seller_bank_account = seller_organisation.newContent(
        portal_type="Bank Account",
        title="test_bank_account_%s" % self.generateNewId(),
        price_currency_value=currency
      )
      seller_bank_account.validate()
      seller_organisation.validate()
      sale_trade_condition = self.portal.sale_trade_condition_module.newContent(
        portal_type="Sale Trade Condition",
        trade_condition_type="instance_tree",
        source_section_value=seller_organisation,
        source_project_value=project,
        price_currency_value=currency,
        specialise="business_process_module/slapos_sale_subscription_business_process"
      )
      sale_trade_condition.validate()
      if (base_price is not None):
        sale_supply = self.portal.sale_supply_module.newContent(
          portal_type="Sale Supply",
          destination_project_value=project,
          price_currency_value=currency
        )
        sale_supply.newContent(
          portal_type="Sale Supply Line",
          base_price=base_price,
          resource_value=software_product
        )
        sale_supply.validate()

    self.tic()
    partition = None
    if node == "compute":
      person.requestComputeNode(compute_node_title='test compute node',
                                project_reference=project.getReference())
      self.tic()
      compute_node = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node',
        reference=self.portal.REQUEST.get('compute_node_reference')
      )
      assert compute_node is not None
      # The edit above will update capacity scope due the interaction workflow
      # The line above force capacity scope to be open, keeping the previous
      # behaviour.
      compute_node.edit(capacity_scope='open')
    elif node == "remote":
      remote_project = self.addProject(is_accountable=False)
      compute_node = self.portal.compute_node_module.newContent(
        portal_type="Remote Node",
        follow_up_value=project,
        destination_project_value=remote_project,
        destination_section_value=person
      )
    elif node == "instance":
      compute_node = self.portal.compute_node_module.newContent(
        portal_type="Instance Node",
        follow_up_value=project
      )
    else:
      raise ValueError("Unsupported node value: %s" % node)

    request_kw = dict(
      software_release=release_variation.getUrlString(),
      software_type=type_variation.getTitle(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateEmptyXml(),
      shared=shared,
      software_title='test tree',
      state='started',
      project_reference=project.getReference()
    )
    person.requestSoftwareInstance(**request_kw)
    instance_tree = self.portal.REQUEST.get('request_instance_tree')

    if allocation_state in ('possible', 'allocated'):
      if (node == "instance") and (shared):
        real_compute_node = self.portal.compute_node_module.newContent(
          portal_type="Compute Node",
          follow_up_value=project,
          reference='TEST-%s' % self.generateNewId(),
          allocation_scope="open",
          capacity_scope='open'
        )
        # The edit above will update capacity scope due the interaction workflow
        # The line above force capacity scope to be open, keeping the previous
        # behaviour.
        real_compute_node.edit(capacity_scope='open')
        real_compute_node.validate()
        partition = real_compute_node.newContent(
          portal_type='Compute Partition',
          reference='reference%s' % self.generateNewId()
        )
        node_instance_tree = self.portal.instance_tree_module.newContent(
          title='TEST-%s' % self.generateNewId(),
        )
        software_instance = self.portal.software_instance_module.newContent(
          portal_type="Software Instance",
          follow_up_value=project,
          specialise_value=node_instance_tree,
          url_string=release_variation.getUrlString(),
          title='TEST-%s' % self.generateNewId(),
          reference='TEST-%s' % self.generateNewId(),
          source_reference='TEST-%s' % self.generateNewId(),
          destination_reference='TEST-%s' % self.generateNewId(),
          ssl_certificate='TEST-%s' % self.generateNewId(),
          ssl_key='TEST-%s' % self.generateNewId(),
        )
        self.tic()
        compute_node.edit(specialise_value=software_instance)
        software_instance.edit(aggregate_value=partition)
        self.portal.portal_workflow._jumpToStateFor(software_instance, 'start_requested')
        self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
        partition.validate()
        partition.markFree()
        partition.markBusy()
      elif (node == "instance") and (not shared):
        raise NotImplementedError('can not allocate on instance node')
      else:
        partition = compute_node.newContent(
          portal_type='Compute Partition',
          reference='reference%s' % self.generateNewId()
        )

        partition.validate()
        partition.markFree()

    #compute_node.validate()

    if allocation_state == 'allocated':
      instance = instance_tree.getSuccessorValue()
      instance.edit(aggregate_value=partition)
      if not ((node == "instance") and (shared)):
        partition.markBusy()

    # create fake open order, to bypass Service_getSubscriptionStatus
    subscrible_item_list = [instance_tree]
    if partition is not None:
      subscrible_item_list.append(partition.getParentValue())
    for item in subscrible_item_list:
      open_order = self.portal.open_sale_order_module.newContent(
        portal_type="Open Sale Order",
        ledger="automated",
        destination_section_value=person
      )
      open_order.newContent(
        aggregate_value=item
      )
      self.portal.portal_workflow._jumpToStateFor(open_order, 'validated')

    self.tic()
    return software_product, release_variation, type_variation, compute_node, partition, instance_tree

  def addAllocationSupply(self, title, node, software_product,
                          software_release, software_type,
                          destination_value=None,
                          is_slave_on_same_instance_tree_allocable=False,
                          disable_alarm=False):
    allocation_supply = self.portal.allocation_supply_module.newContent(
      portal_type="Allocation Supply",
      title=title,
      aggregate_value=node,
      destination_value=destination_value,
      destination_project_value=software_product.getFollowUpValue(),
      slave_on_same_instance_tree_allocable=is_slave_on_same_instance_tree_allocable
    )
    resource_vcl = [
      'software_release/%s' % software_release.getRelativeUrl(),
      'software_type/%s' % software_type.getRelativeUrl()
    ]
    resource_vcl.sort()
    allocation_supply_line = allocation_supply.newContent(
      portal_type="Allocation Supply Line",
      resource_value=software_product,
    )
    allocation_supply_line.edit(
      p_variation_base_category_list=allocation_supply_line.getVariationRangeBaseCategoryList()
    )
    base_id = 'path'
    allocation_supply_line.setCellRange(
      base_id=base_id,
      *allocation_supply_line.SupplyLine_asCellRange(base_id=base_id)
    )
    #cell_key = list(allocation_supply_line.getCellKeyList(base_id=base_id))[0]
    cell_key = resource_vcl
    allocation_supply_cell = allocation_supply_line.newCell(
      base_id=base_id,
      portal_type='Allocation Supply Cell',
      *cell_key
    )
    allocation_supply_cell.edit(
      mapped_value_property_list=['allocable'],
      allocable=True,
      predicate_category_list=cell_key,
      variation_category_list=cell_key
    )
    if disable_alarm:
      # disable generation of Upgrade Decision
      with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
        allocation_supply.validate()
    else:
      allocation_supply.validate()
    return allocation_supply

  def generateNewSoftwareReleaseUrl(self):
    return 'http://example.org/têst%s.cfg' % self.generateNewId()

  def generateNewSoftwareType(self):
    return 'Type ë@î %s' % self.generateNewId()

  def generateNewSoftwareTitle(self):
    return 'Title é#ï %s' % self.generateNewId()

  def generateSafeXml(self):
    return '<?xml version="1.0" encoding="utf-8"?><instance><parameter '\
      'id="paramé">%s</parameter></instance>' % self.generateNewId()

  def generateEmptyXml(self):
    return '<?xml version="1.0" encoding="utf-8"?><instance></instance>'

  def _cleaupREQUEST(self):
    self.portal.REQUEST['request_instance'] = None
    self.portal.REQUEST.headers = {}

  def generateNewId(self):
    return "%sö" % self.portal.portal_ids.generateNewId(
        id_group=('slapos_core_test'))

  def createPaymentTransaction(self):
    new_id = self.generateNewId()
    return self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      )

  def createSaleInvoiceTransaction(self, **kw):
    new_id = self.generateNewId()
    return self.portal.accounting_module.newContent(
      portal_type='Sale Invoice Transaction',
      title="Invoice %s" % new_id,
      reference="TESTSIT-%s" % new_id,
      **kw)

  def createPayzenEvent(self):
    return self.portal.system_event_module.newContent(
        portal_type='Payzen Event',
        reference='PAY-%s' % self.generateNewId())

  def createWechatEvent(self):
    return self.portal.system_event_module.newContent(
        portal_type='Wechat Event',
        reference='PAY-%s' % self.generateNewId())

  def createStoppedSaleInvoiceTransaction(self, destination_section_value=None,
                                          destination_project_value=None,
                                          price=2, payment_mode="payzen"):
    new_source_reference = self.generateNewId()
    new_destination_reference = self.generateNewId()
    invoice = self.createSaleInvoiceTransaction(
      start_date=DateTime(),
      source_reference=new_source_reference,
      destination_reference=new_destination_reference,
      destination_value=destination_section_value,
      destination_section_value=destination_section_value,
      destination_project_value=destination_project_value,
      payment_mode=payment_mode,
      ledger="automated",
      #specialise="sale_trade_condition_module/XXX",
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(invoice, 'stopped')
    invoice.newContent(
      title="",
      portal_type="Invoice Line",
      quantity=-2,
      price=price,
    )
    invoice.newContent(
      portal_type="Sale Invoice Transaction Line",
      source="account_module/receivable",
      quantity=-3,
    )
    return invoice

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      resource='foo/bar',
      )

  def _test_alarm(self, alarm, document, script_name, attribute=None):
    self.tic()
    with TemporaryAlarmScript(self.portal, script_name, attribute=attribute):
      alarm.activeSense()
      self.tic()
    if attribute is None:
      content = document.workflow_history['edit_workflow'][-1]['comment']
    else:
      content = document.getProperty(attribute)
    self.assertEqual(
        'Visited by %s' % script_name,
        content)

  def _test_alarm_not_visited(self, alarm, document, script_name, attribute=None):
    self.tic()
    with TemporaryAlarmScript(self.portal, script_name, attribute=attribute):
      alarm.activeSense()
      self.tic()
    if attribute is None:
      content = document.workflow_history['edit_workflow'][-1]['comment']
    else:
      content = document.getProperty(attribute)
    self.assertNotEqual(
        'Visited by %s' % script_name,
        content)


class SlapOSTestCaseMixinWithAbort(SlapOSTestCaseMixin):
  abort_transaction = 1
