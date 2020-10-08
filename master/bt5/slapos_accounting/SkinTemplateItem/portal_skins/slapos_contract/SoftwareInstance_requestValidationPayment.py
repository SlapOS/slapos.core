from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

software_instance = context
hosting_subscription = software_instance.getSpecialiseValue()
if hosting_subscription is None:
  return
person = hosting_subscription.getDestinationSectionValue(portal_type='Person')
if person is None:
  return

return person.Person_generateCloudContract(batch=True)
