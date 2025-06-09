# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from Products.ERP5Type.Core.Workflow import ValidationFailed
from Products.ERP5Type.Utils import str2bytes, str2unicode
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, \
                                                    TemporaryAlarmScript, \
                                                    SlapOSTestCaseMixinWithAbort
from DateTime import DateTime
from App.Common import rfc1123_date
import json
import hashlib
from binascii import hexlify
from lxml import etree
import transaction

BACKSPACE_CHAR = "\x08"
BELL_CHAR = "\x07"
HORIZONTAL_TAB_CHAR = "\x09"

def hashData(data):
  return hexlify(hashlib.sha1(str2bytes(json.dumps(data, sort_keys=True))).digest())

def _decode_with_json(value):
  # Ensure value is serisalisable as json
  return json.loads(json.dumps(value))

class TestSlapOSCloudSlapOSCacheMixin(
    SlapOSTestCaseMixin):

  require_certificate = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.pinDateTime(DateTime())
    project = self.addProject()
    self._makeComputeNode(project)
    self._makeComplexComputeNode(project, with_slave=True)
    self.tic()

  def beforeTearDown(self):
    self.unpinDateTime()
    self._cleaupREQUEST()

  def test_LastData(self):
    value = "XXX"
    self.assertEqual(None, self.compute_node.getLastData())
    self.compute_node.setLastData(value)
    self.assertEqual(value, self.compute_node.getLastData())
    key = "OI"
    value_key = "ABC"
    self.assertEqual(None, self.compute_node.getLastData(key))
    self.compute_node.setLastData(value_key, key=key)
    self.assertEqual(value_key, self.compute_node.getLastData(key))

  def test_getAccessStatus_no_data(self):
    since = rfc1123_date(DateTime())
    created_at = since
    def getBaseExpectedDict(doc):
      return {
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "SlapOS Master",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#error no data found for %s" % doc.getReference(),
          "no_data": 1
        }

    # Check Compute Node
    self.assertEqual(self.compute_node._getCachedAccessInfo(), None)
    self.assertEqual(self.compute_node.getAccessStatus(),
                     getBaseExpectedDict(self.compute_node))

    # Check Software Installation
    installation = self.start_requested_software_installation
    self.assertEqual(installation._getCachedAccessInfo(), None)
    self.assertEqual(installation.getAccessStatus(),
                     getBaseExpectedDict(installation))   

    partition = self.compute_node.partition1
    self.assertEqual(partition._getCachedAccessInfo(), None)
    self.assertEqual(partition.getAccessStatus(),
                     getBaseExpectedDict(partition))  

    instance = self.start_requested_software_instance
    self.assertEqual(instance._getCachedAccessInfo(), None)
    self.assertEqual(instance.getAccessStatus(),
                     getBaseExpectedDict(instance))  

  def test_setAccessStatus(self):
    since = rfc1123_date(DateTime())
    created_at = since

    def getExpectedCacheDict(doc):
      return json.dumps({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#access TEST123 %s" % doc.getUid()
        },
        sort_keys=True,
      )
    def getBaseExpectedDict(doc):
      return _decode_with_json({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#access TEST123 %s" % doc.getUid(),
          'no_data_since_15_minutes': 0,
          'no_data_since_5_minutes': 0
        })

    # Check Compute Node
    self.assertEqual(True,
      self.compute_node.setAccessStatus("TEST123 %s" % self.compute_node.getUid()))
    self.assertEqual(self.compute_node._getCachedAccessInfo(),
                         getExpectedCacheDict(self.compute_node))
    self.assertEqual(_decode_with_json(self.compute_node.getAccessStatus()),
                     getBaseExpectedDict(self.compute_node))
    self.assertEqual(False,
      self.compute_node.setAccessStatus("TEST123 %s" % self.compute_node.getUid()))

    # Check Software Installation
    installation = self.start_requested_software_installation
    self.assertEqual(True,
      installation.setAccessStatus("TEST123 %s" % installation.getUid()))
    self.assertEqual(installation._getCachedAccessInfo(),
                         getExpectedCacheDict(installation))
    self.assertEqual(_decode_with_json(installation.getAccessStatus()),
                     getBaseExpectedDict(installation))   
    self.assertEqual(False,
      installation.setAccessStatus("TEST123 %s" % installation.getUid()))

    # Compute Partition
    partition = self.compute_node.partition1
    self.assertEqual(True,
      partition.setAccessStatus("TEST123 %s" % partition.getUid()))
    self.assertEqual(partition._getCachedAccessInfo(),
                         getExpectedCacheDict(partition))
    self.assertEqual(_decode_with_json(partition.getAccessStatus()),
                     getBaseExpectedDict(partition))  
    self.assertEqual(False,
      partition.setAccessStatus("TEST123 %s" % partition.getUid()))

    # Software Instance
    instance = self.start_requested_software_instance
    # This is already called from elsewhere, so it actually changed
    self.assertEqual(True,
      instance.setAccessStatus("TEST123 %s" % instance.getUid()))
    self.assertEqual(instance._getCachedAccessInfo(),
                         getExpectedCacheDict(instance))
    self.assertEqual(_decode_with_json(instance.getAccessStatus()),
                     getBaseExpectedDict(instance))  
    self.assertEqual(False,
      instance.setAccessStatus("TEST123 %s" % instance.getUid()))


  def test_setAccessStatus_reindex(self):
    since = rfc1123_date(DateTime())
    created_at = since

    def getExpectedCacheDict(doc):
      return json.dumps({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#access TEST123 %s" % doc.getUid()
        },
        sort_keys=True,
      )
    def getBaseExpectedDict(doc):
      return _decode_with_json({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#access TEST123 %s" % doc.getUid(),
          'no_data_since_15_minutes': 0,
          'no_data_since_5_minutes': 0
        })

    self.tic()


    # Software Instance
    instance = self.start_requested_software_instance
    indexation_timestamp = self.portal.portal_catalog(
      uid=instance.getUid(),
      select_dict={"indexation_timestamp": None}
    )[0].indexation_timestamp

    # This is already called from elsewhere, so it actually changed
    self.assertEqual(True,
      instance.setAccessStatus("TEST123 %s" % instance.getUid()))
    self.assertEqual(instance._getCachedAccessInfo(),
                         getExpectedCacheDict(instance))
    self.assertEqual(_decode_with_json(instance.getAccessStatus()),
                     getBaseExpectedDict(instance))
    self.tic()
    new_indexation_timestamp = self.portal.portal_catalog(
      uid=instance.getUid(),
      select_dict={"indexation_timestamp": None}
    )[0].indexation_timestamp
    self.assertEqual(new_indexation_timestamp, indexation_timestamp)
    self.assertEqual(False,
      instance.setAccessStatus("TEST123 %s" % instance.getUid()))

    self.tic()
    new_indexation_timestamp = self.portal.portal_catalog(
      uid=instance.getUid(),
      select_dict={"indexation_timestamp": None}
    )[0].indexation_timestamp
    self.assertEqual(new_indexation_timestamp, indexation_timestamp)


    self.assertEqual(False,
      instance.setAccessStatus("TEST123 %s" % instance.getUid(), reindex=1))
    self.tic()
    new_indexation_timestamp = self.portal.portal_catalog(
      uid=instance.getUid(),
      select_dict={"indexation_timestamp": None}
    )[0].indexation_timestamp
    self.assertEqual(new_indexation_timestamp, indexation_timestamp)

    self.assertEqual(True,
      instance.setErrorStatus("TEST123 %s" % instance.getUid(), reindex=1))
    self.tic()
    new_indexation_timestamp = self.portal.portal_catalog(
      uid=instance.getUid(),
      select_dict={"indexation_timestamp": None}
    )[0].indexation_timestamp
    self.assertNotEqual(new_indexation_timestamp, indexation_timestamp)


  def test_setErrorStatus(self):
    since = rfc1123_date(DateTime())
    created_at = since

    def getExpectedCacheDict(doc):
      return json.dumps({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#error TEST123 %s" % doc.getUid()
        },
        sort_keys=True,
      )
    def getBaseExpectedDict(doc):
      return _decode_with_json({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#error TEST123 %s" % doc.getUid(),
          'no_data_since_15_minutes': 0,
          'no_data_since_5_minutes': 0
        })

    # Check Compute Node
    self.assertEqual(True,
      self.compute_node.setErrorStatus("TEST123 %s" % self.compute_node.getUid()))
    self.assertEqual(self.compute_node._getCachedAccessInfo(),
                         getExpectedCacheDict(self.compute_node))
    self.assertEqual(_decode_with_json(self.compute_node.getAccessStatus()),
                     getBaseExpectedDict(self.compute_node))
    self.assertEqual(False,
      self.compute_node.setErrorStatus("TEST123 %s" % self.compute_node.getUid()))

    # Check Software Installation
    installation = self.start_requested_software_installation
    self.assertEqual(True,
      installation.setErrorStatus("TEST123 %s" % installation.getUid()))
    self.assertEqual(installation._getCachedAccessInfo(),
                         getExpectedCacheDict(installation))
    self.assertEqual(_decode_with_json(installation.getAccessStatus()),
                     getBaseExpectedDict(installation))   
    self.assertEqual(False,
      installation.setErrorStatus("TEST123 %s" % installation.getUid()))

    # Compute Partition
    partition = self.compute_node.partition1
    self.assertEqual(True,
      partition.setErrorStatus("TEST123 %s" % partition.getUid()))
    self.assertEqual(partition._getCachedAccessInfo(),
                         getExpectedCacheDict(partition))
    self.assertEqual(_decode_with_json(partition.getAccessStatus()),
                     getBaseExpectedDict(partition))  
    self.assertEqual(False,
      partition.setErrorStatus("TEST123 %s" % partition.getUid()))

    # Software Instance
    instance = self.start_requested_software_instance
    self.assertEqual(True,
      instance.setErrorStatus("TEST123 %s" % instance.getUid()))
    self.assertEqual(instance._getCachedAccessInfo(),
                         getExpectedCacheDict(instance))
    self.assertEqual(_decode_with_json(instance.getAccessStatus()),
                     getBaseExpectedDict(instance))  
    self.assertEqual(False,
      instance.setErrorStatus("TEST123 %s" % instance.getUid()))


  def test_setBuildingStatus(self):
    since = rfc1123_date(DateTime())
    created_at = since

    def getExpectedCacheDict(doc):
      return json.dumps({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text": "#building TEST123 %s" % doc.getUid()
        },
        sort_keys=True,
      )
    def getBaseExpectedDict(doc):
      return _decode_with_json({
          "portal_type": doc.getPortalType(),
          "reference": doc.getReference(),
          "user": "ERP5TypeTestCase",
          'created_at': '%s' % created_at,
          'since': '%s' % since,
          'state': "",
          "text":  "#building TEST123 %s" % doc.getUid(),
          'no_data_since_15_minutes': 0,
          'no_data_since_5_minutes': 0
        })

    # Check Software Installation
    installation = self.start_requested_software_installation
    self.assertEqual(True,
      installation.setBuildingStatus("TEST123 %s" % installation.getUid()))
    self.assertEqual(installation._getCachedAccessInfo(),
                         getExpectedCacheDict(installation))
    self.assertEqual(_decode_with_json(installation.getAccessStatus()),
                     getBaseExpectedDict(installation))
    self.assertEqual(False,
      installation.setBuildingStatus("TEST123 %s" % installation.getUid()))

