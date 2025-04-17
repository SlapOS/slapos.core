# this API uses `object` name
# pylint: disable=redefined-builtin
"""Give roles to the owner of the document.

Note that in zope there are two notions of "Owner", first the "Ownership",
which is usually takin into account with executable documents and the "Owner local role".
In normal cases, they are set set to the same.
This uses the later to consider owner, for no strong reasons, just because I guess it would
be easier to use for migrations or "data maintenance". With local roles, there
can be  multiple owners, which might be useful in some cases we don't imagine at this point.
Also, changing owner is easier with local roles (with ownership the ZMI only allows to
"take ownership", with local roles, we can easily change ownership).
"""
from collections import defaultdict
category_dict = defaultdict(list)

if object is None:
  return []

for user, role_list in object.get_local_roles():
  for role in role_list:
    if role == 'Owner':
      # we return all roles here, only the one defined on the role definition document
      # will be set on the document we are assigning local roles on.
      for r in ('Auditor', 'Author', 'Assignee', 'Assignor', 'Associate'):
        category_dict[r].append(user)

# By returning a dict, we force force ERP5Type to interpret the result as a mapping from
# roles to existing security groups
return dict(category_dict)
