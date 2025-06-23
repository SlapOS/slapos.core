# Please see ERP5User_getSecurityCategoryValueFromAssignment for more informations
# on what this script outputs.

portal_type = context.getPortalType()
if portal_type == 'Person':
  return context.ERP5User_getSecurityCategoryValueFromAssignment(
    rule_dict={
      ('function',): ((), ('function',)),
      ('destination_project',): ((), ),
      ('destination_project', 'function'): ((), ),
    },
  )

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