class TestBase_isValidXmlMarshaller(SlapOSTestCaseMixinWithAbort):
  def test_Base_isValidXmlMarshaller(self):
    self.assertTrue(self.portal.Base_isValidXmlMarshaller("""<instance/>"""))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller("""<instance></instance>"""))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller("""<instance>"""))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller(""))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller("""<insta"""))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller({HORIZONTAL_TAB_CHAR: 1}))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller([HORIZONTAL_TAB_CHAR, 1]))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller(HORIZONTAL_TAB_CHAR))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller({'zz': {'aa'}}))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller({}))
    self.assertTrue(self.portal.Base_isValidXmlMarshaller(1))

    self.assertRaises(ValueError,
      self.portal.Base_isValidXmlMarshaller,
      "<instance>%s</instance>" % BACKSPACE_CHAR)
    self.assertRaises(ValueError,
       self.portal.Base_isValidXmlMarshaller, BACKSPACE_CHAR)
    self.assertRaises(ValueError,
      self.portal.Base_isValidXmlMarshaller, {BACKSPACE_CHAR: 1})
    self.assertRaises(ValueError,
      self.portal.Base_isValidXmlMarshaller, [BACKSPACE_CHAR, 1])
    self.assertRaises(ValueError,
      self.portal.Base_isValidXmlMarshaller, BELL_CHAR)
    self.assertRaises(ValueError,
      self.portal.Base_isValidXmlMarshaller, {BELL_CHAR: 1})
    self.assertRaises(ValueError,
      self.portal.Base_isValidXmlMarshaller, [BELL_CHAR, 1])

