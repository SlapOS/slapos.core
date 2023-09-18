# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
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

import six
import six.moves.urllib.parse
from erp5.component.test.testSlapOSCloudSecurityGroup import TestSlapOSSecurityMixin
from erp5.component.test.SlapOSTestCaseMixin import changeSkin
import re
import xml_marshaller
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager

class DefaultScenarioMixin(TestSlapOSSecurityMixin):

  launch_caucase = 1

  def afterSetUp(self):
    TestSlapOSSecurityMixin.afterSetUp(self)
    preference = self.portal.portal_preferences.slapos_default_system_preference

    preference.edit(
      preferred_credential_alarm_automatic_call=0,
      preferred_credential_recovery_automatic_approval=0,
      preferred_credential_request_automatic_approval=1,
      preferred_cloud_contract_enabled=True
    )

    # Enable alarms for regularisation request
    self.portal.portal_alarms.slapos_crm_create_regularisation_request.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_invalidate_suspended_regularisation_request.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_stop_reminder_escalation.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_stop_acknowledgment_escalation.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_delete_reminder_escalation.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_acknowledgment_escalation.setEnabled(True)

    # Create akarls steps
    self.createAlarmStep()

  @changeSkin('Hal')
  def joinSlapOS(self, web_site, reference):
    def findMessage(email, body):
      for candidate in reversed(self.portal.MailHost.getMessageList()):
        if [q for q in candidate[1] if email in q] and body in candidate[2]:
          return candidate[2]

    credential_request_form = self.web_site.hateoas.connection.join_form()

    expected_message = 'You will receive a confirmation email to activate your account.'
    self.assertTrue(expected_message in credential_request_form,
      '%s not in %s' % (expected_message, credential_request_form))

    email = '%s@example.com' % reference

    redirect_url = self.web_site.hateoas.connection.WebSection_newCredentialRequest(
      reference=reference,
      default_email_text=email,
      first_name="Joe",
      last_name=reference,
      password="demo_functional_user",
      default_telephone_text="12345678",
      corporate_name="Nexedi",
      default_address_city="Campos",
      default_address_street_address="Av Pelinca",
      default_address_zip_code="28480",
    )
    parsed_url = six.moves.urllib.parse.urlparse(redirect_url)
    self.assertEqual(parsed_url.path.split('/')[-1], 'login_form')
    self.assertEqual(
      sorted(six.iteritems(dict(six.moves.urllib.parse.parse_qsl(parsed_url.query)))), [
        ('portal_status_message', 'Thank you for your registration. You will receive an email to activate your account.'),
    ])
    self.tic()

    to_click_message = findMessage(email, 'You have requested one user')

    self.assertNotEqual(None, to_click_message)

    to_click_url = re.search('href="(.+?)"', to_click_message).group(1)

    self.assertIn('%s/hateoas/connection/ERP5Site_activeLogin' % self.web_site.getId(), to_click_url)
    
    join_key = to_click_url.split('=')[-1]
    self.assertNotEqual(join_key, None)
    web_site.ERP5Site_activeLogin(key=join_key)

    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 303)
    self.assertIn(self.web_site.getId() + "/%23%21login%3Fp.page%3Dslapos%7B%26n.me%7D",
      self.portal.REQUEST.RESPONSE.getHeader("Location"))

    self.tic()

    welcome_message = findMessage(email, "the creation of you new")
    self.assertNotEqual(None, welcome_message)

  def _getCurrentInstanceTreeList(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    if person is not None:
      return self.portal.portal_catalog(
        portal_type="Instance Tree",
        default_destination_section_uid=person.getUid(),
        validation_state='validated')

    return []

  def setAccessToMemcached(self, agent):
    agent.setAccessStatus("#access ")

  def requestComputeNode(self, title):
    requestXml = self.portal.portal_slap.requestComputer(title)
    self.tic()
    self.assertTrue('marshal' in requestXml)
    compute_node = xml_marshaller.xml_marshaller.loads(requestXml)
    compute_node_id = getattr(compute_node, '_computer_id', None)
    self.assertNotEqual(None, compute_node_id)
    return compute_node_id.encode('UTF-8')

  def supplySoftware(self, server, url, state='available'):
    self.portal.portal_slap.supplySupply(url, server.getReference(), state)
    self.tic()

    software_installation = self.portal.portal_catalog.getResultValue(
        portal_type='Software Installation',
        url_string=url,
        default_aggregate_uid=server.getUid())

    self.assertNotEqual(None, software_installation)

    if state=='available':
      self.assertEqual('start_requested', software_installation.getSlapState())
    else:
      self.assertEqual('destroy_requested', software_installation.getSlapState())

  @changeSkin('RJS')
  def setServerOpenPublic(self, server):
    server.edit(
        allocation_scope='open/public')
    self.assertEqual('open/public', server.getAllocationScope())
    # Called by alarm
    server.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', server.getCapacityScope())
    self.tic()

  @changeSkin('RJS')
  def setServerOpenSubscription(self, server):
    server.edit(
        allocation_scope='open/subscription')
    self.assertEqual('open/subscription', server.getAllocationScope())
    # Called by alarm
    server.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', server.getCapacityScope())
    self.tic()

  @changeSkin('RJS')
  def setServerOpenPersonal(self, server):
    server.edit(
        allocation_scope='open/personal', subject_list=[])
    self.assertEqual('open/personal', server.getAllocationScope())
    # Called by alarm
    server.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', server.getCapacityScope())
    self.tic()

  def formatComputeNode(self, compute_node, partition_count=10):
    compute_node_dict = dict(
      software_root='/opt',
      reference=compute_node.getReference(),
      netmask='255.255.255.0',
      address='128.0.0.1',
      instance_root='/srv'
    )
    compute_node_dict['partition_list'] = []
    a = compute_node_dict['partition_list'].append
    for i in range(1, partition_count+1):
      a(dict(
        reference='part%s' % i,
        tap=dict(name='tap%s' % i),
        address_list=[
          dict(addr='p%sa1' % i, netmask='p%sn1' % i),
          dict(addr='p%sa2' % i, netmask='p%sn2' % i)
        ]
      ))
    sm = getSecurityManager()
    try:
      self.login(compute_node.getUserId())
      self.portal.portal_slap.loadComputerConfigurationFromXML(
          xml_marshaller.xml_marshaller.dumps(compute_node_dict))
      self.tic()
      self.assertEqual(partition_count,
          len(compute_node.contentValues(portal_type='Compute Partition')))
    finally:
      setSecurityManager(sm)

  def simulateSlapgridSR(self, compute_node):
    sm = getSecurityManager()
    compute_node_user_id = compute_node.getUserId()
    try:
      self.login(compute_node_user_id)
      compute_node_xml = self.portal.portal_slap.getFullComputerInformation(
          computer_id=compute_node.getReference())
      if not isinstance(compute_node_xml, str):
        compute_node_xml = compute_node_xml.getBody()
      slap_compute_node = xml_marshaller.xml_marshaller.loads(compute_node_xml)
      self.assertEqual('Computer', slap_compute_node.__class__.__name__)
      for software_release in slap_compute_node._software_release_list:
        if software_release._requested_state == 'destroyed':
          self.portal.portal_slap.destroyedSoftwareRelease(
            software_release._software_release,
						compute_node.getReference())
        else:
          self.portal.portal_slap.availableSoftwareRelease(
            software_release._software_release,
						compute_node.getReference())
    finally:
      setSecurityManager(sm)
    self.tic()

  def simulateSlapgridUR(self, compute_node):
    sm = getSecurityManager()
    compute_node_user_id = compute_node.getUserId()
    try:
      self.login(compute_node_user_id)
      compute_node_xml = self.portal.portal_slap.getFullComputerInformation(
          computer_id=compute_node.getReference())
      if not isinstance(compute_node_xml, str):
        compute_node_xml = compute_node_xml.getBody()
      slap_compute_node = xml_marshaller.xml_marshaller.loads(compute_node_xml)
      self.assertEqual('Computer', slap_compute_node.__class__.__name__)
      destroyed_partition_id_list = []
      for partition in slap_compute_node._computer_partition_list:
        if partition._requested_state == 'destroyed' \
              and partition._need_modification == 1:
          self.portal.portal_slap.destroyedComputerPartition(compute_node.getReference(),
              partition._partition_id.encode("UTF-8")
              )
          destroyed_partition_id_list.append(partition._partition_id.encode("UTF-8"))
    finally:
      setSecurityManager(sm)
    self.tic()
    self.stepCallSlaposFreeComputePartitionAlarm()
    self.tic()
    free_partition_id_list = []
    for partition in compute_node.contentValues(portal_type='Compute Partition'):
      if partition.getReference() in destroyed_partition_id_list \
          and partition.getSlapState() == 'free':
        free_partition_id_list.append(partition.getReference())
    self.assertSameSet(destroyed_partition_id_list, free_partition_id_list)

  def simulateSlapgridCP(self, compute_node):
    sm = getSecurityManager()
    compute_node_reference = compute_node.getReference()
    compute_node_user_id = compute_node.getUserId()
    try:
      self.login(compute_node_user_id)
      compute_node_xml = self.portal.portal_slap.getFullComputerInformation(
        computer_id=compute_node.getReference())
      if not isinstance(compute_node_xml, str):
        compute_node_xml = compute_node_xml.getBody()
      slap_compute_node = xml_marshaller.xml_marshaller.loads(compute_node_xml)
      self.assertEqual('Computer', slap_compute_node.__class__.__name__)
      for partition in slap_compute_node._computer_partition_list:
        if partition._requested_state in ('started', 'stopped') \
              and partition._need_modification == 1:
          instance_reference = partition._instance_guid.encode('UTF-8')
          ip_list = partition._parameter_dict['ip_list']
          connection_xml = xml_marshaller.xml_marshaller.dumps(dict(
            url_1 = 'http://%s/' % ip_list[0][1],
            url_2 = 'http://%s/' % ip_list[1][1],
          ))
          self.login()
          instance_user_id = self.portal.portal_catalog.getResultValue(
              reference=instance_reference, portal_type="Software Instance").getUserId()

          oldsm = getSecurityManager()
          try:
            self.login(instance_user_id)
            self.portal.portal_slap.setComputerPartitionConnectionXml(
              computer_id=compute_node_reference,
              computer_partition_id=partition._partition_id,
              connection_xml=connection_xml
            )
            for slave in partition._parameter_dict['slave_instance_list']:
              slave_reference = slave['slave_reference']
              connection_xml = xml_marshaller.xml_marshaller.dumps(dict(
                url_1 = 'http://%s/%s' % (ip_list[0][1], slave_reference),
                url_2 = 'http://%s/%s' % (ip_list[1][1], slave_reference)
              ))
              self.portal.portal_slap.setComputerPartitionConnectionXml(
                computer_id=compute_node_reference,
                computer_partition_id=partition._partition_id,
                connection_xml=connection_xml,
                slave_reference=slave_reference
              )

          finally:
            setSecurityManager(oldsm)
    finally:
      setSecurityManager(sm)
    self.tic()

  def personRequestInstanceNotReady(self, **kw):
    response = self.portal.portal_slap.requestComputerPartition(**kw)
    status = getattr(response, 'status', None)
    self.assertEqual(408, status)
    self.tic()

  def personRequestInstance(self, **kw):
    response = self.portal.portal_slap.requestComputerPartition(**kw)
    self.assertTrue(isinstance(response, str), "response is not a string: %s" % response)
    software_instance = xml_marshaller.xml_marshaller.loads(response)
    self.assertEqual('SoftwareInstance', software_instance.__class__.__name__)
    self.tic()
    return software_instance

  def checkSlaveInstanceAllocation(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>'
    )

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>'
    )

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]
    self.assertEqual(1, len(instance_tree_list))
    instance_tree = instance_tree_list[0]

    software_instance = instance_tree.getSuccessorValue()
    self.assertEqual(software_instance.getTitle(),
        instance_tree.getTitle())
    connection_dict = software_instance.getConnectionXmlAsDict()
    self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
    self.login()
    partition = software_instance.getAggregateValue()
    self.assertSameSet(
        ['http://%s/%s' % (q.getIpAddress(), software_instance.getReference())
            for q in partition.contentValues(
                portal_type='Internet Protocol Address')],
        connection_dict.values())

  def checkSlaveInstanceUnallocation(self, person_user_id,
      person_reference, instance_title,
      software_release, software_type, server):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>',
      state='<marshal><string>destroyed</string></marshal>'
    )

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]

    self.assertEqual(0, len(instance_tree_list))

  def checkInstanceUnallocation(self, person_user_id,
      person_reference, instance_title,
      software_release, software_type, server):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      state='<marshal><string>destroyed</string></marshal>'
    )

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridUR(server)

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]
    self.assertEqual(0, len(instance_tree_list))

  def checkCloudContract(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server):

    self.login()
    self.assertTrue(self.portal.portal_preferences.getPreferredCloudContractEnabled())

    self.stepCallSlaposContractRequestValidationPaymentAlarm()
    self.tic()

    # stabilise aggregated invoices and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount transaction lines
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # stop the invoices and solve them again
    self.stepCallSlaposStopConfirmedAggregatedSaleInvoiceTransactionAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # trigger the CRM interaction
    self.stepCallSlaposCrmCreateRegularisationRequestAlarm()
    self.tic()

    # trigger the CRM interaction
    self.stepCallSlaposCrmCreateRegularisationRequestAlarm()
    self.tic()

    self.login()

    person = self.portal.portal_catalog.getResultValue(
      portal_type="Person",
      user_id=person_user_id)

    contract = self.portal.portal_catalog.getResultValue(
      portal_type="Cloud Contract",
      default_destination_section_uid=person.getUid(),
      validation_state=['invalidated', 'validated'])
    
    self.assertNotEqual(contract, None)
    self.assertEqual(contract.getValidationState(), "invalidated")
    
    # HACK FOR NOW
    contract.validate()
    self.tic()

    self.login(person_user_id)

    self.stepCallSlaposContractRequestValidationPaymentAlarm()
    self.tic()


  def checkInstanceAllocation(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server):

    self.login(person_user_id)

    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
    )

    self.checkCloudContract(person_user_id, person_reference,
      instance_title, software_release, software_type, server)

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
    )

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]
    self.assertEqual(1, len(instance_tree_list))
    instance_tree = instance_tree_list[0]

    software_instance = instance_tree.getSuccessorValue()
    self.assertEqual(software_instance.getTitle(),
        instance_tree.getTitle())
    connection_dict = software_instance.getConnectionXmlAsDict()
    self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
    self.login()
    partition = software_instance.getAggregateValue()
    self.assertSameSet(
        ['http://%s/' % q.getIpAddress() for q in
            partition.contentValues(portal_type='Internet Protocol Address')],
        connection_dict.values())

  def assertInstanceTreeSimulationCoverage(self, subscription):
    self.login()
    # this is document level assertion, as simulation and its specific delivery
    # is covered by unit tests
    packing_list_line_list = subscription.getAggregateRelatedValueList(
        portal_type='Sale Packing List Line')
    self.assertEqual(len(packing_list_line_list), 1)
    for packing_list_line in packing_list_line_list:
      packing_list = packing_list_line.getParentValue()
      self.assertEqual('Sale Packing List',
          packing_list.getPortalType())
      self.assertEqual('delivered',
          packing_list.getSimulationState())
      causality_state = packing_list.getCausalityState()
      self.assertEqual('solved', causality_state)

  def assertAggregatedSalePackingList(self, delivery):
    self.assertEqual('delivered', delivery.getSimulationState())
    self.assertEqual('solved', delivery.getCausalityState())

    invoice_list= delivery.getCausalityRelatedValueList(
        portal_type='Sale Invoice Transaction')
    self.assertEqual(1, len(invoice_list))
    invoice = invoice_list[0].getObject()

    causality_list = invoice.getCausalityValueList()

    self.assertSameSet([delivery], causality_list)

    self.assertEqual('stopped', invoice.getSimulationState())
    self.assertEqual('solved', invoice.getCausalityState())

    payment_list = invoice.getCausalityRelatedValueList(
        portal_type='Payment Transaction')
    self.assertEqual(0, len(payment_list))

  def assertPersonDocumentCoverage(self, person):
    self.login()
    subscription_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        default_destination_section_uid=person.getUid())
    for subscription in subscription_list:
      self.assertInstanceTreeSimulationCoverage(
          subscription.getObject())

    aggregated_delivery_list = self.portal.portal_catalog(
        portal_type='Sale Packing List',
        default_destination_section_uid=person.getUid(),
        specialise_uid=self.portal.restrictedTraverse(self.portal\
          .portal_preferences.getPreferredAggregatedSaleTradeCondition()\
          ).getUid()
    )

    if len(subscription_list) == 0:
      self.assertEqual(0, len(aggregated_delivery_list))
      return

    self.assertNotEqual(0, len(aggregated_delivery_list))
    for aggregated_delivery in aggregated_delivery_list:
      self.assertAggregatedSalePackingList(aggregated_delivery.getObject())

  def assertOpenSaleOrderCoverage(self, person_reference):
    self.login()
    person = self.portal.portal_catalog.getResultValue(
       portal_type='ERP5 Login',
       reference=person_reference).getParentValue()
    instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        default_destination_section_uid=person.getUid()
    )

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid(),
    )

    if len(instance_tree_list) == 0:
      self.assertEqual(0, len(open_sale_order_list))
      return

    self.assertEqual(2, len(open_sale_order_list))

    archived_open_sale_order_list = [q for q in open_sale_order_list
                       if q.getValidationState() == 'archived']

    archived_open_sale_order_list.sort(key=lambda x: x.getCreationDate())
    
    # Select the first archived
    open_sale_order = archived_open_sale_order_list[0]

    line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    self.assertEqual(len(instance_tree_list), len(line_list))
    self.assertSameSet(
        [q.getRelativeUrl() for q in instance_tree_list],
        [q.getAggregate() for q in line_list]
    )

    validated_open_sale_order_list = [q for q in open_sale_order_list
                       if q.getValidationState() == 'validated']

    # if no line, all open orders are kept archived
    self.assertEqual(len(validated_open_sale_order_list), 0)

    latest_open_sale_order = archived_open_sale_order_list[-1]
    line_list = latest_open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    self.assertEqual(len(line_list), 0)

  def findMessage(self, email, body):
    for candidate in reversed(self.portal.MailHost.getMessageList()):
      if [q for q in candidate[1] if email in q] and body in candidate[2]:
        return candidate[2]

  def assertInvoiceNotification(self, person, is_email_expected=True):

    if person.getLanguage() == "zh":
      expected_message = self.expected_invoice_zh_notification_message
    else:
      expected_message = self.expected_invoice_en_notification_message 

    to_click_message = self.findMessage(person.getDefaultEmailText(),
                                        expected_message)
    if is_email_expected:
      self.assertNotEqual(None, to_click_message)
    else:
      self.assertEqual(None, to_click_message)

  @changeSkin('RJS')
  def usePaymentManually(self, web_site, user_id, is_email_expected=True, subscription_request=None):
    person = self.portal.portal_catalog.getResultValue(
      portal_type="Person",
      user_id=user_id)

    self.assertNotEqual(person, None)
    self.assertInvoiceNotification(person, is_email_expected)

    invoice_list = person.Entity_getOutstandingAmountList()

    self.login() 
    if subscription_request is not None:
      expected_causality = subscription_request.getRelativeUrl()
      filtered_invoice_list = []
      for invoice in invoice_list:
        spl = invoice.getCausalityValue()
        if spl is not None and spl.getCausality() == expected_causality:
          filtered_invoice_list.append(invoice)
      
      self.assertEqual(len(filtered_invoice_list), 1)
      invoice_list = filtered_invoice_list
    else:
      self.assertEqual(len(invoice_list), 1)

    self.login(user_id)
    document_id = invoice_list[0].getId()
    web_site.accounting_module[document_id].\
      SaleInvoiceTransaction_redirectToManualSlapOSPayment()
    self.tic()

  def assertSubscriptionStopped(self, person):
    self.login()
    subscription_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        default_destination_section_uid=person.getUid())
    self.assertEqual(len(subscription_list), 1)
    for subscription in subscription_list:
      self.assertEqual(subscription.getSlapState(), "stop_requested")

  def assertSubscriptionDestroyed(self, person):
    self.login()
    subscription_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        default_destination_section_uid=person.getUid())
    self.assertEqual(len(subscription_list), 1)
    for subscription in subscription_list:
      self.assertEqual(subscription.getSlapState(), "destroy_requested")

  def requestInstance(self, person_user_id, instance_title,
      software_release, software_type):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
    )
