def handleSort(_category_dict):
  # Ensure that destination_project + function and source_project + function
  # generates the same Security ID. This workarround is required because
  # the value already arrives at this point pre-sorted on various locations
  # and it is not possible to change since it is widely used.
  category_list = sorted(_category_dict.keys())
  if category_list == ['function', 'source_project']:
    return ['source_project', 'function']
  # Enforce return list in case
  return category_list

return context.portal_skins.erp5_core.ERP5Type_asSecurityGroupIdSet(
  category_dict=category_dict, key_sort=handleSort)