class TestBase_isValidXml(SlapOSTestCaseMixinWithAbort):

  def test_Base_isValidXml(self):
    self.assertTrue(self.portal.Base_isValidXml("<instance/>"))
    self.assertTrue(self.portal.Base_isValidXml("<instance></instance>"))
    self.assertTrue(
      self.portal.Base_isValidXml("<instance>%s</instance>" % HORIZONTAL_TAB_CHAR))

    self.assertRaises(etree.XMLSyntaxError, self.portal.Base_isValidXml, "<instance>")
    self.assertRaises(etree.XMLSyntaxError, self.portal.Base_isValidXml, "")
    self.assertRaises(ValueError, self.portal.Base_isValidXml, None)
    self.assertRaises(etree.XMLSyntaxError, self.portal.Base_isValidXml, "<insta")

    self.assertRaises(etree.XMLSyntaxError, self.portal.Base_isValidXml,
                      "<instance>%s</instance>" % BACKSPACE_CHAR)


class TestSlapOSCloudSoftwareInstance(
    SlapOSTestCaseMixin):

  require_certificate = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()
    self.tic()
    self.instance_tree = self.addInstanceTree(self.project)
    self.software_instance = self.instance_tree.getSuccessorValue()
    self.tic()

  def test_getXmlAsDict(self):
    simple_parameter_sample_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é</parameter>
