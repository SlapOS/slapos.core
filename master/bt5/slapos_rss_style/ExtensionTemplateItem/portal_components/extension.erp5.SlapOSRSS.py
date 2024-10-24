from zExceptions import Unauthorized
from Products.Formulator.Widget import convert_to_xml_compatible_string

def convertToSafeXML(self, value, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized
  if not value:
    return value
  return convert_to_xml_compatible_string(value)