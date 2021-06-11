from Products.PythonScripts.standard import Object

portal = context.getPortalObject()

support_request_list = portal.portal_catalog(
                portal_type="Support Request",
                simulation_state=["validated", "suspended"],
                )

instance_tree_list = []
for support_request in support_request_list:
  instance_tree_list.append(
    support_request.getAggregateValue(portal_type="Instance Tree"))

monitor_instance_list = []

for instance_tree in instance_tree_list:

  if instance_tree is None:
    continue

  if instance_tree.getSlapState() == 'destroy_requested':
    continue

  instance = instance_tree.getSuccessorValue()
  if instance is None or instance.getSlapState() in ('destroy_requested', 'stop_requested'):
    continue

  parameter_dict = instance.getConnectionXmlAsDict()

  url_string = parameter_dict.get('monitor_setup_url', '') or parameter_dict.get('monitor-setup-url', '')
  if url_string:
    param_list = url_string.split('#')
    if len(param_list) != 2:
      # bad or unknown url
      continue

    monitor_instance_list.append(
      Object(uid="uid_%s" % instance.getId(),
             title=instance.getTitle(),
             monitor_url=url_string))

return monitor_instance_list
