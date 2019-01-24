software_instance = context
portal = context.getPortalObject()

software_type = software_instance.getSourceReference()
software_release_url = software_instance.getUrlString()
software_release = portal.portal_catalog.getResultValue(
  portal_type='Software Release',
  url_string={'query': software_release_url, 'key': 'ExactMatch'})

software_instance_capacity = None
if software_release is not None:
  software_product = software_release.getAggregateValue()

  # Search for Software Product Individual Variation with same reference
  software_product = software_release.getAggregateValue()
  if software_product is not None:
    for variation in software_product.searchFolder(
        portal_type="Software Product Individual Variation",
        reference=software_type):
      software_instance_capacity = variation.getCapacityQuantity(None)
      if software_instance_capacity is not None:
        break

  if software_instance_capacity is None:
    software_instance_capacity = software_release.SoftwareRelease_getCapacity()

if software_instance_capacity is None:
  software_instance_capacity = 1

return software_instance_capacity
