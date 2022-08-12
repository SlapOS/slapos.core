from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()

# First, search if the release already exists
software_release_variation = portal.portal_catalog.getResultValue(
  portal_type="Software Product Release Variation",
  url_string=software_release,
  parent__follow_up__uid=context.getUid()
)
if software_release_variation is not None:
  return software_release_variation.getParentValue().Base_redirect(
    keep_items={
      'portal_status_message': translateString('Software Product already exist.')
    }
  )

software_product = portal.software_product_module.newContent(
  title=title,
  follow_up_value=context
)
software_product.newContent(
  portal_type="Software Product Release Variation",
  title=software_release,
  url_string=software_release
)

if same_type(software_type_list, ""):
  software_type_list = [software_type_list]
for software_type in software_type_list:
  software_product.newContent(
    portal_type="Software Product Type Variation",
    title=software_type
  )
software_product.validate()

return software_product.Base_redirect(
  keep_items={
    'portal_status_message': translateString('New Software Product created.')
  }
)
