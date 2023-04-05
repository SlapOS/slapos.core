from DateTime import DateTime

portal = context.getPortalObject()

if software_release_url is None and \
      context.getPortalType() == "Software Product":
  software_product_reference = context.getReference()

if software_product_reference is None:
  assert(software_release_url is not None)
  software_release = portal.portal_catalog.getResultValue(
               portal_type='Software Release',
               url_string=software_release_url
    )
  if not software_release:
    return []
  
  if strict:
    return [software_release]

  software_product_reference = software_release.getAggregateReference()
  if not software_product_reference:
    return []

else:
  # Don't accept both parameters
  assert(software_release_url is None)

product_list = portal.portal_catalog(
           portal_type='Software Product',
           reference=software_product_reference,
           validation_state=['published', 'validated'],
           limit=2)

if not product_list:
  return []

if len(product_list) > 1:
  raise ValueError('Several Software Product with the same reference.')

software_release_list = product_list[0].getAggregateRelatedValueList()

def sortkey(software_release):
  publication_date = software_release.getEffectiveDate()
  delta = 0
  if software_release.getValidationState() == "archived":
    # Decrease 80 years, to be sure it goes last but still on the list
    delta = 365*80
  if publication_date:
    if (publication_date - DateTime()) > 0:
      # Decrease 100 years, to be sure it goes at the end of the queue
      delta = 365*100
    return publication_date - delta
  return software_release.getCreationDate() - delta

software_release_list = sorted(
         software_release_list,
         key=sortkey, reverse=True,
     )

return [software_release for software_release in software_release_list
          if software_release.getValidationState() in
            ["published", "published_alive", "archived"]]
