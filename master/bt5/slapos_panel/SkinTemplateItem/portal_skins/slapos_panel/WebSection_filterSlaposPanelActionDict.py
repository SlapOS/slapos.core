filtered_action_dict = {}
for action_category_name, action_list in action_dict.items():
  filtered_action_dict[action_category_name] = [action for action in action_list if 'slapos' in action['id']]
return filtered_action_dict
