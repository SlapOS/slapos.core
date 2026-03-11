###############################################################################
#
# Copyright (c) 2002-2013 Nexedi SA and Contributors. All Rights Reserved.
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

from lxml import etree
from zExceptions import Unauthorized
import pkg_resources
from io import BytesIO

from DateTime import DateTime
from Products.ERP5Type.Utils import str2bytes, unicode2str

def ComputerConsumptionTioXMLFile_parseXml(self, REQUEST=None):
  """Call bang on self."""
  if REQUEST is not None:
    raise Unauthorized

  compute_node_consumption_model = \
    pkg_resources.resource_string(
      'slapos.slap', 'doc/computer_consumption.xsd')

  # Validate against the xsd
  xsd_model = BytesIO(compute_node_consumption_model)
  xmlschema_doc = etree.parse(xsd_model)
  xmlschema = etree.XMLSchema(xmlschema_doc)

  xml = self.getData(str2bytes(""))
  string_to_validate = BytesIO(xml)

  try:
    tree = etree.parse(string_to_validate)
  except (etree.XMLSyntaxError, etree.DocumentInvalid): #pylint: disable=catching-non-exception
    return None

  if not xmlschema.validate(tree):
    return None

  # Get the title
  title = \
      tree.find('transaction').find('title').text or ""
  title = unicode2str(title)

  start_date = DateTime(tree.find('transaction').find('start_date').text)
  stop_date = DateTime(tree.find('transaction').find('stop_date').text)
  movement_list = []
  for movement in tree.find('transaction').findall('movement'):
    movement_list.append({
      'resource': unicode2str(movement.find('resource').text or ""),
      'title': unicode2str(movement.find('title').text or ""),
      'reference': unicode2str(movement.find('reference').text or ""),
      'quantity': float(movement.find('quantity').text or "0"),
      'category': unicode2str(movement.find('category').text or ""),
    })

  return {
    'title': title,
    'start_date': start_date,
    'stop_date': stop_date,
    'movement': movement_list,
  }
