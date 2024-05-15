from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
software_product = context

# First, search if the type already exists
software_type_variation = portal.portal_catalog.getResultValue(
  portal_type="Software Product Type Variation",
  parent_uid=software_product.getUid(),
  title=software_type
)
if software_type_variation is not None:
  return software_product.Base_redirect(
    keep_items={
      'portal_status_message': translateString('Software Type already exist.')
    }
  )

software_product.newContent(
  portal_type="Software Product Type Variation",
  title=software_type
)

return software_product.Base_redirect(
  keep_items={
    'portal_status_message': translateString('New Software Type created.')
  })
