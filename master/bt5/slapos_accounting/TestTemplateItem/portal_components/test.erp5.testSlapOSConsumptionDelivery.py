# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2025 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSConsumptionScenario import \
  TestSlapOSConsumptionScenarioMixin

from erp5.component.test.SlapOSTestCaseMixin import  TemporaryAlarmScript, \
  PinnedDateTime

from zExceptions import Unauthorized
from DateTime import DateTime

class TestSlapOSComputerConsumptionTioXMLFile_generateConsumptionDelivery(
                                          TestSlapOSConsumptionScenarioMixin):

  require_certificate = 1
  _start_date = DateTime('2024/05/01')
  _stop_date = DateTime('2024/06/01')

  def bootstrapGenerateConsumptionDeliveryTest(self, shared=False):
    with PinnedDateTime(self, DateTime('2024/12/20')):
      currency, _, _, person, _ = self.bootstrapVirtualMasterTest(
        is_virtual_master_accountable=False)

      self.logout()
      self.login()
      service = self.addConsumptionService()
      self.tic()
      self.logout()
      self.login(person.getUserId())

      # create a default project
      project_relative_url = self.addProject(person=person, currency=currency)
      project = self.portal.restrictedTraverse(project_relative_url)

      self.addProjectCustomerAssignment(person, project)
      self.addProjectProductionManagerAssignment(person, project)
      self.tic()
      self.logout()
      self.login(person.getUserId())

      compute_node_reference = self.requestComputeNode(
        'Public Server for %s' % self.generateNewId(), project.getReference())
      compute_node = self.portal.portal_catalog.getResultValue(
          portal_type='Compute Node', reference=compute_node_reference)
      self.setAccessToMemcached(compute_node)
      self.assertNotEqual(None, compute_node)
      self.setServerOpenPublic(compute_node)
      compute_node.generateCertificate()

      # and install some software on them
      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      self.supplySoftware(compute_node, public_server_software)

      # format the compute_nodes
      self.formatComputeNode(compute_node)

      software_product, release_variation, type_variation = self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

      self.addAllocationSupply("for compute node",
            compute_node, software_product,
            release_variation, type_variation)

      self.tic()

    with PinnedDateTime(self, DateTime('2024/02/20 01:01')):
      instance_title = 'Public title %s' % self.generateNewId()
      self.checkInstanceAllocation(person.getUserId(),
          person.getUserId(), instance_title,
          public_server_software, public_instance_type,
          compute_node, project.getReference())

      if shared:
        self.tic()
        self.login(person.getUserId())
        instance_node_title = 'Shared Instance for %s' % self.generateNewId()
        # Convert the Software Instance into an Instance Node
        # to explicitely mark it as accepting Slave Instance
        software_instance = self.portal.portal_catalog.getResultValue(
            portal_type='Software Instance', title=instance_title)
        instance_node = self.addInstanceNode(
          instance_node_title, software_instance)

        slave_server_software = self.generateNewSoftwareReleaseUrl()
        slave_instance_type = 'slave type'
        software_product, software_release, software_type = self.addSoftwareProduct(
          'share product', project, slave_server_software, slave_instance_type
        )
        self.addAllocationSupply("for instance node",
          instance_node, software_product, software_release, software_type)

        self.login()
        another_instance_title = 'Slave title %s' % self.generateNewId()
        self.checkSlaveInstanceAllocation(person.getUserId(),
            person.getUserId(), another_instance_title,
            slave_server_software, slave_instance_type,
            compute_node, project.getReference())
      else:
        another_instance_title= 'Public title another %s' % self.generateNewId()
        self.checkInstanceAllocation(person.getUserId(),
            person.getUserId(), another_instance_title,
            public_server_software, public_instance_type,
            compute_node, project.getReference())

    self.tic()
    self.logout()
    self.login(person.getUserId())
    instance_tree = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title][0]

    another_instance_title = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == another_instance_title][0]

    return person, compute_node, instance_tree, another_instance_title, service

  def createTioXMLFile(self, contributor_value=None):
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'",
                              attribute='comment'):
      document = self.portal.consumption_document_module.newContent(
        title=self.generateNewId(),
        reference="TESTTIOCONS-%s" % self.generateNewId(),
        contributor_value=contributor_value
      )
      document.submit()
    return document

  def assertWorkflowComment(self, document, message):
    self.assertEqual(message,
        document.workflow_history['slapos_consumption_document_workflow'][-1]['comment'])

  def assertCreatedConsumptionDeliveryLine(self,
         line, title, quantity, aggregate_list, person, service, price=None):

    self.assertEqual(line.getTitle(), title)
    self.assertEqual(line.getQuantity(), quantity)
    self.assertSameSet(line.getAggregateList(), aggregate_list)
    self.assertEqual(line.getDestination(), person.getRelativeUrl())
    self.assertEqual(line.getDestinationDecision(), person.getRelativeUrl())
    self.assertEqual(line.getResource(), service.getRelativeUrl())
    self.assertEqual(line.getQuantityUnit(), "unit/piece")
    self.assertEqual(line.getPrice(), None)

  def generateConsumptionDelivery(self, person, document, tio_dict):
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              tio_dict, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()

    self.assertEqual(document.getValidationState(), "accepted")
    self.assertWorkflowComment(document, "Created Delivery: %s" % result)
    self.assertEqual(len(result), 1)

    delivery = self.portal.restrictedTraverse(result[0])
    self.assertEqual(delivery.getPortalType(), "Consumption Delivery")
    self.assertEqual(delivery.getSourceSection(), None)
    self.assertNotEqual(delivery.getSource(), None)
    self.assertEqual(delivery.getDestination(), person.getRelativeUrl())
    self.assertEqual(delivery.getDestinationDecision(),
                     person.getRelativeUrl())
    self.assertEqual(delivery.getDestinationSection(), person.getRelativeUrl())
    self.assertEqual(delivery.getStartDate(), self._start_date)
    self.assertEqual(delivery.getStopDate(), self._stop_date)
    self.assertEqual(delivery.getTitle(), 'Resource consumptionsé')
    self.assertEqual(delivery.getSimulationState(), "delivered")
    self.assertEqual(delivery.getCausalityState(), "building")
    self.assertNotEqual(delivery.getSpecialise(), None)
    self.assertNotEqual(delivery.getSourceProject(), None)
    self.assertEqual(delivery.getDestinationProject(), None)
    self.assertEqual(document.getFollowUp(), delivery.getSourceProject())
    return delivery


  def generateNewTioDict(self, service, instance, quantity):
    return {
      'title': 'Resource consumptionsé',
      'start_date': self._start_date,
      'stop_date': self._stop_date,
      'movement': [{
        'title': 'fooà',
        'resource': service,
        'reference': instance.getReference(),
        'quantity': quantity,
        'category': "caté",
      }],
    }

  def test_generateConsumptionDelivery_REQUEST_disallowed(self):
    document = self.createTioXMLFile()
    self.assertRaises(
      Unauthorized,
      document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery,
      REQUEST={})

  def test_generateConsumptionDelivery_no_related_compute_node(self):
    document = self.createTioXMLFile()
    self.assertEqual(document.getValidationState(), "submitted")
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              None, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertWorkflowComment(document,
                               'No related Compute Node or Software Instance!')
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_no_data(self):
    _, compute_node, _, _, _ = self.bootstrapGenerateConsumptionDeliveryTest()
    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.assertEqual(document.getValidationState(), "submitted")
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              None, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertEqual("Not usable TioXML data",
        document.workflow_history['slapos_consumption_document_workflow'][-1]['comment'])
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_no_project(self):
    _, compute_node, _, _, _ = self.bootstrapGenerateConsumptionDeliveryTest()
    self.logout()
    self.login()
    # Project is missing for some resason
    compute_node.setFollowUp(None)
    document = self.createTioXMLFile(compute_node)
    self.assertEqual(document.getValidationState(), "submitted")
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              None, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertWorkflowComment(document,
           "Unknown project for %s." % compute_node.getReference())
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_valid_xml_compute_node_future(self):
    _, compute_node, _, _, service = self.bootstrapGenerateConsumptionDeliveryTest()

    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), compute_node, 10.10)
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              tio_dict, attribute='comment'):
      with PinnedDateTime(self, DateTime('2023/12/20')):
        result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertWorkflowComment(document,
      'You cannot invoice future consumption 2024/06/01 00:00:00 UTC')
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_valid_xml_no_reference(self):
    _, compute_node, _, _, service = self.bootstrapGenerateConsumptionDeliveryTest()

    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), compute_node, 10.10)
    del tio_dict['movement'][0]['reference']
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              tio_dict, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertWorkflowComment(document, 'One of Movement has no reference.')
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_valid_xml_compute_unknown_reference(self):
    _, compute_node, _, _, service = self.bootstrapGenerateConsumptionDeliveryTest()

    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), compute_node, 10.10)
    tio_dict['movement'][0]['reference'] = 'RANDOMREF'
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              tio_dict, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertWorkflowComment(document,
                    'Reported consumption for an unknown partition (RANDOMREF)')
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_valid_xml_unknown_reference(self):
    _, compute_node, instance_tree, _, service = \
      self.bootstrapGenerateConsumptionDeliveryTest()

    instance = instance_tree.getSuccessorValue()
    self.logout()
    self.login()
    document = self.createTioXMLFile(instance)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), compute_node, 10.10)
    tio_dict['movement'][0]['reference'] = 'RANDOMREF'
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              tio_dict, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertWorkflowComment(document,
      '%s reported a consumption for RANDOMREF which is not supported.' % \
      (instance.getRelativeUrl()))
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_valid_xml_cross_report(self):
    _, _, instance_tree_a, instance_tree_b, service = self.bootstrapGenerateConsumptionDeliveryTest()

    instance_a = instance_tree_a.getSuccessorValue()
    instance_b = instance_tree_b.getSuccessorValue()

    self.logout()
    self.login()
    document = self.createTioXMLFile(instance_a)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), instance_b, 10.10)
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              tio_dict, attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "rejected")
    self.assertWorkflowComment(document,
      '%s reported a consumption for %s which is not supported.' % \
      (instance_a.getRelativeUrl(),  instance_b.getReference()))
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_valid_xml_compute_node_one_movement(self):
    person, compute_node, _, _, service = self.bootstrapGenerateConsumptionDeliveryTest()

    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")

    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), compute_node, 10.10)
    delivery = self.generateConsumptionDelivery(person, document, tio_dict)

    delivery_line_list = delivery.contentValues(
      portal_type="Consumption Delivery Line")
    self.assertEqual(len(delivery_line_list), 1)
    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[0], "fooà", 10.10, [
        compute_node.getRelativeUrl()
      ], person, service)

  def test_generateConsumptionDelivery_valid_xml_one_movement_instance_reference(self):
    person, compute_node, instance_tree, _, service = \
      self.bootstrapGenerateConsumptionDeliveryTest()

    instance = instance_tree.getSuccessorValue()
    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")

    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), instance, 42.42)
    delivery = self.generateConsumptionDelivery(person, document, tio_dict)

    delivery_line_list = delivery.contentValues(
      portal_type="Consumption Delivery Line")
    self.assertEqual(len(delivery_line_list), 1)
    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[0], "fooà", 42.42, [
        instance.getRelativeUrl(),
        instance_tree.getRelativeUrl()
      ], person, service)

  def test_generateConsumptionDelivery_valid_xml_one_movement_service_reference(self):
    person, compute_node, instance_tree, _, service = \
      self.bootstrapGenerateConsumptionDeliveryTest()

    instance = instance_tree.getSuccessorValue()
    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")

    tio_dict = self.generateNewTioDict(service.getReference(), instance, 42.42)
    delivery = self.generateConsumptionDelivery(person, document, tio_dict)

    delivery_line_list = delivery.contentValues(
      portal_type="Consumption Delivery Line")
    self.assertEqual(len(delivery_line_list), 1)
    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[0], "fooà", 42.42, [
        instance.getRelativeUrl(),
        instance_tree.getRelativeUrl()
      ], person, service)

  def test_generateConsumptionDelivery_valid_xml_slave_instance_reference(self):
    person, compute_node, instance_tree, instance_tree_slave, service = \
      self.bootstrapGenerateConsumptionDeliveryTest(shared=True)

    instance = instance_tree.getSuccessorValue()
    slave_instance = instance_tree_slave.getSuccessorValue()
    self.logout()
    self.login()
    document = self.createTioXMLFile(compute_node)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = {
      'title': 'Resource consumptionsé',
      'start_date': self._start_date,
      'stop_date': self._stop_date,
      'movement': [{
        'title': 'fooà',
        'resource': service.getRelativeUrl(),
        'reference': instance.getReference(),
        'quantity': 42.42,
        'category': "caté",
      }, {
        'title': 'barà',
        'resource': service.getRelativeUrl(),
        'reference': slave_instance.getReference(),
        'quantity': 10.10,
        'category': "caté",
      }]
    }
    delivery = self.generateConsumptionDelivery(person, document, tio_dict)
    delivery_line_list = delivery.contentValues(
      portal_type="Consumption Delivery Line")
    self.assertEqual(len(delivery_line_list), 2)
    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[0], "fooà", 42.42, [
        instance.getRelativeUrl(),
        instance_tree.getRelativeUrl()
      ], person, service)

    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[1], "barà", 10.10, [
        slave_instance.getRelativeUrl(),
        instance_tree_slave.getRelativeUrl()
      ], person, service)

  def test_generateConsumptionDelivery_valid_xml_instance_one_movement(self):
    person, _, _, instance_tree, service = \
                self.bootstrapGenerateConsumptionDeliveryTest()

    instance = instance_tree.getSuccessorValue()
    self.logout()
    self.login()
    document = self.createTioXMLFile(instance)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), instance, 10.10)
    delivery = self.generateConsumptionDelivery(person, document, tio_dict)

    delivery_line_list = delivery.contentValues(
      portal_type="Consumption Delivery Line")
    self.assertEqual(len(delivery_line_list), 1)
    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[0], "fooà", 10.10, [
        instance_tree.getRelativeUrl(),
        instance.getRelativeUrl()
      ], person, service)

  def test_generateConsumptionDelivery_valid_xml_instance_two_movement(self):
    person, _, instance_tree, _ , service = \
       self.bootstrapGenerateConsumptionDeliveryTest()

    instance = instance_tree.getSuccessorValue()

    self.logout()
    self.login()
    document = self.createTioXMLFile(instance)
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    tio_dict = self.generateNewTioDict(service.getRelativeUrl(), instance, 42.42)
    tio_dict['movement'].append({
      'title': 'foob',
      'resource': service.getRelativeUrl(),
      'reference': instance.getReference(),
      'quantity': 24.24,
      'category': "caté",
    })
    delivery = self.generateConsumptionDelivery(person, document, tio_dict)
    delivery_line_list = delivery.contentValues(
      portal_type="Consumption Delivery Line")
    self.assertEqual(len(delivery_line_list), 2)

    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[0], "fooà", 42.42, [
        instance.getRelativeUrl(),
        instance_tree.getRelativeUrl()
      ], person, service)

    self.assertCreatedConsumptionDeliveryLine(
      delivery_line_list[1], "foob", 24.24, [
        instance.getRelativeUrl(),
        instance_tree.getRelativeUrl()
      ], person, service)
