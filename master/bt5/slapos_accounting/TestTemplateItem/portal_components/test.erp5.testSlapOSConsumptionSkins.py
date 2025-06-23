# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixinWithAbort, SlapOSTestCaseMixin, simulate

from Products.ERP5Type.Utils import str2bytes, bytes2str
from zExceptions import Unauthorized
from unittest import expectedFailure

class TestSlapOSComputeNode_reportComputeNodeConsumption(SlapOSTestCaseMixinWithAbort):

  def createComputeNode(self):
    new_id = self.generateNewId()
    return self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title="Compute Node %s" % new_id,
      reference="TESTCOMP-%s" % new_id,
      )

  def test_reportComputeNodeConsumption_REQUEST_disallowed(self):
    compute_node = self.createComputeNode()
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
<title>Title Sale Packing List Line 1</title>
<reference>slappart0</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>None</category>
</movement>
</transaction>
</journal>"""

    compute_node = self.createComputeNode()
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
    self.assertEqual(bytes2str(document.getData()), consumption_xml)
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
<title>Title Sale Packing List Line 1</title>
<reference>slappart0</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>None</category>
</movement>
</transaction>
</journal>"""

    compute_node = self.createComputeNode()
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
    self.assertEqual(bytes2str(document2.getData()), consumption_xml)
    self.assertEqual(document2.getClassification(), "personal")
    self.assertEqual(document2.getPublicationSection(), "other")
    self.assertEqual(document1.getValidationState(), "submitted")
    self.assertEqual(document2.getValidationState(), "submitted")
    self.assertEqual(document2.getContributor(), compute_node.getRelativeUrl())

