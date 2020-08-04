from Products.ERP5Type.TransactionalVariable import getTransactionalVariable
from lxml import etree
from zExceptions import Unauthorized

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
  except (etree.XMLSchemaError, etree.XMLSchemaParseError, #pylint: disable=catching-non-exception
    etree.XMLSchemaValidateError, etree.XMLSyntaxError): #pylint: disable=catching-non-exception
    LOG('SubscriptionRequest', INFO, 'Issue during parsing xml:', error=True)
  return result_dict

def SubscriptionCondition_renderParameter(self, amount=0, **kw):
  method_id = self.getParameterTemplateRendererMethodId()
  if method_id is not None:
    return getattr(self, method_id)(amount=amount, **kw)

  return self.getTextContent()

def SubscriptionRequest_searchExistingUserByEmail(self, email, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized
  portal = self.getPortalObject()

  erp5_login_list = portal.portal_catalog.unrestrictedSearchResults(
    portal_type="ERP5 Login",
    reference=email,
    validation_state="validated")

  if len(erp5_login_list):
    return erp5_login_list[0].getParentValue()

  # Already has login with this.
  person_list = portal.portal_catalog.unrestrictedSearchResults(
    portal_type="Person",
    default_email_text=email,
    validation_state="validated")

  if len(person_list):
    return person_list[0].getObject()

