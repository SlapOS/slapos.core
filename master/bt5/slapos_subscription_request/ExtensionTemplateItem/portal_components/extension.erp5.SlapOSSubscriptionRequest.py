from Products.ERP5Type.TransactionalVariable import getTransactionalVariable
from zExceptions import Unauthorized


def SubscriptionRequest_saveTransactionalUser(self, person=None):
  if person.getPortalType() == "Person":
    getTransactionalVariable()["transactional_user"] = person
  return person

def SubscriptionRequest_getTransactionalUser(self, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized
  return getTransactionalVariable().get("transactional_user", None) 

def SubscriptionRequest_searchExistingUserByEmail(self, email, REQUEST=None):
  if REQUEST is not None:
    raise Unauthorized
  portal = self.getPortalObject()

  if email in ["", None]:
    return

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

