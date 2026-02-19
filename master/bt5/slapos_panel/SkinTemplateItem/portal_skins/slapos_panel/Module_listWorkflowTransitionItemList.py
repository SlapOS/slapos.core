result = {
  # items (ready to be used in a listfield items) of common workflow transition on a module's documents
  'transition_item_list': [],
  # form id for each transition
  'form_id_dict': {},
  # additional catalog parameter per transition
  'listbox_parameter_dict': {}
}

portal = context.getPortalObject()
module = context
translate = portal.Base_translateString

if module.getPortalType() == 'Support Request Module':

  result['transition_item_list'].append((translate('Add Event'), 'Ticket_addSlapOSEvent'))
  result['form_id_dict']['Ticket_addSlapOSEvent'] = 'Ticket_viewSlapOSEventFastInputDialog'
  result['listbox_parameter_dict']['Ticket_addSlapOSEvent'] = [('simulation_state', ['submitted']), ('local_roles', ['Assignee', 'Assignor'])]

  result['transition_item_list'].append((translate('Suspend'), 'Ticket_suspendSlapOS'))
  result['form_id_dict']['Ticket_suspendSlapOS'] = 'Ticket_viewSlapOSSuspendFastInputDialog'
  result['listbox_parameter_dict']['Ticket_suspendSlapOS'] = [('simulation_state', ['validated']), ('local_roles', ['Assignee', 'Assignor'])]

  result['transition_item_list'].append((translate('Close'), 'Ticket_closeSlapOS'))
  result['form_id_dict']['Ticket_closeSlapOS'] = 'Ticket_viewSlapOSCloseFastInputDialog'
  result['listbox_parameter_dict']['Ticket_closeSlapOS'] = [('simulation_state', ['submitted', 'validated', 'suspended']), ('local_roles', ['Assignee', 'Assignor'])]

elif module.getPortalType() == 'Upgrade Decision Module':

  result['transition_item_list'].append((translate('Accept'), 'UpgradeDecision_acceptOnSlaposPanel'))
  result['form_id_dict']['UpgradeDecision_acceptOnSlaposPanel'] = 'Base_viewEmptyDialog'
  result['listbox_parameter_dict']['Ticket_addSlapOSEvent'] = [('simulation_state', ['confirmed']), ('local_roles', ['Assignee', 'Assignor'])]

  result['transition_item_list'].append((translate('Reject'), 'UpgradeDecision_rejectOnSlaposPanel'))
  result['form_id_dict']['UpgradeDecision_rejectOnSlaposPanel'] = 'Base_viewEmptyDialog'
  result['listbox_parameter_dict']['Ticket_addSlapOSEvent'] = [('simulation_state', ['confirmed']), ('local_roles', ['Assignee', 'Assignor'])]

result['transition_item_list'].insert(0, ('', ''))

return result
