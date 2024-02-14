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


class TemporaryAlarmScript(object):
  """
  Context manager for temporary python scripts
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


class SlapOSTestCaseMixin(testSlapOSMixin):

  expected_html_payzen_redirect_page = None
  
  # Define few expected defaults
  expected_invoice_en_notification_message = 'A new invoice has been generated'

  # W/o notification messages the default is send message in english
  expected_invoice_zh_notification_message = 'A new invoice has been generated'

  # Allow customize extra bt5 and modules available on the deployed setup
  _custom_expected_module_list = []
  _custom_additional_bt5_list = []

  # Expected organisation when generate invoices, tickets, etc...
  expected_slapos_organisation = "organisation_module/slapos"
  expected_zh_slapos_organisation = "organisation_module/slapos"

  # Used by testSlapOSERP5GroupRoleSecurity.TestSlapOSGroupRoleSecurityCoverage for
  # searh classes for assert overage
  security_group_role_test_id_list = ['test.erp5.testSlapOSERP5GroupRoleSecurity']


  def afterSetUp(self):
    testSlapOSMixin.afterSetUp(self)
    self.changeSkin('View')
    self.portal.portal_activities.unsubscribe()
    self.new_id = self.generateNewId()
    
    # Define default Organisation
    self.slapos_organisation = self.portal.restrictedTraverse(
      self.expected_slapos_organisation
    )

    instance_template = self.portal.software_instance_module.template_software_instance		 
    if len(instance_template.objectValues()):
      instance_template.manage_delObjects(		 
        ids=[i.getId() for i in instance_template.objectValues()])


  def beforeDumpExpectedConfiguration(self):
    """Overwrite this function on project context to tweak production focus tests"""
    pass

  def makeCustomOrganisation(self, new_id=None, index=True,
          price_currency="currency_module/EUR"):
    # Create a custom organisation same as slapos, for ensure we can have
    # multiple organisations working on the site

    if new_id is None:
      new_id = self.generateNewId()
    
    custom_organisation = self.portal.organisation_module.slapos.\
                                 Base_createCloneDocument(batch_mode=1)
    custom_organisation.edit(
      title="organisation_live_test_%s" % new_id,
      reference="organisation_live_test_%s" % new_id,
      default_email_text="organisation_live_test_%s@example.org" % new_id,
    )

    custom_organisation.validate()

    self.assertEqual(custom_organisation.getGroup(),
                      "company")

    self.assertEqual("currency_module/EUR",
                     custom_organisation.getPriceCurrency())

    custom_organisation.setPriceCurrency(price_currency)
    self.assertNotEqual(getattr(custom_organisation, "bank_account", None), None)

    if index:
      custom_organisation.updateLocalRolesOnSecurityGroups()
      custom_organisation.bank_account.updateLocalRolesOnSecurityGroups()
  
      transaction.commit()
      custom_organisation.immediateReindexObject()
      
    return custom_organisation

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

  def makePerson(self, new_id=None, index=True, user=True):
    if new_id is None:
      new_id = self.generateNewId()
    # Clone person document
    person_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)
    person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
      default_email_text="live_test_%s@example.org" % new_id,
    )

    person_user.validate()
    for assignment in person_user.contentValues(portal_type="Assignment"):
      assignment.open()


    if user:
      login = self._addERP5Login(person_user)

    if index:
      transaction.commit()
      person_user.immediateReindexObject()
      if user:
        login.immediateReindexObject()

    return person_user

  def _makeTree(self, requested_template_id='template_software_instance'):
    new_id = self.generateNewId()

    self.request_kw = dict(
        software_release=self.generateNewSoftwareReleaseUrl(),
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateEmptyXml(),
        shared=False,
        state="started"
    )

    self.person_user = self.makePerson(new_id=new_id, index=False)
    self.commit()
    # prepare part of tree
    self.instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    self.software_instance = self.portal.software_instance_module\
        [requested_template_id].Base_createCloneDocument(batch_mode=1)

    self.instance_tree.edit(
        title=self.request_kw['software_title'],
        reference="TESTHS-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        root_slave=self.request_kw['shared'],
        successor=self.software_instance.getRelativeUrl(),
        destination_section=self.person_user.getRelativeUrl()
    )
    self.instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(self.instance_tree, 'start_requested')

    self.requested_software_instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    self.software_instance.edit(
        title=self.request_kw['software_title'],
        reference="TESTSI-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=self.instance_tree.getRelativeUrl(),
        successor=self.requested_software_instance.getRelativeUrl()
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
    )
    self.portal.portal_workflow._jumpToStateFor(self.requested_software_instance, 'start_requested')
    self.requested_software_instance.validate()
    self.tic()

  def _makeSlaveTree(self, requested_template_id='template_slave_instance'):
    return self._makeTree(requested_template_id=requested_template_id)

  def _makeComputeNode(self, owner=None, allocation_scope='open/public'):
    self.compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    reference = 'TESTCOMP-%s' % self.generateNewId()
    self.compute_node.edit(
        allocation_scope=allocation_scope,
        reference=reference,
        title=reference
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

    if owner is not None:
      self.compute_node.edit(
        source_administration_value=owner,
      )

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

  def _makeComplexComputeNode(self, person=None, with_slave=False):
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
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    self.start_requested_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.compute_node.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Start requested for %s' % self.compute_node.getTitle()
    )
    self.start_requested_software_installation.validate()
    self.start_requested_software_installation.requestStart()

    self.destroy_requested_software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    self.destroy_requested_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.compute_node.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Destroy requested for %s' % self.compute_node.getTitle()
    )
    self.destroy_requested_software_installation.validate()
    self.destroy_requested_software_installation.requestStart()
    self.destroy_requested_software_installation.requestDestroy()

    self.destroyed_software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    self.destroyed_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.compute_node.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Destroyed for %s' % self.compute_node.getTitle()
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
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        destination_section_value=person,
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**kw)
    instance_tree.requestInstance(**kw)

    self.start_requested_software_instance = instance_tree.getSuccessorValue()
    self.start_requested_software_instance.edit(aggregate=self.compute_node.partition1.getRelativeUrl())

    if with_slave:
      instance_tree = self.portal.instance_tree_module\
          .template_instance_tree.Base_createCloneDocument(batch_mode=1)
      instance_tree.validate()
      instance_tree.edit(
          title=self.generateNewSoftwareTitle(),
          reference="TESTSI-%s" % self.generateNewId(),
          destination_section_value=person,
      )
      slave_kw = dict(
        software_release=kw['software_release'],
        software_type=kw['software_type'],
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        shared=True,
        software_title=instance_tree.getTitle(),
        state='started'
      )
      instance_tree.requestStart(**slave_kw)
      instance_tree.requestInstance(**slave_kw)

      self.start_requested_slave_instance = instance_tree.getSuccessorValue()
      self.start_requested_slave_instance.edit(aggregate=self.compute_node.partition1.getRelativeUrl())

    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        destination_section_value=person,
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='stopped'
    )
    instance_tree.requestStop(**kw)
    instance_tree.requestInstance(**kw)

    self.stop_requested_software_instance = instance_tree.getSuccessorValue()
    self.stop_requested_software_instance.edit(
        aggregate=self.compute_node.partition2.getRelativeUrl()
    )

    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='stopped'
    )
    instance_tree.requestStop(**kw)
    instance_tree.requestInstance(**kw)

    kw['state'] = 'destroyed'
    instance_tree.requestDestroy(**kw)

    self.destroy_requested_software_instance = instance_tree.getSuccessorValue()
    self.destroy_requested_software_instance.requestDestroy(**kw)
    self.destroy_requested_software_instance.edit(
        aggregate=self.compute_node.partition3.getRelativeUrl()
    )

    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='stopped'
    )
    instance_tree.requestStop(**kw)
    instance_tree.requestInstance(**kw)

    kw['state'] = 'destroyed'
    instance_tree.requestDestroy(**kw)

    self.destroyed_software_instance = instance_tree.getSuccessorValue()
    self.destroyed_software_instance.edit(
        aggregate=self.compute_node.partition4.getRelativeUrl()
    )
    self.destroyed_software_instance.requestDestroy(**kw)
    self.destroyed_software_instance.invalidate()

    self.tic()
    if with_slave:
      # as slave is created in non usual way update its local roles
      self.start_requested_slave_instance.updateLocalRolesOnSecurityGroups()
      self.tic()
    self._cleaupREQUEST()

  def _makeSoftwareProduct(self, new_id=None):
    if new_id is None:
      new_id = self.generateNewId()
    software_product = self.portal.software_product_module\
      .template_software_product.Base_createCloneDocument(batch_mode=1)
    software_product.edit(
      reference='TESTSOFTPROD-%s' % new_id,
      title='Test software product %s' % new_id
    )
    software_product.publish()
    return software_product

  def _makeSoftwareRelease(self, new_id=None):
    if new_id is None:
      new_id = self.generateNewId()

    software_release = self.portal.software_release_module\
      .template_software_release.Base_createCloneDocument(batch_mode=1)
    software_release.edit(
      url_string=self.generateNewSoftwareReleaseUrl(),
      reference='TESTSOFTRELS-%s' % new_id,
      title='Start requested for %s' % new_id
    )
    software_release.release()
    return software_release
  
  def _makeCustomSoftwareRelease(self, software_product_url, software_url):
    software_release = self._makeSoftwareRelease()
    software_release.edit(
        aggregate_value=software_product_url,
        url_string=software_url
    )
    software_release.publish()
    return software_release

  def generateNewSoftwareReleaseUrl(self):
    return 'http://example.org/têst%s.cfg' % self.generateNewId()

  def generateNewSoftwareType(self):
    return 'Type ë@î %s' % self.generateNewId()

  def generateNewSoftwareTitle(self):
    return 'Title é#ï %s' % self.generateNewId()

  def generateSafeXml(self):
    return '<?xml version="1.0" encoding="utf-8"?><instance><parameter '\
      'id="%s">%s</parameter></instance>' % \
      ("paramé".decode("UTF-8").encode("UTF-8"),
      self.generateNewId().decode("UTF-8").encode("UTF-8"))

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

  def createStoppedSaleInvoiceTransaction(self, destination_section=None, price=2, payment_mode="payzen"):
    new_source_reference = self.generateNewId()
    new_destination_reference = self.generateNewId()
    invoice = self.createSaleInvoiceTransaction(
      start_date=DateTime(),
      source_reference=new_source_reference,
      destination_reference=new_destination_reference,
      destination_section=destination_section,
      payment_mode=payment_mode,
      specialise="sale_trade_condition_module/slapos_aggregated_trade_condition",
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

  def restoreAccountingTemplatesOnPreferences(self):
    self.login()
    system_preference = self.portal.portal_preferences.slapos_default_system_preference
    system_preference.edit(
      preferred_aggregated_consumption_sale_trade_condition=\
        'sale_trade_condition_module/slapos_aggregated_consumption_trade_condition',
      preferred_aggregated_sale_trade_condition=\
        'sale_trade_condition_module/slapos_aggregated_trade_condition',
      preferred_aggregated_subscription_sale_trade_condition=\
        'sale_trade_condition_module/slapos_aggregated_subscription_trade_condition',
      preferred_default_pre_payment_template=\
        'accounting_module/slapos_pre_payment_template',
      preferred_instance_delivery_template=\
        'sale_packing_list_module/slapos_accounting_instance_delivery_template',
      preferred_open_sale_order_line_template=\
        'open_sale_order_module/slapos_accounting_open_sale_order_line_template/slapos_accounting_open_sale_order_line_template',
      preferred_open_sale_order_template=\
        'open_sale_order_module/slapos_accounting_open_sale_order_template',
      preferred_zh_pre_payment_template=\
        'accounting_module/slapos_wechat_pre_payment_template',
      preferred_zh_pre_payment_subscription_invoice_template=\
        'accounting_module/template_wechat_pre_payment_subscription_sale_invoice_transaction',
      preferred_default_pre_payment_subscription_invoice_template=\
        'accounting_module/template_pre_payment_subscription_sale_invoice_transaction'

    )
    self.tic()

  def redefineAccountingTemplatesonPreferences(self, price_currency="currency_module/EUR"):
    # Define a new set of templates and change organisation on them, in this way tests should
    # behave the same.
    self.login()
    organisation = self.makeCustomOrganisation(price_currency=price_currency)
    accounting_module = self.portal.accounting_module
    sale_packing_list_module = self.portal.sale_packing_list_module

    preferred_zh_pre_payment_template = \
      accounting_module.slapos_wechat_pre_payment_template.Base_createCloneDocument(batch_mode=1)
    preferred_zh_pre_payment_template.edit(
      source_section_value = organisation,
      source_payment_value=organisation.bank_account
    )
    
    preferred_default_pre_payment_template = \
      accounting_module.slapos_pre_payment_template.Base_createCloneDocument(batch_mode=1)
    preferred_default_pre_payment_template.edit(
      source_section_value = organisation,
      source_payment_value=organisation.bank_account
    )

    preferred_zh_pre_payment_subscription_invoice_template = \
      accounting_module.template_wechat_pre_payment_subscription_sale_invoice_transaction.Base_createCloneDocument(batch_mode=1)

    preferred_zh_pre_payment_subscription_invoice_template.edit(
      source_section_value = organisation,
      source_value=organisation
    )
    preferred_default_pre_payment_subscription_invoice_template = \
      accounting_module.template_pre_payment_subscription_sale_invoice_transaction.Base_createCloneDocument(batch_mode=1)
    
    preferred_default_pre_payment_subscription_invoice_template.edit(
      source_section_value = organisation,
      source_value=organisation
    )

    preferred_instance_delivery_template = \
      sale_packing_list_module.slapos_accounting_instance_delivery_template.Base_createCloneDocument(batch_mode=1)

    preferred_instance_delivery_template.edit(
      source_section_value = organisation,
      source_value=organisation
    )

    open_sale_order_module = self.portal.open_sale_order_module

    preferred_open_sale_order_template=\
        open_sale_order_module.slapos_accounting_open_sale_order_template.Base_createCloneDocument(batch_mode=1)

    preferred_open_sale_order_template.edit(
      source_section_value = organisation,
      source_value=organisation
    )

    system_preference = self.portal.portal_preferences.slapos_default_system_preference

    system_preference.edit(
      preferred_default_pre_payment_template=preferred_default_pre_payment_template.getRelativeUrl(),
      preferred_zh_pre_payment_template=preferred_zh_pre_payment_template.getRelativeUrl(),
      preferred_zh_pre_payment_subscription_invoice_template=\
        preferred_zh_pre_payment_subscription_invoice_template.getRelativeUrl(),
      preferred_default_pre_payment_subscription_invoice_template=\
        preferred_default_pre_payment_subscription_invoice_template.getRelativeUrl(),
      preferred_instance_delivery_template=\
        preferred_instance_delivery_template.getRelativeUrl(),
      preferred_open_sale_order_template=\
        preferred_open_sale_order_template.getRelativeUrl()
    )
    self.tic()

    return organisation

  def redefineAccountingTemplatesonPreferencesWithDualOrganisation(self):
    # Define a new set of templates and change organisation on them, in this way tests should
    # behave the same.
    self.login()
    fr_organisation = self.makeCustomOrganisation()
    zh_organisation = self.makeCustomOrganisation(
            price_currency="currency_module/CNY")

    # Update Price currency for Chinese company
    
    accounting_module = self.portal.accounting_module
    sale_packing_list_module = self.portal.sale_packing_list_module

    preferred_zh_pre_payment_template = \
      accounting_module.slapos_wechat_pre_payment_template.Base_createCloneDocument(batch_mode=1)
    preferred_zh_pre_payment_template.edit(
      source_section_value = zh_organisation,
      source_payment_value=zh_organisation.bank_account
    )
    
    preferred_default_pre_payment_template = \
      accounting_module.slapos_pre_payment_template.Base_createCloneDocument(batch_mode=1)
    preferred_default_pre_payment_template.edit(
      source_section_value = fr_organisation,
      source_payment_value=fr_organisation.bank_account
    )

    preferred_zh_pre_payment_subscription_invoice_template = \
      accounting_module.template_wechat_pre_payment_subscription_sale_invoice_transaction.Base_createCloneDocument(batch_mode=1)

    preferred_zh_pre_payment_subscription_invoice_template.edit(
      source_section_value = zh_organisation,
      source_value=zh_organisation
    )
    preferred_default_pre_payment_subscription_invoice_template = \
      accounting_module.template_pre_payment_subscription_sale_invoice_transaction.Base_createCloneDocument(batch_mode=1)
    
    preferred_default_pre_payment_subscription_invoice_template.edit(
      source_section_value=fr_organisation,
      source_value=fr_organisation
    )

    preferred_instance_delivery_template = \
      sale_packing_list_module.slapos_accounting_instance_delivery_template.Base_createCloneDocument(batch_mode=1)

    preferred_instance_delivery_template.edit(
      source_section_value=fr_organisation,
      source_value=fr_organisation
    )

    open_sale_order_module = self.portal.open_sale_order_module

    preferred_open_sale_order_template=\
        open_sale_order_module.slapos_accounting_open_sale_order_template.Base_createCloneDocument(batch_mode=1)

    preferred_open_sale_order_template.edit(
      source_section_value=fr_organisation,
      source_value=fr_organisation
    )

    system_preference = self.portal.portal_preferences.slapos_default_system_preference

    system_preference.edit(
      preferred_default_pre_payment_template=preferred_default_pre_payment_template.getRelativeUrl(),
      preferred_zh_pre_payment_template=preferred_zh_pre_payment_template.getRelativeUrl(),
      preferred_zh_pre_payment_subscription_invoice_template=\
        preferred_zh_pre_payment_subscription_invoice_template.getRelativeUrl(),
      preferred_default_pre_payment_subscription_invoice_template=\
        preferred_default_pre_payment_subscription_invoice_template.getRelativeUrl(),
      preferred_instance_delivery_template=\
        preferred_instance_delivery_template.getRelativeUrl(),
      preferred_open_sale_order_template=\
        preferred_open_sale_order_template.getRelativeUrl()
    )
    self.tic()

    return fr_organisation, zh_organisation


class SlapOSTestCaseMixinWithAbort(SlapOSTestCaseMixin):
  abort_transaction = 1
