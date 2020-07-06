##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Lukasz Nowak <luke@nexedi.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
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

from Products.ERP5Type.Constraint import Constraint
from lxml import etree
from slapos import slap
import pkg_resources

class SoftwareInstanceXmlValidationConstraint(Constraint):
  """
    Checks that Software Instance's XML is valid against its DSD.
  """

  _message_id_list = [ 'message_xml_invalid', 'message_xml_garbaged',\
                       'message_no_xml' ]

  message_xml_garbaged = "The string is not XML at all."
  message_xml_invalid = "The XML failed validation with error: ${xml_error}"
  message_no_xml = "No XML is set"

  def checkConsistency(self, obj, fixit=0):
    """Checks that Software Instance's XML is valid.
    """
    error_list = []
    if self._checkConstraintCondition(obj):
      xml_schema = etree.XMLSchema(
            file=pkg_resources.resource_filename(
              slap.__name__, 'doc/software_instance.xsd'))
      try:
        tree = etree.fromstring(obj.getTextContent())
      except etree.XMLSyntaxError:
        error_list.append(self._generateError(obj,
                            self._getMessage('message_xml_garbaged')))
      except ValueError:
        error_list.append(self._generateError(obj,
                            self._getMessage('message_no_xml')))
      else:
        if not xml_schema.validate(tree):
          mapping = {}
          mapping['xml_error'] = xml_schema.error_log.filter_from_errors()[0]
          error_list.append(self._generateError(obj,
                              self._getMessage('message_xml_garbaged'),
                              mapping))
    return error_list

