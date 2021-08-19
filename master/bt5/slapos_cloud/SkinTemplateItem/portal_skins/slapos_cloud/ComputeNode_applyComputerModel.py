compute_node = context
Base_translateString = context.Base_translateString
computer_model_portal_type = 'Computer Model'

computer_model = compute_node.getSpecialiseValue(
  portal_type=computer_model_portal_type)

if computer_model is None:
  message = Base_translateString('No Computer Model.')
  result = False
else :
  category_list = [
    'cpu_core',
    'cpu_frequency',
    'cpu_type',
    'function',
    'group',
    'local_area_network_type',
    'memory_size',
    'memory_type',
    'role',
    'region',
    'storage_capacity',
    'storage_interface',
    'storage_redundancy',
    'wide_area_network_type',
  ]

  property_list = [
    'capacity_quantity'
  ]

  new_category_dict = {}
  for category in category_list:
    if force or not compute_node.getPropertyList(category):
      v = computer_model.getPropertyList(category)
      if v:
        new_category_dict[category] = v

  for _property in property_list:
    if force or not compute_node.getProperty(_property):
      v = computer_model.getProperty(_property)
      if v:
        new_category_dict[_property] = v

  if new_category_dict:
    compute_node.edit(**new_category_dict)
    message = Base_translateString('Computer Model applied.')
    result = True
  else:
    message = Base_translateString('No changes applied.')
    result = False

if not batch_mode:
  return context.Base_redirect(form_id,
          keep_items=dict(portal_status_message=message))
else:
  return result