</instance>
"""
    self.assertEqual(
      self.software_instance._getXmlAsDict(simple_parameter_sample_xml),
      {'p1é': 'v1é', 'p2é': 'v2é'})

  def test_getXmlAsDict_invalid_backspace_char(self):
    simple_parameter_sample_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é%(bs)s">v1é%(bs)s</parameter>
  <parameter id="p2é%(bs)s">v2é%(bs)s</parameter>
</instance>
""" % {'bs' : BACKSPACE_CHAR}
    self.assertRaises(etree.XMLSyntaxError,
        self.software_instance._getXmlAsDict, simple_parameter_sample_xml)

  def test_getInstanceXmlAsDict(self):
    self.software_instance.setTextContent("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é</parameter>
</instance>
""")
    self.assertEqual(
      self.software_instance.getInstanceXmlAsDict(),
      {'p1é': 'v1é', 'p2é': 'v2é'})

    # Ensure SoftwareInstanceConstraint catches eventual the problems.
    self.assertEqual(self.software_instance.checkConsistency(), [])

  def test_getInstanceXmlAsDict_invalid_backspace_char(self):
    self.software_instance.setTextContent("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é%(bs)s">v1é</parameter>
  <parameter id="p2é">v2é%(bs)s</parameter>
</instance>
""" % {'bs' : BACKSPACE_CHAR})
    self.assertRaises(etree.XMLSyntaxError,
      self.software_instance.getInstanceXmlAsDict)

    # Ensure SoftwareInstanceConstraint catches eventual the problems.
    consistency_list = self.software_instance.checkConsistency()
    self.assertEqual(len(consistency_list), 1, consistency_list)
    self.assertTrue(
      str(consistency_list[0].getTranslatedMessage()).startswith(
        'Instance XML is invalid: invalid character'), consistency_list)

  def test_getSlaXmlAsDict(self):
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é</parameter>
</instance>
""")
    self.assertEqual(
      self.software_instance.getSlaXmlAsDict(),
      {'p1é': 'v1é', 'p2é': 'v2é'})

    # Ensure SoftwareInstanceConstraint catches eventual the problems.
    self.assertEqual(self.software_instance.checkConsistency(), [])

  def test_getSlaXmlAsDict_invalid_backspace_char(self):
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é%(bs)s</parameter>
</instance>
""" % {'bs' : BACKSPACE_CHAR})
    self.assertRaises(etree.XMLSyntaxError,
      self.software_instance.getSlaXmlAsDict)

    # Ensure SoftwareInstanceConstraint catches eventual the problems.
    consistency_list = self.software_instance.checkConsistency()
    self.assertEqual(len(consistency_list), 1, consistency_list)
    self.assertTrue(
      str(consistency_list[0].getTranslatedMessage()).startswith(
        'Sla XML is invalid: PCDATA invalid Char value'), consistency_list)

  def test_getConnectionXmlAsDict(self):
    self.software_instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é</parameter>
