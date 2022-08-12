keep_items = None

if aggregate_uid is None:
  software_product_list = [x for x in context.getPortalObject().portal_catalog(
    portal_type='Software Product Release Variation',
    url_string=url_string
  ) if x.getFollowUpUid() == context.getUid()]
  if len(software_product_list) == 1:
    keep_items = {
      'field_your_aggregate_uid': software_product_list[0].getParentUid(),
      'your_aggregate_uid': software_product_list[0].getParentUid(),
      'aggregate_uid': software_product_list[0].getParentUid()

    }
    context.log('keep_items %s' % str(keep_items))

return context.Base_renderForm(
  'Project_viewRequestInstanceTreeDialog', keep_items=keep_items
)
