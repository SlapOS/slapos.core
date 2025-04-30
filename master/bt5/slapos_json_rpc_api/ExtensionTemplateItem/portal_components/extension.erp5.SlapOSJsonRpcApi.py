###############################################################################
#
# Copyright (c) 2002-2025 Nexedi SA and Contributors. All Rights Reserved.
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

import six
import pkg_resources
from lxml import etree
from zLOG import LOG, INFO


def _validateXML(to_be_validated, xsd_model):
  """Will validate the xml file"""
  #We parse the XSD model
  xsd_model = six.StringIO(xsd_model)
  xmlschema_doc = etree.parse(xsd_model)
  xmlschema = etree.XMLSchema(xmlschema_doc)

  string_to_validate = six.StringIO(to_be_validated)

  try:
    document = etree.parse(string_to_validate)
  except (etree.XMLSyntaxError, etree.DocumentInvalid) as e: # pylint: disable=catching-non-exception
    LOG('SlapTool::_validateXML', INFO,
      'Failed to parse this XML reports : %s\n%s' % \
        (to_be_validated, e))
    return False

  if xmlschema.validate(document):
    return True

  return False

def validateTioXMLAndExtractReference(tioxml):
  compute_node_consumption_model = pkg_resources.resource_string(
    'slapos.slap',
    'doc/computer_consumption.xsd'
  )

  if _validateXML(tioxml, compute_node_consumption_model):
    tree = etree.fromstring(tioxml)
    source_reference = tree.find('transaction').find('reference').text or ""
    return source_reference.encode("UTF-8")
  return None