class TestSlapOSComputerConsumptionTioXMLFile_parseXml(SlapOSTestCaseMixinWithAbort):

  def createTioXMLFile(self):
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
<title>Title Sale Packing List Line 1</title>
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
      'movement': [{
        'resource': 'CPU Consumptioné',
        'reference': 'slappart0é',
        'quantity': 42.42,
        'category': "caté",
        'title': "Title Sale Packing List Line 1",
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
<title>Title Sale Packing List Line 1</title>
<reference>slappart0é</reference>
<quantity>42.42</quantity>
<price>0.00</price>
<VAT>None</VAT>
<category>caté</category>
</movement>
<movement>
<resource>CPU Consumptioné</resource>
<title>Title Sale Packing List Line 1</title>
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

class TestSlapOSComputerConsumptionTioXMLFile_solveInvoicingGeneration(
                                                           SlapOSTestCaseMixin):

  def createTioXMLFile(self):
    document = self.portal.consumption_document_module.newContent(
      title=self.generateNewId(),
      reference="TESTTIOCONS-%s" % self.generateNewId(),
    )
    document.submit()
    return document

  def createAllocatedComputeNode(self):
    project = self.addProject()

    # Create person
    reference = 'test_%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
      title=reference,
      reference=reference)
    person.newContent(
      portal_type='Assignment',
      function='customer',
      destination_project_value=project
    ).open()

    # Create second person
    reference = 'test_%s' % self.generateNewId()
    second_person = self.portal.person_module.newContent(portal_type='Person',
      title=reference,
      reference=reference)
    second_person.newContent(
      portal_type='Assignment',
      function='customer',
      destination_project_value=project
    ).open()

    self.commit()
    self.person = person
    self.person_reference = person.getReference()
    self.second_person = second_person
    self.second_person_reference = second_person.getReference()

    new_id = self.generateNewId()

    # Prepare compute_node
    self.compute_node = self.createComputeNode()
    self.compute_node.edit(
      title="Compute Node %s" % new_id,
      reference="TESTCOMP-%s" % new_id,
      follow_up_value=project
    )

    self.compute_node.validate()

    self.tic()

    self._makeComplexComputeNode(project)
    self.tic()

    self.start_requested_software_instance.getSpecialiseValue().edit(
      destination_section_value=person
    )

    self.stop_requested_software_instance.getSpecialiseValue().edit(
      destination_section_value=second_person
    )
    
    return self.compute_node

  @expectedFailure
  def test_solveInvoicingGeneration_REQUEST_disallowed(self):
    document = self.createTioXMLFile()
    self.assertRaises(
      Unauthorized,
      document.ComputerConsumptionTioXMLFile_solveInvoicingGeneration,
      REQUEST={})

  @expectedFailure
  @simulate('ComputerConsumptionTioXMLFile_parseXml', 
            '*args, **kwargs',
            'return None')
  def test_solveInvoicingGeneration_no_data(self):
    document = self.createTioXMLFile()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_solveInvoicingGeneration()
    self.assertEqual(document.getValidationState(), "draft")
    self.assertEqual("Not usable TioXML data",
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(result, [])

  tio_dict = {
    'title': 'Resource consumptionsé',
    'movement': [{
      'title': 'fooà',
      'resource': 'service_module/slapos_netdrive_consumption',
      'reference': 'partition1',
      'quantity': 42.42,
      'category': "caté",
    }],
  }
  @expectedFailure
  @simulate('ComputerConsumptionTioXMLFile_parseXml', 
            '*args, **kwargs',
            "return %s" % tio_dict)
  def test_solveInvoicingGeneration_valid_xml_one_movement(self):
    document = self.createTioXMLFile()
    compute_node = self.createAllocatedComputeNode()
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_solveInvoicingGeneration()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created packing list: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1)
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Sale Packing List")
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
      len(delivery.contentValues(portal_type="Sale Packing List Line")), 1)
    line = delivery.contentValues(portal_type="Sale Packing List Line")[0]
    
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
    'movement': [{
      'title': 'fooà',
      'resource': 'service_module/slapos_netdrive_consumption',
      'reference': 'partition2',
      'quantity': 42.42,
      'category': "caté",
    }],
  }
  @expectedFailure
  @simulate('ComputerConsumptionTioXMLFile_parseXml', 
            '*args, **kwargs',
            "return %s" % tio_dict)
  def test_solveInvoicingGeneration_valid_xml_one_movement_partition2(self):
    document = self.createTioXMLFile()
    compute_node = self.createAllocatedComputeNode()
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_solveInvoicingGeneration()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created packing list: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1)
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Sale Packing List")
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
      len(delivery.contentValues(portal_type="Sale Packing List Line")), 1)
    line = delivery.contentValues(portal_type="Sale Packing List Line")[0]
    
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
  @expectedFailure
  @simulate('ComputerConsumptionTioXMLFile_parseXml', 
            '*args, **kwargs',
            "return %s" % tio_dict)
  def test_solveInvoicingGeneration_valid_xml_two_movement(self):
    document = self.createTioXMLFile()
    compute_node = self.createAllocatedComputeNode()
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_solveInvoicingGeneration()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created packing list: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1)
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Sale Packing List")
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
      len(delivery.contentValues(portal_type="Sale Packing List Line")), 2)

    line = delivery.contentValues(portal_type="Sale Packing List Line")[0]
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

    line = delivery.contentValues(portal_type="Sale Packing List Line")[1]
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
  @expectedFailure
  @simulate('ComputerConsumptionTioXMLFile_parseXml', 
            '*args, **kwargs',
            "return %s" % tio_dict)
  def test_solveInvoicingGeneration_valid_xml_two_partitions(self):
    document = self.createTioXMLFile()
    compute_node = self.createAllocatedComputeNode()
    document.edit(
      contributor_value=compute_node,
    )
    self.tic()
    self.assertEqual(document.getValidationState(), "submitted")
    result = document.ComputerConsumptionTioXMLFile_solveInvoicingGeneration()
    self.assertEqual(document.getValidationState(), "shared")
    self.assertEqual("Created packing list: %s" % result,
        document.workflow_history['document_publication_workflow'][-1]['comment'])
    self.assertEqual(len(result), 1)

    # One Delivery
    delivery = self.portal.restrictedTraverse(result[0])

    self.assertEqual(delivery.getPortalType(), "Sale Packing List")
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
      len(delivery.contentValues(portal_type="Sale Packing List Line")), 2)

    # Sale Packing List Line 1
    line1 = delivery.contentValues(portal_type="Sale Packing List Line")[0]
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

    # Sale Packing List Line 2
    line2 = delivery.contentValues(portal_type="Sale Packing List Line")[1]
    
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
