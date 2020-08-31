###############################################################################
#
# Copyright (c) 2002-2013 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

from lxml import etree
from zExceptions import Unauthorized
import pkg_resources
import StringIO

def ComputerConsumptionTioXMLFile_parseXml(self, REQUEST=None):
  """Call bang on self."""
  if REQUEST is not None:
    raise Unauthorized
  xml = self.getData("")

  computer_consumption_model = \
    pkg_resources.resource_string(
      'slapos.slap', 'doc/computer_consumption.xsd')

  # Validate against the xsd
  xsd_model = StringIO.StringIO(computer_consumption_model)
  xmlschema_doc = etree.parse(xsd_model)
  xmlschema = etree.XMLSchema(xmlschema_doc)

  string_to_validate = StringIO.StringIO(xml)

  try:
    tree = etree.parse(string_to_validate)
  except (etree.XMLSyntaxError, etree.DocumentInvalid): #pylint: disable=catching-non-exception
    return None

  if not xmlschema.validate(tree):
    return None

  # Get the title
  title = \
      tree.find('transaction').find('title').text or ""
  title = title.encode("UTF-8")

  movement_list = []
  for movement in tree.find('transaction').findall('movement'):
    movement_list.append({
      'resource': (movement.find('resource').text or "").encode("UTF-8"),
      'title': (movement.find('title').text or "").encode("UTF-8"),
      'reference': (movement.find('reference').text or "").encode("UTF-8"),
      'quantity': float(movement.find('quantity').text or "0"),
      'category': (movement.find('category').text or "").encode("UTF-8"),
    })

  return {
    'title': title,
    'movement': movement_list,
  }
