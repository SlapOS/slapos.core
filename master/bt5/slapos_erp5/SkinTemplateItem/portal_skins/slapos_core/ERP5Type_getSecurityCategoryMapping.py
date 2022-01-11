"""
Core security script - defines the way to get security groups of the current user.

WARNING: providing such script in erp5_dms could be dangerous
if this conflicts with an existing production site which uses
deprecated ERP5Type_asSecurityGroupIdList
"""

return (
  # Person security
  ('ERP5Type_getSecurityCategoryFromAssignment', ['function']),
  ('ERP5Type_getSecurityCategoryFromAssignmentParent', ['function']),
  # XXX TODO check that only validated project are used
  ('ERP5Type_getSecurityCategoryFromAssignment', ['destination_project']),
  ('ERP5Type_getSecurityCategoryFromAssignment', ['destination_project', 'function']),
  
  # Compute Node security
  ('ERP5Type_getComputeNodeSecurityCategory', ['role']),

  # Instance security
  ('ERP5Type_getSoftwareInstanceSecurityCategory', ['role']),
  ('ERP5Type_getSoftwareInstanceSecurityCategory', ['destination_project']),
  ('ERP5Type_getSoftwareInstanceSecurityCategory', ['destination_project', 'role']),
  ('ERP5Type_getSoftwareInstanceSecurityCategory', ['aggregate']),

)
