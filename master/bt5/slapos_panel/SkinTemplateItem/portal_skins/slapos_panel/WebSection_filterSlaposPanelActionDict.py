filtered_action_dict = {}
for action_category_name, action_list in action_dict.items():
  filtered_action_dict[action_category_name] = []
  for action in action_list:
    if action['id'] == 'slapos_panel_view':
      # Rename the webapp default view action to 'view',
      # to be compatible with all the Base_redirect calls
      # hardcoding the 'view' action
      action['id'] = 'view'
      filtered_action_dict[action_category_name].append(action)
    elif (action['id'].startswith('slapos_panel_workflow_')):
      # Consider some actions as fake workflow actions
      # To separate them on the panel
      if 'workflow' not in filtered_action_dict:
        filtered_action_dict['workflow'] = []
      filtered_action_dict['workflow'].append(action)
    elif (
      ('slapos' in action['id']) or
      (action['id'] in ['delete_document_list', 'delete_document'])
    ):
      # Allow all slapos* action
      # Allow deleting documents
      filtered_action_dict[action_category_name].append(action)

  if not filtered_action_dict[action_category_name]:
    # If there is no remaining action, drop the category
    filtered_action_dict.pop(action_category_name)

return filtered_action_dict
