support_request = context

instance_tree = support_request.getAggregateValue(portal_type="Instance Tree")
if instance_tree is None:
  return

instance = None
for possible_instance in instance_tree.getSuccessorValueList():
  if possible_instance.getSlapState() != 'destroy_requested':
    instance = possible_instance
    break
if instance is None:
  return

parameter_dict = instance.getConnectionXmlAsDict()
return parameter_dict.get('monitor-setup-url', None)
