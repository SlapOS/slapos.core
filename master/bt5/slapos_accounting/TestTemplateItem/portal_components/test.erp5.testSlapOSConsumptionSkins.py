# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import TemporaryAlarmScript, \
  SlapOSTestCaseMixinWithAbort, SlapOSTestCaseMixin, simulate

from Products.ERP5Type.Utils import str2bytes
from zExceptions import Unauthorized
from DateTime import DateTime

class TestSlapOSComputeNode_reportComputeNodeConsumption(SlapOSTestCaseMixinWithAbort):

  def test_reportComputeNodeConsumption_REQUEST_disallowed(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    self.assertRaises(
      Unauthorized,
      compute_node.ComputeNode_reportComputeNodeConsumption,
      "foo", "bar",
      REQUEST={})

  def test_reportComputeNodeConsumption_expected_xml(self):
    new_id = self.generateNewId()
    consumption_xml = """<?xml version='1.0' encoding='utf-8'?>
<journal>
<transaction type="Sale Packing List">
<title>Resource consumptions</title>
<start_date></start_date>
<stop_date></stop_date>
<reference>foo</reference>
<currency></currency>
<payment_mode></payment_mode>
<category></category>
<arrow type="Administration">
<source></source>
<destination></destination>
</arrow>
<movement>
<resource>CPU Consumption</resource>
<title>Title Consumption Delivery Line 1</title>
<reference>slappart0</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>None</category>
</movement>
</transaction>
</journal>"""

    compute_node, _ = self._makeComputeNode(self.addProject())
    document_relative_url = compute_node.ComputeNode_reportComputeNodeConsumption(
                                                 new_id, consumption_xml)
    document = self.portal.restrictedTraverse(document_relative_url)
    self.assertEqual(document.getPortalType(),
                      "Computer Consumption TioXML File")
    self.assertEqual(document.getSourceReference(), new_id)
    self.assertEqual(document.getTitle(),
                      "%s consumption (%s)" % (compute_node.getReference(), new_id))
    self.assertNotEqual(document.getReference(), "")
    self.assertEqual(document.getVersion(), "1")
    self.assertEqual(document.getData(), consumption_xml)
    self.assertEqual(document.getClassification(), "personal")
    self.assertEqual(document.getPublicationSection(), "other")
    self.assertEqual(document.getValidationState(), "submitted")
    self.assertEqual(document.getContributor(), compute_node.getRelativeUrl())

  def test_reportComputeNodeConsumption_reported_twice(self):
    new_id = self.generateNewId()
    consumption_xml = """<?xml version='1.0' encoding='utf-8'?>
<journal>
<transaction type="Sale Packing List">
<title>Resource consumptions</title>
<start_date></start_date>
<stop_date></stop_date>
<reference>foo</reference>
<currency></currency>
<payment_mode></payment_mode>
<category></category>
<arrow type="Administration">
<source></source>
<destination></destination>
</arrow>
<movement>
<resource>CPU Consumption</resource>
<title>Title Consumption Delivery Line 1</title>
<reference>slappart0</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>None</category>
</movement>
</transaction>
</journal>"""

    compute_node, _ = self._makeComputeNode(self.addProject())
    document1_relative_url = compute_node.ComputeNode_reportComputeNodeConsumption(
                                                 new_id, consumption_xml)
    document1 = self.portal.restrictedTraverse(document1_relative_url)

    document2_relative_url = compute_node.ComputeNode_reportComputeNodeConsumption(
                                                 new_id, consumption_xml)
    document2 = self.portal.restrictedTraverse(document2_relative_url)

    self.assertEqual(document2.getPortalType(),
                      "Computer Consumption TioXML File")
    self.assertEqual(document2.getSourceReference(),
                      document1.getSourceReference())
    self.assertEqual(document2.getTitle(), document1.getTitle())
    self.assertEqual(document2.getReference(), document1.getReference())
    self.assertEqual(document1.getVersion(), "1")
    self.assertEqual(document2.getVersion(), "2")
    self.assertEqual(document2.getData(), consumption_xml)
    self.assertEqual(document2.getClassification(), "personal")
    self.assertEqual(document2.getPublicationSection(), "other")
    self.assertEqual(document1.getValidationState(), "submitted")
    self.assertEqual(document2.getValidationState(), "submitted")
    self.assertEqual(document2.getContributor(), compute_node.getRelativeUrl())

class TestSlapOSComputerConsumptionTioXMLFile_parseXml(SlapOSTestCaseMixinWithAbort):

  def createTioXMLFile(self):
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'",
                              attribute='comment'):
      document = self.portal.consumption_document_module.newContent(
        title=self.generateNewId(),
        reference="TESTTIOCONS-%s" % self.generateNewId(),
      )
      document.submit()
    return document

  def test_parseXml_REQUEST_disallowed(self):
    document = self.createTioXMLFile()
    self.assertRaises(
      Unauthorized,
      document.ComputerConsumptionTioXMLFile_parseXml,
      REQUEST={})

  def test_parseXml_no_data(self):
    document = self.createTioXMLFile()
    result = document.ComputerConsumptionTioXMLFile_parseXml()
    self.assertEqual(result, None)

  def test_parseXml_no_xml(self):
    document = self.createTioXMLFile()
    document.edit(data=str2bytes("<?xml version='1.0' encoding='utf-8'?><foo></foo>"))
    result = document.ComputerConsumptionTioXMLFile_parseXml()
    self.assertEqual(result, None)

  def test_parseXml_invalid_xml(self):
    document = self.createTioXMLFile()
    document.edit(data=str2bytes("<xml></foo>"))
    result = document.ComputerConsumptionTioXMLFile_parseXml()
    self.assertEqual(result, None)

  def test_parseXml_valid_xml_one_movement(self):
    document = self.createTioXMLFile()
    consumption_xml = """<?xml version='1.0' encoding='utf-8'?>
<journal>
<transaction type="Sale Packing List">
<title>Resource consumptionsé</title>
<start_date>Sun, 06 Nov 1994 08:49:37 GMT</start_date>
<stop_date>Sun, 07 Nov 1994 08:49:37 GMT</stop_date>
<reference>fooé</reference>
<currency></currency>
<payment_mode></payment_mode>
<category></category>
<arrow type="Administration">
<source></source>
<destination></destination>
</arrow>
<movement>
<resource>CPU Consumptioné</resource>
<title>Title Consumption Delivery Line 1</title>
<reference>slappart0é</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>caté</category>
</movement>
</transaction>
</journal>"""
    document.edit(data=str2bytes(consumption_xml))
    result = document.ComputerConsumptionTioXMLFile_parseXml()
    self.assertEqual(result, {
      'title': 'Resource consumptionsé',
      'start_date': DateTime('1994/11/06 08:49:37 GMT'),
      'stop_date': DateTime('1994/11/07 08:49:37 GMT'),
      'movement': [{
        'resource': 'CPU Consumptioné',
        'reference': 'slappart0é',
        'quantity': 42.42,
        'category': "caté",
        'title': "Title Consumption Delivery Line 1",
      }],
    })

  def test_parseXml_valid_xml_two_movements(self):
    document = self.createTioXMLFile()
    consumption_xml = """<?xml version='1.0' encoding='utf-8'?>
<journal>
<transaction type="Sale Packing List">
<title>Resource consumptionsé</title>
<start_date>Sun, 06 Nov 1994 08:49:37 GMT</start_date>
<stop_date>Sun, 07 Nov 1994 08:49:37 GMT</stop_date>
<reference>fooé</reference>
<currency></currency>
<payment_mode></payment_mode>
<category></category>
<arrow type="Administration">
<source></source>
<destination></destination>
</arrow>
<movement>
<resource>CPU Consumptioné</resource>
<title>Title Consumption Delivery Line 1</title>
<reference>slappart0é</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>caté</category>
</movement>
<movement>
<resource>CPU Consumptioné</resource>
<title>Title Consumption Delivery Line 1</title>
<reference>slappart0é</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>caté</category>
</movement>
</transaction>
</journal>"""
    document.edit(data=str2bytes(consumption_xml))
    result = document.ComputerConsumptionTioXMLFile_parseXml()
    self.assertEqual(result, {
      'title': 'Resource consumptionsé',
      'start_date': DateTime('1994/11/06 08:49:37 GMT'),
      'stop_date': DateTime('1994/11/07 08:49:37 GMT'),
      'movement': [{
        'resource': 'CPU Consumptioné',
        'reference': 'slappart0é',
        'quantity': 42.42,
        'category': "caté",
        'title': "Title Sale Packing List Line 1",
        },{
        'resource': 'CPU Consumptioné',
        'reference': 'slappart0é',
        'quantity': 42.42,
        'category': "caté",
        'title': "Title Sale Packing List Line 1",
      }],
    })

