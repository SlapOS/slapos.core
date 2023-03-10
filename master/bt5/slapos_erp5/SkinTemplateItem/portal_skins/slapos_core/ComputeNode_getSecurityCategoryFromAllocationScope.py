# XXX For now, this script requires proxy manager

# base_category_list : list of category values we need to retrieve
# user_name : string obtained from getSecurityManager().getUser().getUserName() [NuxUserGroup]
#             or from getSecurityManager().getUser().getId() [PluggableAuthService with ERP5GroupManager]
# object : object which we want to assign roles to.
# portal_type : portal type of object

# must always return a list of dicts

if obj is None:
  return []

compute_node = obj

category_list = []

scope = compute_node.getAllocationScope()
if scope == 'open/public':
  return {"Auditor": ["R-SHADOW-PERSON"]}
elif scope == 'open/subscription':
  return {"Auditor": ["R-SHADOW-PERSON"]}
elif scope == 'open/personal':
  person = compute_node.getSourceAdministrationValue(portal_type="Person")
  if person is not None:
    return {"Auditor": ["SHADOW-%s" % person.getUserId()]}

return category_list
