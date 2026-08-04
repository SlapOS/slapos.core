portal = context.getPortalObject()
person = context

# First, search all customer's Workgroup for this project
workgroup_uid_list = [x.getDestinationDecisionUid() for x in portal.portal_catalog(
  portal_type='Assignment Request',
  destination_decision__portal_type='Workgroup',
  destination_project__uid=project.getUid(),
  function__uid=portal.portal_categories.function.customer.getUid(),
) if (x.getDestinationDecisionValue().getValidationState() == 'validated')]

if not workgroup_uid_list:
  return None

# Then, search if the person is assignment to those workgroup
assigned_customer_workgroup_relative_url_set = set()
assigned_customer_workgroup_relative_url_set.update([x.getDestination() for x in portal.portal_catalog(
  portal_type='Assignment Request',
  destination__uid=workgroup_uid_list,
  destination_decision__uid=person.getUid(),
  limit=2
)])

if len(assigned_customer_workgroup_relative_url_set) == 0:
  return None
elif len(assigned_customer_workgroup_relative_url_set) == 1:
  return portal.restrictedTraverse(list(assigned_customer_workgroup_relative_url_set)[0])
else:
  raise ValueError("Multiple customer workgroup found: %s" % str(assigned_customer_workgroup_relative_url_set))
