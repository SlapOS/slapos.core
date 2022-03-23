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


from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSCloudSoftwareInstance(
    SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree()

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

  def test_asParameterDict_not_allocated(self):
    self.assertRaises(ValueError,
      self.software_instance._asParameterDict)

  def test_asParameterDict(self):
    self._makeComputeNode()
    self._makeComplexComputeNode(with_slave=True)

    as_parameter_dict = self.start_requested_software_instance._asParameterDict()

    self.assertSameSet(as_parameter_dict.keys(),
      ['instance_guid', 'instance_title', 'root_instance_title',
      'root_instance_short_title', 'xml', 'connection_xml',
      'filter_xml', 'slap_computer_id', 'slap_computer_partition_id',
      'slap_software_type', 'slap_software_release_url', 'slave_instance_list',
      'ip_list', 'full_ip_list', 'timestamp'])

    self.assertEqual(as_parameter_dict["instance_guid"],
      self.start_requested_software_instance.getReference().decode("UTF-8") )
    self.assertEqual(as_parameter_dict["instance_title"],
      self.start_requested_software_instance.getTitle().decode("UTF-8") )
    self.assertEqual(as_parameter_dict["xml"],
      self.start_requested_software_instance.getTextContent() )
    self.assertEqual(as_parameter_dict["connection_xml"],
      self.start_requested_software_instance.getConnectionXml() )
    self.assertEqual(as_parameter_dict["filter_xml"],
      self.start_requested_software_instance.getSlaXml() )
    self.assertEqual(as_parameter_dict["root_instance_title"], 
      self.start_requested_software_instance.getSpecialiseTitle().decode("UTF-8"))
    self.assertEqual(as_parameter_dict["root_instance_short_title"],
      self.start_requested_software_instance.getSpecialiseShortTitle().decode("UTF-8"))
    self.assertEqual(as_parameter_dict["slap_computer_id"], 
      self.compute_node.getReference().decode("UTF-8"))
    self.assertEqual(as_parameter_dict["slap_computer_partition_id"],
      "partition1")

    self.assertEqual(len(as_parameter_dict["slave_instance_list"]), 1)
    self.assertSameSet(as_parameter_dict["slave_instance_list"][0].keys(),
      ['slave_title', 'slap_software_type', 'slave_reference',
       'timestamp', 'xml', 'connection_xml'])

    self.assertEqual(
      self.start_requested_slave_instance.getTitle().decode("UTF-8"),
      as_parameter_dict["slave_instance_list"][0]["slave_title"]
    )

    self.assertEqual(as_parameter_dict["ip_list"], [(u'', u'ip_address_1')])
    # Since gateway isn't set both are the same.
    self.assertEqual(as_parameter_dict["full_ip_list"], [(u'', u'ip_address_1')])