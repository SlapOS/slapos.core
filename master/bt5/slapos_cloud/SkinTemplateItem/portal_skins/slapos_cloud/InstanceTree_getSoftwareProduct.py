portal = context.getPortalObject()
url_string = context.getUrlString()
software_product = None
software_release = None
software_type = None

if url_string:

  use_category_uid = portal.restrictedTraverse("portal_categories/use/trade/sale").getUid(),
  product_list = portal.portal_catalog(
    portal_type="Software Product",
    validation_state=['validated', 'published'],
    use__uid=use_category_uid,
    follow_up__uid=context.getFollowUpUid()
  )

  if len(product_list) != 0:
    software_release = portal.portal_catalog.getResultValue(
      portal_type="Software Product Release Variation",
      url_string=url_string,
      parent_uid=[x.getUid() for x in product_list]
    )

    if software_release is not None:
      software_product = software_release.getParentValue()

      software_type = portal.portal_catalog.getResultValue(
        parent_uid=software_product.getUid(),
        title={'query': context.getSourceReference(), 'key': 'ExactMatch'},
        portal_type="Software Product Type Variation"
      )

      if software_type is None:
        software_release = None
        software_product = None

return software_product, software_release, software_type
