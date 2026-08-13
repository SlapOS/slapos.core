# Please see ERP5User_getSecurityCategoryValueFromAssignment for more informations
# on what this script outputs.
from DateTime import DateTime
now = DateTime()
from Products.ERP5Type.Document import newTempBase

portal_type = context.getPortalType()
if portal_type == 'Person':
  category_list = []
  for assignment_value in context.objectValues(portal_type='Assignment'):
    if assignment_value.getValidationState() == 'open' and \
      assignment_value.getDestination(portal_type="Workgroup") is not None and \
    (  not assignment_value.hasStartDate() or assignment_value.getStartDate() <= now
    ) and (
      not assignment_value.hasStopDate() or assignment_value.getStopDate() >= now
    ):
      workgroup = assignment_value.getDestinationValue(portal_type="Workgroup")
      workgroup_category_list = workgroup.ERP5User_getSecurityCategoryValueFromAssignment(
        rule_dict={
          ('function',): ((), ('function',)),
          ('destination_project',): ((), ),
          ('destination_project', 'function'): ((), ),
        },
      )
      category_list.extend(workgroup_category_list)
      for entry in workgroup_category_list:
        if set(entry) == set(['destination_project', 'function']):
          # Append Workgroup entry as a marker so we don't
          # need to browser the roles to know where the project+function
          # comes from. Use newTempBase since workgroup directly don't work.
          wg = newTempBase(context, workgroup.getId(), reference=workgroup.getUserId())
          category_list.append(
            ({
              'destination': ((wg, False),),
              'destination_project': entry['destination_project'],
              'function': entry['function'],
            })
          )
          break
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
  return category_list

category_list = []
portal = context.getPortalObject()

if portal_type == 'Compute Node':
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
