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

category_list = []

if obj is None:
  return []

aggregate_value = None
for line in obj.objectValues():
  aggregate_value = line.getAggregateValue()
  if aggregate_value is not None:
    break

if aggregate_value is None:
  return []

# Limit the scope arround Instance tree otherwise we
# Leak security on the Compute Nodes placed on the same site.
if aggregate_value.getPortalType() != "Instance Tree":
  return []

organisation = aggregate_value.Item_getCurrentSiteValue()
if organisation is not None and \
  organisation.getPortalType() == "Organisation":
  category_list.append({'destination': [organisation.getRelativeUrl()]})

return category_list