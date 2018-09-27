from Products.ERP5Type.TransactionalVariable import getTransactionalVariable

def SubscriptionRequest_saveTransactionalUser(self, person=None):
  if person.getPortalType() == "Person":
    getTransactionalVariable()["transactional_user"] = person
  return person

