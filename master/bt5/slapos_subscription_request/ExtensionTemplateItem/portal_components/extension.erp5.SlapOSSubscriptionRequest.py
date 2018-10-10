from Products.ERP5Type.TransactionalVariable import getTransactionalVariable
from lxml import etree
from zLOG import LOG, INFO

def SubscriptionRequest_saveTransactionalUser(self, person=None):
  if person.getPortalType() == "Person":
    getTransactionalVariable()["transactional_user"] = person
  return person

def Base_instanceXmlToDict(self, xml):
  result_dict = {}
  try:
    if xml is not None and xml != '':
      tree = etree.fromstring(xml)
      for element in tree.findall('parameter'):
        key = element.get('id')
        value = result_dict.get(key, None)
        if value is not None:
          value = value + ' ' + element.text
        else:
          value = element.text
        result_dict[key] = value
  except (etree.XMLSchemaError, etree.XMLSchemaParseError,
    etree.XMLSchemaValidateError, etree.XMLSyntaxError):
    LOG('SubscriptionRequest', INFO, 'Issue during parsing xml:', error=True)
  return result_dict

def SubscriptionCondition_renderParameter(self, amount=0, **kw):
  method_id = self.getParameterTemplateRendererMethodId()
  if method_id is not None:
    return getattr(self, method_id)(amount=amount, **kw)

  return self.getTextContent()