class TestSlapOSComputerConsumptionTioXMLFile_generateConsumptionDelivery(
                                                           SlapOSTestCaseMixin):

  def createTioXMLFile(self):
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'",
                              attribute='comment'):
      document = self.portal.consumption_document_module.newContent(
        title=self.generateNewId(),
        reference="TESTTIOCONS-%s" % self.generateNewId(),
      )
      document.submit()
    return document

  def test_generateConsumptionDelivery_REQUEST_disallowed(self):
    document = self.createTioXMLFile()
    self.assertRaises(
      Unauthorized,
      document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery,
      REQUEST={})

  @simulate('ComputerConsumptionTioXMLFile_parseXml',
            '*args, **kwargs',
            'return None')
  def test_generateConsumptionDelivery_no_data(self):
    document = self.createTioXMLFile()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "draft")
    self.assertEqual("Not usable TioXML data",
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(result, [])

  def test_generateConsumptionDelivery_valid_xml_one_movement(self):

    document = self.createTioXMLFile()
    _, _, _, compute_node, partition, instance_tree = \
      self.bootstrapAllocableInstanceTree(
        is_accountable=True, allocation_state='allocated')
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")

    tio_dict = {
      'title': 'Resource consumptionsé',
      'start_date': DateTime('2024/05/01'),
      'stop_date': DateTime('2024/06/01'),
      'movement': [{
        'title': 'fooà',
        'resource': 'service_module/slapos_netdrive_consumption',
        'reference': partition.getReference(),
        'quantity': 42.42,
        'category': "caté",
      }],
    }
    with TemporaryAlarmScript(self.portal, 'ComputerConsumptionTioXMLFile_parseXml',
                              tio_dict,
                              attribute='comment'):
      result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created Delivery: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1, partition.getReference())
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Consumption Delivery")
    self.assertEqual(delivery.getDestination(), self.person.getRelativeUrl())
    self.assertEqual(delivery.getDestinationDecision(),
                     self.person.getRelativeUrl())
    self.assertEqual(delivery.getStartDate(),
                     document.getCreationDate())
    self.assertEqual(delivery.getTitle(), 'Resource consumptionsé')
    self.assertEqual(delivery.getSimulationState(), "delivered")
    self.assertEqual(delivery.getCausalityState(), "building")
    self.assertEqual(delivery.getSpecialise(),
      "sale_trade_condition_module/slapos_consumption_trade_condition")

    self.assertEqual(
      len(delivery.contentValues(portal_type="Consumption Delivery Line")), 1)
    line = delivery.contentValues(portal_type="Consumption Delivery Line")[0]

    self.assertEqual(line.getTitle(), "fooà")
    self.assertEqual(line.getQuantity(), 42.42)
    self.assertEqual(line.getPrice(), 0)
    self.assertEqual(line.getAggregateList(), [
      self.compute_node.partition1.getRelativeUrl(),
      self.start_requested_software_instance.getRelativeUrl(),
      self.start_requested_software_instance.getSpecialise()
    ])
    self.assertEqual(line.getResource(),
                     "service_module/slapos_netdrive_consumption")
    self.assertEqual(line.getQuantityUnit(),
                     "unit/piece")

  tio_dict = {
    'title': 'Resource consumptionsé',
    'start_date': DateTime('2024/05/01'),
    'stop_date': DateTime('2024/06/01'),
    'movement': [{
      'title': 'fooà',
      'resource': 'service_module/slapos_netdrive_consumption',
      'reference': 'partition2',
      'quantity': 42.42,
      'category': "caté",
    }],
  }

  @simulate('ComputerConsumptionTioXMLFile_parseXml',
            '*args, **kwargs',
            "return %s" % tio_dict)
  def xtest_generateConsumptionDelivery_valid_xml_one_movement_partition2(self):
    document = self.createTioXMLFile()
    _, _, _, compute_node, partition, instance_tree = \
      self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created Delivery: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1)
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Consumption Delivery")
    self.assertEqual(delivery.getDestination(), self.person.getRelativeUrl())
    self.assertEqual(delivery.getDestinationDecision(),
                     self.person.getRelativeUrl())
    self.assertEqual(delivery.getStartDate(),
                     document.getCreationDate())
    self.assertEqual(delivery.getTitle(), 'Resource consumptionsé')
    self.assertEqual(delivery.getSimulationState(), "delivered")
    self.assertEqual(delivery.getCausalityState(), "building")
    self.assertEqual(delivery.getSpecialise(),
      "sale_trade_condition_module/slapos_consumption_trade_condition")

    self.assertEqual(
      len(delivery.contentValues(portal_type="Consumption Delivery Line")), 1)
    line = delivery.contentValues(portal_type="Consumption Delivery Line")[0]

    self.assertEqual(line.getTitle(), "fooà")
    self.assertEqual(line.getQuantity(), 42.42)
    self.assertEqual(line.getPrice(), 0)
    self.assertEqual(line.getAggregateList(), [
      self.compute_node.partition2.getRelativeUrl(),
      self.stop_requested_software_instance.getRelativeUrl(),
      self.stop_requested_software_instance.getSpecialise()
    ])
    self.assertEqual(line.getDestination(), self.second_person.getRelativeUrl())
    self.assertEqual(line.getDestinationDecision(),
                     self.second_person.getRelativeUrl())
    self.assertEqual(line.getResource(),
                     "service_module/slapos_netdrive_consumption")
    self.assertEqual(line.getQuantityUnit(),
                     "unit/piece")

  tio_dict = {
    'title': 'Resource consumptionsé',
    'start_date': DateTime('2024/05/01'),
    'stop_date': DateTime('2024/06/01'),
    'movement': [{
      'title': 'fooà',
      'resource': 'service_module/slapos_netdrive_consumption',
      'reference': 'partition1',
      'quantity': 42.42,
      'category': "caté",
      },{
      'title': 'foob',
      'resource': 'service_module/slapos_netdrive_consumption',
      'reference': 'partition1',
      'quantity': 24.24,
      'category': "caté",
    }],
  }

  @simulate('ComputerConsumptionTioXMLFile_parseXml',
            '*args, **kwargs',
            "return %s" % tio_dict)
  def test_generateConsumptionDelivery_valid_xml_two_movement(self):
    document = self.createTioXMLFile()
    compute_node = self.createAllocatedComputeNode()
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created Delivery: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1)
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Consumption Delivery")
    self.assertEqual(delivery.getDestination(), self.person.getRelativeUrl())
    self.assertEqual(delivery.getDestinationDecision(),
                     self.person.getRelativeUrl())
    self.assertEqual(delivery.getStartDate(),
                     document.getCreationDate())
    self.assertEqual(delivery.getTitle(), 'Resource consumptionsé')
    self.assertEqual(delivery.getSimulationState(), "delivered")
    self.assertEqual(delivery.getCausalityState(), "building")
    self.assertEqual(delivery.getSpecialise(), 
      "sale_trade_condition_module/slapos_consumption_trade_condition")

    self.assertEqual(
      len(delivery.contentValues(portal_type="Consumption Delivery Line")), 2)

    line = delivery.contentValues(portal_type="Consumption Delivery Line")[0]
    self.assertEqual(line.getTitle(), "fooà")
    self.assertEqual(line.getQuantity(), 42.42)
    self.assertEqual(line.getAggregateList(), [
      self.compute_node.partition1.getRelativeUrl(),
      self.start_requested_software_instance.getRelativeUrl(),
      self.start_requested_software_instance.getSpecialise()
    ])
    self.assertEqual(line.getDestination(), self.person.getRelativeUrl())
    self.assertEqual(line.getDestinationDecision(),
                     self.person.getRelativeUrl())
    self.assertEqual(line.getResource(),
                     "service_module/slapos_netdrive_consumption")
    self.assertEqual(line.getQuantityUnit(),
                     "unit/piece")

    line = delivery.contentValues(portal_type="Consumption Delivery Line")[1]
    self.assertEqual(line.getTitle(), "foob")
    self.assertEqual(line.getQuantity(), 24.24)
    self.assertEqual(line.getAggregateList(), [
      self.compute_node.partition1.getRelativeUrl(),
      self.start_requested_software_instance.getRelativeUrl(),
      self.start_requested_software_instance.getSpecialise()
    ])
    self.assertEqual(line.getDestination(), self.person.getRelativeUrl())
    self.assertEqual(line.getDestinationDecision(),
                     self.person.getRelativeUrl())
    self.assertEqual(line.getResource(),
                     "service_module/slapos_netdrive_consumption")
    self.assertEqual(line.getQuantityUnit(),
                     "unit/piece")

  tio_dict = {
    'title': 'Resource consumptionsé',
    'movement': [{
      'title': 'fooà',
      'resource': 'service_module/slapos_netdrive_consumption',
      'reference': 'partition1',
      'quantity': 42.42,
      'category': "caté",
      },{
      'title': 'foob',
      'resource': 'service_module/slapos_netdrive_consumption',
      'reference': 'partition2',
      'quantity': 24.24,
      'category': "caté",
    }],
  }

  @simulate('ComputerConsumptionTioXMLFile_parseXml', 
            '*args, **kwargs',
            "return %s" % tio_dict)
  def test_generateConsumptionDelivery_valid_xml_two_partitions(self):
    document = self.createTioXMLFile()
    compute_node = self.createAllocatedComputeNode()
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_generateConsumptionDelivery()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created Delivery: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1)

    # One Delivery
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Consumption Delivery")
    self.assertEqual(delivery.getDestination(), self.person.getRelativeUrl())
    self.assertEqual(delivery.getDestinationDecision(),
                     self.person.getRelativeUrl())
    self.assertEqual(delivery.getStartDate(),
                     document.getCreationDate())
    self.assertEqual(delivery.getTitle(), 'Resource consumptionsé')
    self.assertEqual(delivery.getSimulationState(), "delivered")
    self.assertEqual(delivery.getCausalityState(), "building")
    self.assertEqual(delivery.getSpecialise(),
      "sale_trade_condition_module/slapos_consumption_trade_condition")

    self.assertEqual(
      len(delivery.contentValues(portal_type="Consumption Delivery Line")), 2)

    # Consumption Delivery Line 1
    line1 = delivery.contentValues(portal_type="Consumption Delivery Line")[0]
    self.assertEqual(line1.getTitle(), "fooà")
    self.assertEqual(line1.getQuantity(), 42.42)
    self.assertEqual(line1.getAggregateList(), [
      self.compute_node.partition1.getRelativeUrl(),
      self.start_requested_software_instance.getRelativeUrl(),
      self.start_requested_software_instance.getSpecialise()
    ])
    self.assertEqual(line1.getDestination(), self.person.getRelativeUrl())
    self.assertEqual(line1.getDestinationDecision(),
                     self.person.getRelativeUrl())
    self.assertEqual(line1.getResource(),
                     "service_module/slapos_netdrive_consumption")
    self.assertEqual(line1.getQuantityUnit(),
                     "unit/piece")

    # Consumption Delivery Line 2
    line2 = delivery.contentValues(portal_type="Consumption Delivery Line")[1]

    self.assertEqual(line2.getTitle(), "foob")
    self.assertEqual(line2.getQuantity(), 24.24)
    self.assertEqual(line2.getAggregateList(), [
      self.compute_node.partition2.getRelativeUrl(),
      self.stop_requested_software_instance.getRelativeUrl(),
      self.stop_requested_software_instance.getSpecialise()
    ])
    self.assertEqual(line2.getDestination(), self.second_person.getRelativeUrl())
    self.assertEqual(line2.getDestinationDecision(),
                     self.second_person.getRelativeUrl())
    self.assertEqual(line2.getResource(),
                     "service_module/slapos_netdrive_consumption")
    self.assertEqual(line2.getQuantityUnit(),
                     "unit/piece")
