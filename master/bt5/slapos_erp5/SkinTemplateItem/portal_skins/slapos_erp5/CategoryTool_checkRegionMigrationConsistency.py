from zExceptions import Unauthorized
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery
if REQUEST is not None:
  raise Unauthorized

# check if is consistent
portal = context.getPortalObject()
not_expired_category_list = portal.portal_catalog(
  portal_type="Category",
  path="%portal_categories/region/%",
  validation_state=NegatedQuery(SimpleQuery(validation_state='expired'))
)

# Filter the list, since search for None dont work properly.
category_to_migrate_list = [c for c in not_expired_category_list if c.getIntIndex(0) < 1]

if not len(category_to_migrate_list):
  # Skip everything is consistent
  return []

if fixit:
  # Build a Map to not search inside the loop, this makes upgrade faster
  new_category_map = {}
  for category in not_expired_category_list:
    if c.getIntIndex(0) < 1 or category.getValidationState() == 'expired':
      continue
    title = category.getTitle()
    if title not in new_category_map:
      new_category_map[title] = [category]
    else:
      new_category_map[title].append(category)

message_list = []
for category in category_to_migrate_list:
  if category.getIntIndex() == 1:
    raise ValueError("Selected the wrong thing")

  if category.getValidationState() == 'expired':
    # skip, we seems to be rerunning the migration
    # and some reindexation is going on.
    continue

  message_list.append(
    "%s requires migration (int_index: %s, validation_state: %s)" % (
      category.getRelativeUrl(), category.getIntIndex(), category.getValidationState())
  )
  if fixit:
    new_category_list = new_category_map[category.getTitle()]

    if len(new_category_list) != 1:
      raise ValueError('Cannot decide which one to migrate into (%s options)' % len(new_category_list))

    new_category = new_category_list[0]

    # XXX It could be relavant to use activities here
    category.Category_updateRelatedRegionAndExpire(new_category)
    message_list.append(
      "%s migrated and expired (int_index: %s, validation_state: %s)" % (
        category.getRelativeUrl(), category.getIntIndex(), category.getValidationState())
    )

return message_list
