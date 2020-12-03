# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSCloudSecurityGroup import TestSlapOSSecurityMixin
from erp5.component.test.SlapOSTestCaseMixin import changeSkin
import json
import re
import xml_marshaller
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager
from DateTime import DateTime

class DefaultScenarioMixin(TestSlapOSSecurityMixin):

  def afterSetUp(self):
    TestSlapOSSecurityMixin.afterSetUp(self)
    preference = self.portal.portal_preferences.getActiveSystemPreference()

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

    request = self.web_site.hateoas.connection.WebSection_newCredentialRequest(
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

    self.assertIn('Thank you for your registration. You will receive an email to activate your account.', request)

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

    welcome_message = findMessage(email, "the creation of you new ERP5 account")
    self.assertNotEqual(None, welcome_message)

  def _getCurrentHostingSubscriptionList(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    if person is not None:
      return self.portal.portal_catalog(
        portal_type="Hosting Subscription",
        default_destination_section_uid=person.getUid(),
        validation_state='validated')

    return []

  def setAccessToMemcached(self, agent):
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
      key_prefix='slap_tool',
      plugin_path='portal_memcached/default_memcached_plugin')

    access_date = DateTime()
    memcached_dict[agent.getReference()] = json.dumps(
        {"created_at":"%s" % access_date, "text": "#access "}
    )

  def requestComputer(self, title):
    requestXml = self.portal.portal_slap.requestComputer(title)
    self.tic()
    self.assertTrue('marshal' in requestXml)
    computer = xml_marshaller.xml_marshaller.loads(requestXml)
    computer_id = getattr(computer, '_computer_id', None)
    self.assertNotEqual(None, computer_id)
    return computer_id.encode('UTF-8')

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
    self.assertEqual('close', server.getCapacityScope())
    server.edit(capacity_scope='open')
    self.tic()

  @changeSkin('RJS')
  def setServerOpenSubscription(self, server):
    server.edit(
        allocation_scope='open/subscription')
    self.assertEqual('open/subscription', server.getAllocationScope())
    self.assertEqual('close', server.getCapacityScope())
    server.edit(capacity_scope='open')
    self.tic()

  @changeSkin('RJS')
  def setServerOpenPersonal(self, server):
    server.edit(
        allocation_scope='open/personal', subject_list=[])
    self.assertEqual('open/personal', server.getAllocationScope())
    self.assertEqual('open', server.getCapacityScope())
    self.tic()

  @changeSkin('RJS')
  def setServerOpenFriend(self, server, friend_list=None):
    if friend_list is None:
      friend_list = []
    server.edit(
        allocation_scope='open/friend', subject_list=friend_list)
    self.assertEqual('open/friend', server.getAllocationScope())
    self.assertEqual('open', server.getCapacityScope())
    self.assertSameSet(friend_list, server.getSubjectList())
    self.tic()

  def formatComputer(self, computer, partition_count=10):
    computer_dict = dict(
      software_root='/opt',
      reference=computer.getReference(),
      netmask='255.255.255.0',
      address='128.0.0.1',
      instance_root='/srv'
    )
    computer_dict['partition_list'] = []
    a = computer_dict['partition_list'].append
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
      self.login(computer.getUserId())
      self.portal.portal_slap.loadComputerConfigurationFromXML(
          xml_marshaller.xml_marshaller.dumps(computer_dict))
      self.tic()
      self.assertEqual(partition_count,
          len(computer.contentValues(portal_type='Computer Partition')))
    finally:
      setSecurityManager(sm)

  def simulateSlapgridSR(self, computer):
    sm = getSecurityManager()
    computer_user_id = computer.getUserId()
    try:
      self.login(computer_user_id)
      computer_xml = self.portal.portal_slap.getFullComputerInformation(
          computer_id=computer.getReference())
      if not isinstance(computer_xml, str):
        computer_xml = computer_xml.getBody()
      slap_computer = xml_marshaller.xml_marshaller.loads(computer_xml)
      self.assertEqual('Computer', slap_computer.__class__.__name__)
      for software_release in slap_computer._software_release_list:
        if software_release._requested_state == 'destroyed':
          self.portal.portal_slap.destroyedSoftwareRelease(
            software_release._software_release,
						computer.getReference())
        else:
          self.portal.portal_slap.availableSoftwareRelease(
            software_release._software_release,
						computer.getReference())
    finally:
      setSecurityManager(sm)
    self.tic()

  def simulateSlapgridUR(self, computer):
    sm = getSecurityManager()
    computer_user_id = computer.getUserId()
    try:
      self.login(computer_user_id)
      computer_xml = self.portal.portal_slap.getFullComputerInformation(
          computer_id=computer.getReference())
      if not isinstance(computer_xml, str):
        computer_xml = computer_xml.getBody()
      slap_computer = xml_marshaller.xml_marshaller.loads(computer_xml)
      self.assertEqual('Computer', slap_computer.__class__.__name__)
      destroyed_partition_id_list = []
      for partition in slap_computer._computer_partition_list:
        if partition._requested_state == 'destroyed' \
              and partition._need_modification == 1:
          self.portal.portal_slap.destroyedComputerPartition(computer.getReference(),
              partition._partition_id.encode("UTF-8")
              )
          destroyed_partition_id_list.append(partition._partition_id.encode("UTF-8"))
    finally:
      setSecurityManager(sm)
    self.tic()
    self.stepCallSlaposFreeComputerPartitionAlarm()
    self.tic()
    free_partition_id_list = []
    for partition in computer.contentValues(portal_type='Computer Partition'):
      if partition.getReference() in destroyed_partition_id_list \
          and partition.getSlapState() == 'free':
        free_partition_id_list.append(partition.getReference())
    self.assertSameSet(destroyed_partition_id_list, free_partition_id_list)

  def simulateSlapgridCP(self, computer):
    sm = getSecurityManager()
    computer_reference = computer.getReference()
    computer_user_id = computer.getUserId()
    try:
      self.login(computer_user_id)
      computer_xml = self.portal.portal_slap.getFullComputerInformation(
        computer_id=computer.getReference())
      if not isinstance(computer_xml, str):
        computer_xml = computer_xml.getBody()
      slap_computer = xml_marshaller.xml_marshaller.loads(computer_xml)
      self.assertEqual('Computer', slap_computer.__class__.__name__)
      for partition in slap_computer._computer_partition_list:
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
              computer_id=computer_reference,
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
                computer_id=computer_reference,
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

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    hosting_subscription_list = [q.getObject() for q in
        self._getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]
    self.assertEqual(1, len(hosting_subscription_list))
    hosting_subscription = hosting_subscription_list[0]

    software_instance = hosting_subscription.getPredecessorValue()
    self.assertEqual(software_instance.getTitle(),
        hosting_subscription.getTitle())
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
    hosting_subscription_list = [q.getObject() for q in
        self._getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]

    self.assertEqual(0, len(hosting_subscription_list))

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

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridUR(server)

    # let's find instances of user and check connection strings
    hosting_subscription_list = [q.getObject() for q in
        self._getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]
    self.assertEqual(0, len(hosting_subscription_list))

  def checkCloudContract(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server):

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

    builder = self.portal.portal_orders.slapos_payment_transaction_builder
    for _ in range(500):
      # build the aggregated payment
      self.stepCallSlaposTriggerPaymentTransactionOrderBuilderAlarm()
      self.tic()
      # If there is something unbuild recall alarm.
      if len(builder.OrderBuilder_generateUnrelatedInvoiceList()):
        break

    # start the payzen payment
    self.stepCallSlaposPayzenUpdateConfirmedPaymentAlarm()
    self.tic()

    # stabilise the payment deliveries and expand them
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

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    hosting_subscription_list = [q.getObject() for q in
        self._getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]
    self.assertEqual(1, len(hosting_subscription_list))
    hosting_subscription = hosting_subscription_list[0]

    software_instance = hosting_subscription.getPredecessorValue()
    self.assertEqual(software_instance.getTitle(),
        hosting_subscription.getTitle())
    connection_dict = software_instance.getConnectionXmlAsDict()
    self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
    self.login()
    partition = software_instance.getAggregateValue()
    self.assertSameSet(
        ['http://%s/' % q.getIpAddress() for q in
            partition.contentValues(portal_type='Internet Protocol Address')],
        connection_dict.values())

  def assertHostingSubscriptionSimulationCoverage(self, subscription):
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
    self.assertEqual(1, len(payment_list))

    payment = payment_list[0].getObject()

    causality_list = payment.getCausalityValueList()
    self.assertSameSet([invoice], causality_list)

    self.assertEqual('started', payment.getSimulationState())
    self.assertEqual('draft', payment.getCausalityState())

    self.assertEqual(-1 * payment.PaymentTransaction_getTotalPayablePrice(),
        invoice.getTotalPrice())

  def assertPersonDocumentCoverage(self, person):
    self.login()
    subscription_list = self.portal.portal_catalog(
        portal_type='Hosting Subscription',
        default_destination_section_uid=person.getUid())
    for subscription in subscription_list:
      self.assertHostingSubscriptionSimulationCoverage(
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
    hosting_subscription_list = self.portal.portal_catalog(
        portal_type='Hosting Subscription',
        default_destination_section_uid=person.getUid()
    )

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid(),
    )

    if len(hosting_subscription_list) == 0:
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
    self.assertEqual(len(hosting_subscription_list), len(line_list))
    self.assertSameSet(
        [q.getRelativeUrl() for q in hosting_subscription_list],
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
  def useWechatManually(self, web_site, user_id, is_email_expected=True):

    person = self.portal.portal_catalog.getResultValue(
      portal_type="Person",
      user_id=user_id)

    self.assertNotEqual(person, None)
    self.assertInvoiceNotification(person, is_email_expected)

    # If you are using live test, be aware that the call of the alarm can be
    # not enough for the number of objects on the site.
    document_id = self.portal.portal_catalog.getResultValue(
				portal_type="Payment Transaction",
				simulation_state="started",
        destination_section_uid=person.getUid()
				).getId()

    web_site.accounting_module[document_id].\
      PaymentTransaction_redirectToManualWechatPayment()

  @changeSkin('RJS')
  def usePayzenManually(self, web_site, user_id, is_email_expected=True):
    person = self.portal.portal_catalog.getResultValue(
      portal_type="Person",
      user_id=user_id)

    self.assertNotEqual(person, None)
    self.assertInvoiceNotification(person, is_email_expected)

    # Pay to payzen...
    # If you are using live test, be aware that the call of the alarm can be
    # not enough for the number of objects on the site.
    document_id = self.portal.portal_catalog.getResultValue(
				portal_type="Payment Transaction",
				simulation_state="started",
        destination_section_uid=person.getUid()
				).getId()

    web_site.accounting_module[document_id].\
      PaymentTransaction_redirectToManualPayzenPayment()

  def assertSubscriptionStopped(self, person):
    self.login()
    subscription_list = self.portal.portal_catalog(
        portal_type='Hosting Subscription',
        default_destination_section_uid=person.getUid())
    self.assertEqual(len(subscription_list), 1)
    for subscription in subscription_list:
      self.assertEqual(subscription.getSlapState(), "stop_requested")

  def assertSubscriptionDestroyed(self, person):
    self.login()
    subscription_list = self.portal.portal_catalog(
        portal_type='Hosting Subscription',
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
