portal_type_list = ['Computer', 'Computer Network', 'Hosting Subscription']
internal_packing_list_line = state_change['object']
after_tag = (internal_packing_list_line.getPath(), ('immediateReindexObject', 'recursiveImmediateReindexObject'))
for object_ in internal_packing_list_line.getAggregateValueList(portal_type=portal_type_list):
  object_.activate(after_path_and_method_id=after_tag).updateLocalRolesOnSecurityGroups()
