"""
This script returns a list of dictionaries which represent
the security groups which a person is member of. It extracts
the categories from the current content. It is useful in the
following cases:

- calculate a security group based on a given
  category of the current object (ex. group). This
  is used for example in ERP5 DMS to calculate
  document security.

- assign local roles to a document based on
  the person which the object related to through
  a given base category (ex. destination). This
  is used for example in ERP5 Project to calculate
  Task / Task Report security.

The parameters are

  base_category_list -- list of category values we need to retrieve
  user_name          -- string obtained from getSecurityManager().getUser().getId()
  object             -- object which we want to assign roles to
  portal_type        -- portal type of object

NOTE: for now, this script requires proxy manager
"""

if obj is None:
  return []

if not base_category_list:
  return []

# We only need the first
base_category = base_category_list[0]

person_list = [i for i in obj.getValueList(base_category) if i.getPortalType() == "Person"]

if not person_list:
  return []

# The assignee is hardcoded here.
person_shadow_id = "SHADOW-%s" % person_list[0].getUserId()

# Return all usecased so the role filter on upper level
return {"Assignee": [person_shadow_id], 
        "Auditor": [person_shadow_id]}