</instance>
""")
    self.assertEqual(
      self.software_instance.getConnectionXmlAsDict(),
      {'p1é': 'v1é', 'p2é': 'v2é'})

    # Ensure SoftwareInstanceConstraint catches eventual the problems.
    self.assertEqual(self.software_instance.checkConsistency(), [])

  def test_getConnectionXmlAsDict_invalid_backspace_char(self):
    self.software_instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é%(bs)s</parameter>
</instance>
""" % {'bs' : BACKSPACE_CHAR})
    self.assertRaises(etree.XMLSyntaxError,
      self.software_instance.getConnectionXmlAsDict)

    # Ensure SoftwareInstanceConstraint catches eventual the problems.
    consistency_list = self.software_instance.checkConsistency()
    self.assertEqual(len(consistency_list), 1, consistency_list)
    self.assertTrue(
      str(consistency_list[0].getTranslatedMessage()).startswith(
        'Connection XML is invalid: PCDATA invalid Char value'),
      consistency_list)

  def test_getTitle_invalid_backspace_char(self):
    self.software_instance.setTitle("v2é%(bs)s" % ({'bs' : BACKSPACE_CHAR}))

    # Ensure SoftwareInstanceConstraint catches eventual the problems.
    consistency_list = self.software_instance.checkConsistency()
    self.assertEqual(len(consistency_list), 1, consistency_list)
    self.assertTrue(
      str(consistency_list[0].getTranslatedMessage()).startswith(
        'Title is invalid: All strings must be XML compatible'),
      consistency_list)

  def test_instanceXmlToDict(self):
    simple_parameter_sample_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é</parameter>
</instance>
"""
    self.assertEqual(
      self.software_instance._instanceXmlToDict(simple_parameter_sample_xml),
      # different from getXmlAsDict it don't encode things as utf-8
      {u'p1é': u'v1é', u'p2é': u'v2é'})

  def test_instanceXmlToDict_invalid_xml(self):
    simple_parameter_sample_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é%(bs)s</parameter>
</instance>
""" % {'bs' : BACKSPACE_CHAR}
    self.assertEqual(
      self.software_instance._instanceXmlToDict(simple_parameter_sample_xml),
      # if the XML is invalid, it return {} by default
      {})

    simple_parameter_sample_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="p1é">v1é</parameter>
  <parameter id="p2é">v2é%(bs)s</parameter>
