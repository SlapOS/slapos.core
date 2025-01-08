portal = context.getPortalObject()

assignment_category_list = portal.portal_preferences.getPreferredSubscriptionAssignmentCategoryList()
is_default_project_defined = False
for assignment_category in assignment_category_list:
  if assignment_category.startswith('destination_project/project_module/'):
    is_default_project_defined = True

if not is_default_project_defined:
  return

portal.portal_catalog.searchAndActivate(
  portal_type='Assignment',
  # Do not create assignment if the Person does not have at least one
  validation_state='open',
  # Prevent checking the same person multiple times
  group_by=['parent_uid'],
  method_id='Assignment_createPersonMissingSubscriptionAssignment',
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  method_args=[assignment_category_list],
  method_kw={"activate_kw": {'tag': tag, 'priority': 2}},
  activate_kw={'tag': tag, 'priority': 2}
)

context.activate(after_tag=tag).getId()
