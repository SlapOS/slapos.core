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
from slapos.util import dumps, loads
from Products.ERP5Type.Utils import str2bytes, bytes2str
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager

class DefaultScenarioMixin(TestSlapOSSecurityMixin):

  require_certificate = 1

  def afterSetUp(self):
    TestSlapOSSecurityMixin.afterSetUp(self)
    """
    preference = self.portal.portal_preferences.slapos_default_system_preference

    preference.edit(
      preferred_credential_alarm_automatic_call=0,
      preferred_credential_recovery_automatic_approval=0,
      preferred_credential_request_automatic_approval=1
    )

    # Enable alarms for regularisation request
    self.portal.portal_alarms.slapos_crm_create_regularisation_request.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_invalidate_suspended_regularisation_request.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_stop_reminder_escalation.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_stop_acknowledgment_escalation.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_delete_reminder_escalation.setEnabled(True)
    self.portal.portal_alarms.slapos_crm_trigger_acknowledgment_escalation.setEnabled(True)
"""
    # Create akarls steps
    self.createAlarmStep()

  def createProject(self):
    project = self.portal.project_module.newContent(
      portal_type='Project',
      title='project-%s' % self.generateNewId()
    )
    project.validate()
    return project

  def createAdminUser(self, project):
    """ Create a Admin user, to manage compute_nodes and instances eventually """
    admin_user_login = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference="admin_user",
      validation_state="validated"
    )

    if admin_user_login is None:
      admin_user = self.portal.person_module\
                                 .newContent(portal_type="Person")

      admin_user.newContent(
        portal_type="ERP5 Login",
        reference="admin_user").validate()
      admin_user.edit(
        first_name="Admin User",
        reference="Admin_user",
        default_email_text="do_not_reply_to_admin@example.org",
      )

      admin_user.validate()

    else:
      admin_user = admin_user_login.getParentValue()

    admin_user.newContent(
      portal_type='Assignment',
      destination_project_value=project,
      function='production/manager'
    ).open()

    self.admin_user = admin_user

  @changeSkin('Hal')
  def joinSlapOS(self, web_site, reference):
    def findMessage(email, body):
      for candidate in reversed(self.portal.MailHost.getMessageList()):
        if [q for q in candidate[1] if email in q] and body in candidate[2]:
          return candidate[2]

    self.portal.portal_skins.changeSkin('RJS')
    credential_request_form = self.web_site.slapos_master_panel.hateoas.connection.join_form()

    expected_message = 'You will receive a confirmation email to activate your account.'
    self.assertTrue(expected_message in credential_request_form,
      '%s not in %s' % (expected_message, credential_request_form))

    # According to email address RFC you should be 'ascii' compatible
    # for email specificiations.
    # reference: https://en.wikipedia.org/wiki/Email_address#Local-part
    email = 'joe%s@example.com' % self.generateNewAsciiId()

    redirect_url = self.web_site.slapos_master_panel.hateoas.connection.WebSection_newCredentialRequest(
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
      default_address_region='europe/west/france',
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
    self.portal.portal_skins.changeSkin('RJS')
    web_site.slapos_master_panel.hateoas.connection.ERP5Site_activeLogin(key=join_key)

    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 303)
    self.assertIn(self.web_site.getId() + "/%23%21login%3Fp.page%3Dslapos_master_panel_access%26p.view%3D1%7B%26n.me%7D",
      self.portal.REQUEST.RESPONSE.getHeader("Location"))

    self.tic()

    welcome_message = findMessage(email, "the creation of you new")
    self.assertNotEqual(None, welcome_message)

    self.login()
    # Fetch the user from login and return
    return self.portal.portal_catalog.getResultValue(
        portal_type="ERP5 Login",
        reference=reference).getParentValue()

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

  def requestComputeNode(self, title, project_reference):
    requestXml = self.portal.portal_slap.requestComputer(title, project_reference)
    self.tic()
    self.assertIn('marshal', requestXml)
    compute_node = loads(str2bytes(requestXml))
    compute_node_id = getattr(compute_node, '_computer_id', None)
    self.assertNotEqual(None, compute_node_id)
    return compute_node_id.encode('UTF-8')

  def supplySoftware(self, server, url, state='available'):
    self.portal.portal_slap.supplySupply(url, server.getReference(), state)
    self.tic()
    self.cleanUpRequest()

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
        allocation_scope='open')
    self.assertEqual('open', server.getAllocationScope())
    self.assertEqual('close', server.getCapacityScope())
    server.edit(capacity_scope='open')
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
          bytes2str(dumps(compute_node_dict)))
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
      slap_compute_node = loads(str2bytes(compute_node_xml))
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

  def simulateSlapgridUR(self, compute_node, consumption_xml_report=None):
    sm = getSecurityManager()
    compute_node_user_id = compute_node.getUserId()
    try:
      self.login(compute_node_user_id)
      compute_node_xml = self.portal.portal_slap.getFullComputerInformation(
          computer_id=compute_node.getReference())
      if not isinstance(compute_node_xml, str):
        compute_node_xml = compute_node_xml.getBody()
      slap_compute_node = loads(str2bytes(compute_node_xml))
      self.assertEqual('Computer', slap_compute_node.__class__.__name__)
      if consumption_xml_report is not None:
        response = self.portal.portal_slap.useComputer(
           compute_node.getReference(), consumption_xml_report)
        # Ensure it succeed
        self.assertEqual(200, response.status)
        self.assertEqual("OK", response.body)
      destroyed_partition_id_list = []
      for partition in slap_compute_node._computer_partition_list:
        if partition._requested_state == 'destroyed' \
              and partition._need_modification == 1:
          self.portal.portal_slap.destroyedComputerPartition(compute_node.getReference(),
              partition._partition_id
              )
          destroyed_partition_id_list.append(partition._partition_id)
    finally:
      setSecurityManager(sm)
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
      slap_compute_node = loads(str2bytes(compute_node_xml))
      self.assertEqual('Computer', slap_compute_node.__class__.__name__)
      for partition in slap_compute_node._computer_partition_list:
        if partition._requested_state in ('started', 'stopped') \
              and partition._need_modification == 1:
          instance_reference = partition._instance_guid.encode('UTF-8')
          ip_list = partition._parameter_dict['ip_list']
          connection_xml = bytes2str(dumps(dict(
            url_1 = 'http://%s/' % ip_list[0][1],
            url_2 = 'http://%s/' % ip_list[1][1],
          )))
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
              connection_xml = bytes2str(dumps(dict(
                url_1 = 'http://%s/%s' % (ip_list[0][1], slave_reference),
                url_2 = 'http://%s/%s' % (ip_list[1][1], slave_reference)
              )))
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
    software_instance = loads(str2bytes(response))
    self.assertEqual('SoftwareInstance', software_instance.__class__.__name__)
    self.tic()
    return software_instance

  def checkSlaveInstanceAllocation(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server,
       project_reference):

    self.tic()
    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>',
      project_reference=project_reference
    )

    # XXX search only for this user
    instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type="Instance Tree",
      title=instance_title,
      follow_up__reference=project_reference
    )
    self.checkServiceSubscriptionRequest(instance_tree)
    self.tic()

    self.login(person_user_id)
    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>',
      project_reference=project_reference
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

  def checkInstanceTreeSlaveInstanceAllocation(
    self,
    person_user_id,
    person_reference,
    instance_tree_title, instance_title, software_release, software_type,
    server,
    project_reference
  ):

    self.login(person_user_id)

    # let's find instance of user
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_tree_title]
    self.assertEqual(1, len(instance_tree_list))
    instance_tree = instance_tree_list[0]

    software_instance = instance_tree.getSuccessorValue()

    self.login()
    instance_user_id = software_instance.getUserId()
    compute_partition = software_instance.getAggregateValue()
    computer_id = compute_partition.getParentValue().getReference()
    computer_partition_id = compute_partition.getTitle()

    self.login(instance_user_id)

    response = self.portal.portal_slap.requestComputerPartition(
      computer_id=computer_id,
      computer_partition_id=computer_partition_id,
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>2</bool></marshal>',
      project_reference=project_reference
    )
    status = getattr(response, 'status', None)
    self.assertEqual(408, status)
    self.tic()

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    slave_instance = software_instance.getSuccessorValue()

    connection_dict = slave_instance.getConnectionXmlAsDict()
    self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
    self.login()
    partition = slave_instance.getAggregateValue()
    self.assertSameSet(
        ['http://%s/%s' % (q.getIpAddress(), slave_instance.getReference())
            for q in partition.contentValues(
                portal_type='Internet Protocol Address')],
        connection_dict.values())

  def checkRemoteInstanceAllocation(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server,
      project_reference, connection_dict_to_check=None,
      slave=False):

    shared_xml = '<marshal><bool>%i</bool></marshal>' % int(slave)

    self.login(person_user_id)

    if connection_dict_to_check is None:
      self.personRequestInstanceNotReady(
        software_release=software_release,
        software_type=software_type,
        partition_reference=instance_title,
        project_reference=project_reference,
        shared_xml=shared_xml,
      )

      # XXX search only for this user
      instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=instance_title,
        follow_up__reference=project_reference
      )
      self.checkServiceSubscriptionRequest(instance_tree)

      self.tic()
      self.login(person_user_id)

    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference,
      shared_xml=shared_xml,
    )

    # now instantiate it on compute_node and set some nice connection dict
    # XXX XXX self.simulateSlapgridCP(server)

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

    if connection_dict_to_check is None:
      connection_dict_to_check = {}

    self.assertSameSet(connection_dict_to_check.keys(), connection_dict.keys())
    self.assertSameSet(
        connection_dict_to_check.values(),
        connection_dict.values())

  def checkSlaveInstanceUnallocation(self, person_user_id,
      person_reference, instance_title,
      software_release, software_type, server,
      project_reference):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>',
      state='<marshal><string>destroyed</string></marshal>',
      project_reference=project_reference
    )

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]

    self.assertEqual(0, len(instance_tree_list))

  def checkRemoteInstanceUnallocation(self, person_user_id,
      person_reference, instance_title,
      software_release, software_type, server,
      project_reference):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      state='<marshal><string>destroyed</string></marshal>',
      project_reference=project_reference
    )

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]

    self.assertEqual(0, len(instance_tree_list))

  def checkInstanceUnallocation(self, person_user_id,
      person_reference, instance_title,
      software_release, software_type, server, project_reference):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      state='<marshal><string>destroyed</string></marshal>',
      project_reference=project_reference
    )

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridUR(server)

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]
    self.assertEqual(0, len(instance_tree_list))

  def checkServiceSubscriptionRequest(self, service, simulation_state='invalidated'):
    self.login()

    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type="Subscription Request",
      aggregate__uid=service.getUid(),
      simulation_state=simulation_state
    )
    self.assertNotEqual(subscription_request, None,
      "Not found subscription request for %s" % service.getRelativeUrl())
    return subscription_request

  def checkInstanceAllocation(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server,
      project_reference):

    self.login(person_user_id)

    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference
    )
    self.tic()

    # XXX search only for this user
    instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type="Instance Tree",
      title=instance_title,
      follow_up__reference=project_reference
    )
    self.checkServiceSubscriptionRequest(instance_tree)
    self.tic()

    self.login(person_user_id)
    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference
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

  def checkInstanceAllocationWithDeposit(self, person_user_id, person_reference,
      instance_title, software_release, software_type, server,
      project_reference, deposit_amount, currency):

    self.login(person_user_id)

    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference
    )
    self.tic()

    instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type="Instance Tree",
      title=instance_title,
      follow_up__reference=project_reference
    )
    person = instance_tree.getDestinationSectionValue()
    self.assertEqual(person.getUserId(), person_user_id)

    subscription_request = self.checkServiceSubscriptionRequest(instance_tree, 'submitted')
    self.assertEqual(
      subscription_request.getTotalPrice() - person.Entity_getDepositBalanceAmount([subscription_request]),
      deposit_amount
    )

    self.tic()

    outstanding_amount_list = person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=subscription_request.getLedgerUid())

    self.assertEqual(sum([i.total_price for i in outstanding_amount_list]), deposit_amount)

    self.login(person.getUserId())
    # Ensure to pay from the website
    outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
    outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()
    person.REQUEST.set('Entity_addDepositPayment_%s' % person.getUid(), None)
    self.tic()
    self.logout()
    self.login()
    payment_transaction = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      destination_section_uid=person.getUid(),
      simulation_state="started"
    )
    self.assertEqual(payment_transaction.getSpecialiseValue().getTradeConditionType(), "deposit")
    # payzen interface will only stop the payment
    payment_transaction.stop()
    self.tic()
    assert payment_transaction.receivable.getGroupingReference(None) is not None
    self.login(person_user_id)

    self.checkServiceSubscriptionRequest(instance_tree, 'invalidated')

    amount = sum([i.total_price for i in person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=subscription_request.getLedgerUid())])
    self.assertEqual(0, amount)

    self.login(person_user_id)
    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference
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

  def requestInstance(self, person_user_id, instance_title,
      software_release, software_type, project_reference):

    self.login(person_user_id)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference
    )
