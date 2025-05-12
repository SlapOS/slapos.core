from DateTime import DateTime

project = context
portal = context.getPortalObject()

destination_value = portal.portal_membership.getAuthenticatedMember().getUserValue()

allocation_predicate_list = project.Project_getSoftwareProductPredicateList(destination_value=destination_value)

result_list = []
seen_dict = {}
result_dict = {}

for allocation_predicate in allocation_predicate_list:

  seen_key = "%s_%s_%s" % (
    allocation_predicate.getResource(),
    allocation_predicate.getSoftwareRelease(),
    allocation_predicate.getSoftwareType()
  )
  result_key = "%s_%s" % (
    allocation_predicate.getResource(),
    allocation_predicate.getSoftwareRelease()
  )

  if seen_key in seen_dict:
    continue
  seen_dict[seen_key] = True
  if result_key in result_dict:
    continue

  software_product = allocation_predicate.getResourceValue()

  try:
    subscription_request = software_product.Resource_createSubscriptionRequest(
      destination_value,
      # [software_type, software_release],
      allocation_predicate.getVariationCategoryList(),
      context,
      temp_object=True
    )
  except AssertionError:
    continue

  price = subscription_request.getPrice(None)
  if price is not None:
    title = '%s %s' % (software_product.getTitle(), allocation_predicate.getSoftwareReleaseTitle())
    result_list.append(allocation_predicate.asContext(
      title = title
    ))
    result_dict[result_key] = True

return sorted(result_list, key=lambda x: x.getTitle())
