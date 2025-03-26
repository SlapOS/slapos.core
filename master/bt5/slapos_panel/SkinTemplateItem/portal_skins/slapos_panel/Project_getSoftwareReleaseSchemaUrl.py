from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

# Ensure this script is called on the expected context
# for futur compatibility
assert context.getPortalType() == 'Project'
portal = context.getPortalObject()
default_json_schema_url = software_release_url.split("?")[0] + ".json"

use_category_uid = portal.restrictedTraverse("portal_categories/use/trade/sale").getUid(),
product_list = portal.portal_catalog(
  portal_type="Software Product",
  validation_state=['validated', 'published'],
  use__uid=use_category_uid,
  follow_up__uid=context.getUid()
)
if len(product_list) != 0:
  software_release = portal.portal_catalog.getResultValue(
    portal_type="Software Product Release Variation",
    url_string=software_release_url,
    parent_uid=[x.getUid() for x in product_list]
  )
  if software_release is not None:
    return software_release.getSoftwareSchemaLinkUrlString(default_json_schema_url)
