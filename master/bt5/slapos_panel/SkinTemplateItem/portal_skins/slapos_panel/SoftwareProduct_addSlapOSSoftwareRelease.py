from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
software_product = context

# First, search if the release already exists
software_release_variation = portal.portal_catalog.getResultValue(
  portal_type="Software Product Release Variation",
  url_string=software_release,
  parent__follow_up__uid=software_product.getFollowUpUid()
)
if software_release_variation is not None:
  return software_release_variation.Base_redirect(
    keep_items={
      'portal_status_message': translateString('Software Release already exist.')
    }
  )

software_release_variation = software_product.newContent(
  portal_type="Software Product Release Variation",
  title=software_release,
  url_string=software_release
)

if same_type(software_type_list, ""):
  software_type_list = [software_type_list]
for software_type in software_type_list:
  # Check if the software type already exist
  software_type_variation = portal.portal_catalog.getResultValue(
    portal_type="Software Product Type Variation",
    parent_uid=software_product.getUid(),
    title=software_type,
  )
  if software_type_variation is None:
    software_product.newContent(
      portal_type="Software Product Type Variation",
      title=software_type
    )

return software_release_variation.Base_redirect(
  keep_items={
    'portal_status_message': translateString('New Software Release created.')
  })
