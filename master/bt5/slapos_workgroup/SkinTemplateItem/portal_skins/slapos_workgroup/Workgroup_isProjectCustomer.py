assert project.getPortalType() == 'Project'
assert context.getPortalType() == 'Workgroup'

portal = context.getPortalObject()
function_uid = portal.portal_categories.function.customer.getUid()

# Compatible with ERP5User_getUserSecurityCategoryValueList
for entry in context.ERP5User_getSecurityCategoryValueFromAssignment(
  rule_dict={
   ('destination_project', 'function'): ((), )
  }
):
  # Sanitize before check
  if len(entry) != 2 or \
      'destination_project' not in entry or \
      'function' not in entry:
    continue

  try:
    found_project = entry['destination_project'][0][0]
    found_function = entry['function'][0][0]
  except IndexError:
    # No project or function found on assignment
    continue

  if found_project.getUid() == project.getUid() and \
     found_function.getUid() == function_uid:
    return True