""" % {'bs' : BACKSPACE_CHAR}
    self.assertEqual(
      self.software_instance._instanceXmlToDict(simple_parameter_sample_xml),
      # This dont raise because it isn't converted verified converted as XML.
      {})

  def test_asParameterDict_not_allocated(self):
    self.assertRaises(ValueError,
      self.software_instance._asParameterDict)

  def test_asParameterDict(self):
    self._makeComputeNode(self.project)
    self._makeComplexComputeNode(self.project, with_slave=True)

    as_parameter_dict = self.start_requested_software_instance._asParameterDict()

    self.assertSameSet(as_parameter_dict.keys(),
      ['instance_guid', 'instance_title', 'root_instance_title',
      'root_instance_short_title', 'xml', 'connection_xml',
      'filter_xml', 'slap_computer_id', 'slap_computer_partition_id',
      'slap_software_type', 'slap_software_release_url', 'slave_instance_list',
      'ip_list', 'full_ip_list', 'timestamp'])

    self.assertEqual(as_parameter_dict["instance_guid"],
      str2unicode(self.start_requested_software_instance.getReference()) )
    self.assertEqual(as_parameter_dict["instance_title"],
      str2unicode(self.start_requested_software_instance.getTitle()) )
    self.assertEqual(as_parameter_dict["xml"],
      self.start_requested_software_instance.getTextContent() )
    self.assertEqual(as_parameter_dict["connection_xml"],
      self.start_requested_software_instance.getConnectionXml() )
    self.assertEqual(as_parameter_dict["filter_xml"],
      self.start_requested_software_instance.getSlaXml() )
    self.assertEqual(as_parameter_dict["root_instance_title"],
      str2unicode(self.start_requested_software_instance.getSpecialiseTitle()))
    self.assertEqual(as_parameter_dict["root_instance_short_title"],
      str2unicode(self.start_requested_software_instance.getSpecialiseShortTitle()))
    self.assertEqual(as_parameter_dict["slap_computer_id"],
      str2unicode(self.compute_node.getReference()))
    self.assertEqual(as_parameter_dict["slap_computer_partition_id"],
      "partition1")

    self.assertEqual(len(as_parameter_dict["slave_instance_list"]), 1)
    self.assertSameSet(as_parameter_dict["slave_instance_list"][0].keys(),
      ['slave_title', 'slap_software_type', 'slave_reference',
       'timestamp', 'xml', 'connection_xml'])

    self.assertEqual(
      str2unicode(self.start_requested_slave_instance.getTitle()),
      as_parameter_dict["slave_instance_list"][0]["slave_title"]
    )

    self.assertEqual(as_parameter_dict["ip_list"], [(u'', u'ip_address_1')])
    # Since gateway isn't set both are the same.
    self.assertEqual(as_parameter_dict["full_ip_list"], [])

  def test_getInstanceTreeIpList(self):
    self._makeComputeNode(self.project)
    self._makeComplexComputeNode(self.project, with_slave=True)
    self.tic()

    self.assertEqual([(u'', u'ip_address_1')],
      self.start_requested_software_instance._getInstanceTreeIpList())

class TestSlapOSCloudSlaveInstance(
    TestSlapOSCloudSoftwareInstance):

  require_certificate = 1

  def _skipTest(self):
    pass

  test_asParameterDict_not_allocated = _skipTest
  test_getInstanceTreeIpList = _skipTest
  test_asParameterDict = _skipTest

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()
    self.tic()
    self.instance_tree = self.addInstanceTree(project=self.project, shared=True)
    self.software_instance = self.instance_tree.getSuccessorValue()
    self.tic()


class TestSlapOSCloudSlapOSComputeNodeMixin_getCacheComputeNodeInformation(
      SlapOSTestCaseMixin):
  require_certificate = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()

    # Prepare compute_node
    self.compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    self.compute_node.edit(
      title="Compute Node %s" % self.new_id,
      reference="TESTCOMP-%s" % self.new_id,
      follow_up_value=self.project
    )
    self.compute_node.validate()
    self._addCertificateLogin(self.compute_node)

    self.tic()

    self.compute_node_id = self.compute_node.getReference()
    self.compute_node_user_id = self.compute_node.getUserId()
    self.pinDateTime(DateTime())

  def beforeTearDown(self):
    self.unpinDateTime()
    self._cleaupREQUEST()

  def test_activate_getCacheComputeNodeInformation_first_access(self):

    #
    # This is a port of
    #    TestSlapOSSlapToolgetFullComputerInformation.test_activate_getFullComputerInformation_first_access
    #

    self._makeComplexComputeNode(self.project, with_slave=True)
    self.portal.REQUEST['disable_isTestRun'] = True

    self.login(self.compute_node_user_id)
    user = self.portal.portal_membership.getAuthenticatedMember().getUserName()

    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)
    # This tic and second call is to fix indexation ordering while some sub object
    # is created after the etag is computed and stored.
    self.tic()
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)

    self.commit()
    first_etag = self.compute_node._calculateRefreshEtag()
    first_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    self.assertEqual(first_etag, etag)
    self.assertEqual(first_body_fingerprint, hashData(body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

    # Trigger the compute_node reindexation
    # This should trigger a new etag, but the body should be the same
    self.compute_node.reindexObject()
    self.commit()

    # Second access
    # Check that the result is stable, as the indexation timestamp is not changed yet
    current_activity_count = len(self.portal.portal_activities.getMessageList())
    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)
    self.commit()

    self.assertEqual(first_etag, etag)
    self.assertEqual(first_body_fingerprint, hashData(body))
    self.assertEqual(current_activity_count,
                     len(self.portal.portal_activities.getMessageList()))

    self.tic()

    # Third access, new calculation expected
    # The retrieved informations comes from the cache
    # But a new cache modification activity is triggered
    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)
    self.commit()

    second_etag = self.compute_node._calculateRefreshEtag()
    second_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    self.assertNotEqual(first_etag, second_etag)
    # The indexation timestamp does not impact the response body
    self.assertEqual(first_body_fingerprint, second_body_fingerprint)
    self.assertEqual(first_etag, etag)
    self.assertEqual(first_body_fingerprint, hashData(body))
    self.assertEqual(1, len(self.portal.portal_activities.getMessageList()))

    # Execute the cache modification activity
    self.tic()

    # 4th access
    # The new etag value is now used
    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)
    self.commit()

    self.assertEqual(second_etag, etag)
    self.assertEqual(first_body_fingerprint, hashData(body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

    # Edit the instance
    # This should trigger a new etag and a new body
    self.stop_requested_software_instance.edit(text_content=self.generateSafeXml())
    self.commit()

    # 5th access
    # Check that the result is stable, as the indexation timestamp is not changed yet
    current_activity_count = len(self.portal.portal_activities.getMessageList())
    # Edition does not impact the etag
    self.assertEqual(second_etag, self.compute_node._calculateRefreshEtag())
    third_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    # The edition impacts the response body
    self.assertNotEqual(first_body_fingerprint, third_body_fingerprint)
    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)
    self.commit()

    self.assertEqual(second_etag, etag)
    self.assertEqual(first_body_fingerprint, hashData(body))
    self.assertEqual(current_activity_count,
                     len(self.portal.portal_activities.getMessageList()))

    self.tic()

    # 6th, the instance edition triggered an interaction workflow
    # which updated the cache
    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)

    # On the previous tic, the values can be indexed out of order, so recall after indextion
    # so the values are propely set.
    self.tic()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)
    self.commit()

    third_etag = self.compute_node._calculateRefreshEtag()
    self.assertNotEqual(second_etag, third_etag)
    self.assertEqual(third_etag, etag)
    self.assertEqual(third_body_fingerprint, hashData(body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

    # Remove the slave link to the partition
    # Compute Node should loose permission to access the slave instance
    self.logout()
    self.login()
    # unallocate is done by an alarm
    self.start_requested_slave_instance.setAggregate('')
    self.logout()
    self.login(self.compute_node_user_id)
    self.commit()

    # 7th access
    # Check that the result is stable, as the indexation timestamp is not changed yet
    current_activity_count = len(self.portal.portal_activities.getMessageList())
    # Edition does not impact the etag
    self.assertEqual(third_etag, self.compute_node._calculateRefreshEtag())
    # The edition does not impact the response body yet, as the aggregate relation
    # is not yet unindex
    self.assertEqual(third_body_fingerprint, hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    ))
    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)
    self.commit()

    self.assertEqual(third_etag, etag)
    self.assertEqual(third_body_fingerprint, hashData(body))
    self.assertEqual(current_activity_count,
                     len(self.portal.portal_activities.getMessageList()))

    self.tic()

    # 8th access
    # changing the aggregate relation trigger the partition reindexation
    # which trigger cache modification activity
    # So, we should get the correct cached value
    self.compute_node.setAccessStatus(self.compute_node_id)
    refresh_etag = self.compute_node._calculateRefreshEtag()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)

    # On the previous tic, the values can be indexed out of order, so recall after indextion
    # so the values are propely set.
    self.tic()
    body, etag = self.compute_node._getComputeNodeInformation(user, refresh_etag)

    self.commit()
    fourth_etag = self.compute_node._calculateRefreshEtag()
    fourth_body_fingerprint = hashData(
      self.compute_node._getCacheComputeNodeInformation(self.compute_node_id)
    )
    self.assertNotEqual(third_etag, fourth_etag)
    # The indexation timestamp does not impact the response body
    self.assertNotEqual(third_body_fingerprint, fourth_body_fingerprint)
    self.assertEqual(fourth_etag, etag)
    self.assertEqual(fourth_body_fingerprint, hashData(body))
    self.assertEqual(0, len(self.portal.portal_activities.getMessageList()))

class TestSlapOSCloudInstanceInvalidRequest(SlapOSTestCaseMixin):
  require_certificate = 1

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()

  def generateUnsafeXml_bad_string(self):
    return '<?xml version="1.0" encoding="utf-8"?><instance><parameter '\
      'id="paramé">%s\x08</parameter></instance>' % self.generateNewId()

  def _test_invalid(self, title=None, instance_xml=None, sla_xml=None, shared=False):
    self._makeComputeNode(self.project)
    self._makeComplexComputeNode(self.project, with_slave=not shared)
    self.tic()

    if title is None:
      title = self.generateNewSoftwareTitle()
    # Create second Slave with invalid char (backspace)
    instance_tree = self.portal.instance_tree_module\
          .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        # No need
        destination_section_value=None,
        follow_up_value=self.project
    )
    if not instance_xml:
      instance_xml = self.generateSafeXml()
    if not sla_xml:
      sla_xml = self.generateSafeXml()

    software_instance_kw = dict(
      software_release=self.start_requested_software_instance.getUrlString(),
      software_type=self.start_requested_software_instance.getSourceReference(),
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=shared,
      software_title=title,
      state='started',
      project_reference=self.project.getReference()
    )

    # Ensure this produces a consistent instance first, to start.
    instance_tree_kw = software_instance_kw.copy()
    instance_tree_kw.update({
      "instance_xml" : self.generateSafeXml(),
      "sla_xml" : self.generateSafeXml(),
      "software_title" : instance_tree.getTitle()
    })
    instance_tree.requestStart(**instance_tree_kw)

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      with self.assertRaises(ValidationFailed):
        instance_tree.requestInstance(**software_instance_kw)
      # Abort transaction to prevent interaction workflow to trigger,
      # and to the temporary script be removed
      transaction.abort()

  def test_invalid_backspace_char_on_software_title(self):
    title = "abc\08x" + self.generateNewSoftwareTitle()
    self._test_invalid(title=title)

  def test_invalid_backspace_char_on_slave_title(self):
    title = "abc\08x" + self.generateNewSoftwareTitle()
    self._test_invalid(title=title, shared=True)

  def test_invalid_backspace_char_on_software_paramameter_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid(instance_xml=invalid_xml)

  def test_invalid_backspace_char_on_slave_paramameter_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid(instance_xml=invalid_xml, shared=True)

  def test_invalid_backspace_char_on_software_sla_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid(sla_xml=invalid_xml)

  def test_invalid_backspace_char_on_slave_sla_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid(sla_xml=invalid_xml, shared=True)

  def _test_invalid_connection_parameter(self, connection_xml, shared=False):
    self._makeComputeNode(self.project)
    self._makeComplexComputeNode(self.project, with_slave=not shared)
    self.tic()

    # Create second Slave with invalid char (backspace)
    instance_tree = self.portal.instance_tree_module\
          .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        # No need
        destination_section_value=None,
        follow_up_value=self.project
    )

    software_instance_kw = dict(
      software_release=self.start_requested_software_instance.getUrlString(),
      software_type=self.start_requested_software_instance.getSourceReference(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=shared,
      software_title=instance_tree.getTitle(),
      state='started',
      project_reference=self.project.getReference()
    )
    instance_tree.requestStart(**software_instance_kw)
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.requestInstance(**software_instance_kw)

    software_instance = instance_tree.getSuccessorValue()
    with self.assertRaises(ValidationFailed):
      software_instance.updateConnection(connection_xml=connection_xml)

  def test_invalid_backspace_char_on_software_connection_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid_connection_parameter(invalid_xml)

  def test_invalid_backspace_char_on_slave_connection_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid_connection_parameter(invalid_xml, shared=True)

  def _test_invalid_instance_tree(self, title=None,
                                instance_xml=None, sla_xml=None):
    self._makeComputeNode(self.project)
    self._makeComplexComputeNode(self.project)
    self.tic()

    if title is None:
      title = self.generateNewSoftwareTitle()
    # Create second Slave with invalid char (backspace)
    instance_tree = self.portal.instance_tree_module\
          .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    instance_tree.edit(
        title=title,
        reference="TESTSI-%s" % self.generateNewId(),
        # No need
        destination_section_value=None,
        follow_up_value=self.project
    )
    if not instance_xml:
      instance_xml = self.generateSafeXml()
    if not sla_xml:
      sla_xml = self.generateSafeXml()

    instance_tree_kw = dict(
      software_release=self.start_requested_software_instance.getUrlString(),
      software_type=self.start_requested_software_instance.getSourceReference(),
      instance_xml=instance_xml,
      sla_xml=sla_xml,
      shared=False,
      software_title=title,
      state='started',
      project_reference=self.project.getReference()
    )

    with self.assertRaises(ValidationFailed):
      instance_tree.requestStart(**instance_tree_kw)

  def test_invalid_backspace_char_on_instance_title(self):
    title = "abc\08x" + self.generateNewSoftwareTitle()
    self._test_invalid_instance_tree(title=title)

  def test_invalid_backspace_char_on_instance_paramameter_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid_instance_tree(instance_xml=invalid_xml)

  def test_invalid_backspace_char_on_instance_sla_xml(self):
    invalid_xml = self.generateUnsafeXml_bad_string()
    self._test_invalid_instance_tree(sla_xml=invalid_xml)
