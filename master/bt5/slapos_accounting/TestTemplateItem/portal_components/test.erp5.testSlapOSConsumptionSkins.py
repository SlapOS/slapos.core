# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import TemporaryAlarmScript, \
  SlapOSTestCaseMixinWithAbort

from Products.ERP5Type.Utils import str2bytes, bytes2str
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
    self.assertEqual(bytes2str(document2.getData()), consumption_xml)
    self.assertEqual(document2.getClassification(), "personal")
    self.assertEqual(document2.getPublicationSection(), "other")
    self.assertEqual(document1.getValidationState(), "submitted")
    self.assertEqual(document2.getValidationState(), "submitted")
    self.assertEqual(document2.getContributor(), compute_node.getRelativeUrl())

class TestSlapOSComputerConsumptionTioXMLFile_parseXml(SlapOSTestCaseMixinWithAbort):

  maxDiff = None
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
        'title': "Title Consumption Delivery Line 1",
        },{
        'resource': 'CPU Consumptioné',
        'reference': 'slappart0é',
        'quantity': 42.42,
        'category': "caté",
        'title': "Title Consumption Delivery Line 1",
      }],
    })

