if context.getPortalType() == 'Person':
  return context.ERP5User_getSecurityCategoryValueFromAssignment(
    rule_dict={
      ('function',): ((), ('function',)),
      ('destination_project',): ((), ),
      ('destination_project', 'function'): ((), ),
    },
  )
return context.ERP5User_getSlapOSUserSecurityCategoryValue()
