compute_node = state_object["object"]
allocation_scope = compute_node.getAllocationScope()

if allocation_scope in ['open/public', 'open/subscription']:
  # Public compute_node capacity is handle by an alarm
  capacity_scope = 'close'
  monitor_scope = 'enabled'
elif allocation_scope == 'open/friend':
  # Capacity is not handled for 'private' compute_nodes
  capacity_scope = 'open'
  monitor_scope = 'enabled'
elif allocation_scope == 'open/personal':
  capacity_scope = 'open'
  # Keep the same.
  monitor_scope = compute_node.getMonitorScope("disabled")
else:
  monitor_scope = 'disabled'
  capacity_scope = 'close'

edit_kw = {
  'capacity_scope': capacity_scope,
  'monitor_scope': monitor_scope
}

self_person = compute_node.getSourceAdministrationValue(portal_type="Person")
if self_person is None:
  compute_node.edit(**edit_kw)
  return

self_email = self_person.getDefaultEmailCoordinateText()
if allocation_scope in ['open/public', 'open/subscription']:
  # reset friends and update in place
  edit_kw['subject_list'] = ['']
  edit_kw['destination_section'] = None
elif allocation_scope == 'open/personal':
  # reset friends to self and update in place
  edit_kw['subject_list'] = [self_email]
  edit_kw['destination_section'] = self_person.getRelativeUrl()
else:
  subject_list = compute_node.getSubjectList()
  if self_email not in subject_list:
    # add self as friend
    subject_list.append(self_email)
    edit_kw['subject_list'] = subject_list

compute_node.edit(**edit_kw)
