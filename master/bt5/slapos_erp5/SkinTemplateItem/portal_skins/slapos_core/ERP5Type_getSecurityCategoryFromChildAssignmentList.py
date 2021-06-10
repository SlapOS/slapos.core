"""
This script returns a list of dictionaries which represent
the security groups which a person is member of. It extracts
the categories from the current content. It is useful in the
following cases:

- calculate a security group based on a given
  category of all Assifbment subobjects (ex. destination_project). This
  is used for example in ERP5 to calculate
  security of person objects so that members 
  of the same project can view each other.

The parameters are

  base_category_list -- list of category values we need to retrieve
  user_name          -- string obtained from getSecurityManager().getUser().getId()
  object             -- object which we want to assign roles to
  portal_type        -- portal type of object

NOTE: for now, this script requires proxy manager
"""

category_list = []

if obj is None:
  return []

person_object = obj

# We look for every valid assignments of this user
for assignment in person_object.contentValues(filter={'portal_type': 'Assignment'}):
  if assignment.getValidationState() == 'open':
    category_dict = {}
    for base_category in base_category_list:
      category_value_list = assignment.getAcquiredValueList(base_category)
      if category_value_list:
        for category_value in category_value_list:
          category_dict.setdefault(base_category, []).append('%s' % category_value.getRelativeUrl())
    category_list.append(category_dict)

return category_list
