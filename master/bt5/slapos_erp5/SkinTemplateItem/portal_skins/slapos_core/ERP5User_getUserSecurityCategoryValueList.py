# Please see ERP5User_getSecurityCategoryValueFromAssignment for more informations
# on what this script outputs.
from DateTime import DateTime
now = DateTime()
portal = context.getPortalObject()

portal_type = context.getPortalType()
category_list = []

if portal_type == 'Person':
  # Only extend workgroup from a person to prevent infinite loop
  # (workgroup assignmed to self)
  for assignment_value in context.objectValues(portal_type='Assignment'):
    if ((assignment_value.getValidationState() == 'open') and
        (assignment_value.getDestination(portal_type="Workgroup") is not None) and
        (not assignment_value.hasStartDate() or (assignment_value.getStartDate() <= now)) and
        (not assignment_value.hasStopDate() or (now <= assignment_value.getStopDate()))):
      workgroup = assignment_value.getDestinationValue(portal_type="Workgroup")
      if workgroup.getValidationState() == 'validated':
        # invalidating a workgroup will quickly block all functionalities
        category_list.extend(workgroup.ERP5User_getUserSecurityCategoryValueList())

if portal_type in ('Person', 'Workgroup'):
  category_list.extend(
    context.ERP5User_getSecurityCategoryValueFromAssignment(
    rule_dict={
      ('function',): ((), ('function',)),
      ('destination_project',): ((), ),
      ('destination',): ((), ),
      ('destination_project', 'function'): ((), ),
    },
   )
  )

elif portal_type == 'Compute Node':
  category_list.append({
    'role': (
      (portal.portal_categories.role.computer, False),
      ),
    })

elif portal_type == 'Software Instance':
  instance_role = portal.portal_categories.role.instance
  category_list.append({'role': ((instance_role, False),),})

  project = context.getFollowUpValue(portal_type='Project')
  if project is not None:
    category_list.append(({'destination_project': ((project, False),)}))
    category_list.append(
      ({
        'role': ((instance_role, False),),
        'destination_project': ((project, False),)
      })
    )

  instance_tree = context.getSpecialiseValue(portal_type='Instance Tree')
  if instance_tree is not None:
    category_list.append({'aggregate': ((instance_tree, False),),})

else:
  raise NotImplementedError(
    'Unsupported portal type as user: %s' % portal_type)

return category_list
