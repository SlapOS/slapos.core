compute_node = state_object["object"]
allocation_scope = compute_node.getAllocationScope()

edit_kw = {}

# Automatically close the capacity whenever the allocation scope
# changes, and let the alarm update it later, whenever the 
# allocation scope is open.
if compute_node.getCapacityScope() != "close":
  edit_kw['capacity_scope'] = 'close'

if compute_node.getMonitorScope() is None:
  edit_kw['monitor_scope'] = 'enabled'

if allocation_scope == "close/forever":
  edit_kw['monitor_scope'] = 'disabled'

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
