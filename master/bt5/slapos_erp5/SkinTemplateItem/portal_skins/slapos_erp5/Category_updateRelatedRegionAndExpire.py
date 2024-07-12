from zExceptions import Unauthorized
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery
if REQUEST is not None:
  raise Unauthorized

assert context.getPortalType() == "Category"
assert context.getIntIndex() < 0
assert context.getRelativeUrl().startswith("portal_categories/region/"), \
  "The context (%s) is not a region"

if context.getValidationState() == 'expired':
  # skip, we seems to be rerunning the migration
  # and some reindexation is going on.
  return []

related_document_list = context.Base_getRelatedObjectList(**{
  'portal_type': NegatedQuery(SimpleQuery(portal_type='Category')),
  'category.category_strict_membership': 1})

for document in related_document_list:
  # XXX Can we do better them use replace?
  if document.isMemberOf(context.getRelativeUrl().replace("portal_categories/", "")):
    document.edit(
      region=new_category.getRelativeUrl(),
      activate_kw={'tag': 'edit_%s' % (context.getRelativeUrl())})
  else:
    # Trigger reindex since the the member was edited
    # use tag to ensure it happens after the edit is reindexed.
    document.reindexObject(
      activate_kw={'after_tag': 'edit_%s' % (context.getRelativeUrl())})

context.expire()
