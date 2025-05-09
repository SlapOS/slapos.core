keep_items = None
portal = context.getPortalObject()

if aggregate_uid is None:
  software_product_list = [x for x in portal.portal_catalog(
    portal_type='Software Product Release Variation',
    url_string=url_string
  ) if x.getFollowUpUid() == context.getUid()]
  if len(software_product_list) == 1:
    software_product = software_product_list[0].getParentValue()

    keep_items = {
      'field_your_aggregate_uid': software_product.getUid(),
      'your_aggregate_uid': software_product.getUid(),
      'aggregate_uid': software_product.getUid()
    }

return context.Base_renderForm(
  'Project_viewRequestInstanceTreeDialog', keep_items=keep_items
)
