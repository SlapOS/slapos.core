from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

software_instance = context
instance_tree = software_instance.getSpecialiseValue()
if instance_tree is None:
  return
person = instance_tree.getDestinationSectionValue(portal_type='Person')
if person is None:
  return

return person.Person_generateCloudContract(batch=True)
