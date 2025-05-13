portal = context.getPortalObject()
translateString = context.Base_translateString

result = ''
is_one_future_balance_negative = False

software_product_release_variation = portal.portal_catalog.getResultValue(
  portal_type='Software Product Release Variation',
  parent_uid=software_product_uid,
  url_string=url_string
)

if software_product_release_variation is not None:

  software_product = software_product_release_variation.getParentValue()
  destination_value = portal.portal_membership.getAuthenticatedMember().getUserValue()
  allocation_predicate_list = context.Project_getSoftwareProductPredicateList(
    software_product=software_product,
    software_product_release=software_product_release_variation,
    destination_value=destination_value)

  if allocation_predicate_list:
    def wrapWithShadow(destination_value, variation_category_list, project):
      try:
        subscription_request = software_product.Resource_createSubscriptionRequest(
          destination_value,
          # [software_type, software_release],
          variation_category_list,
          project,
          temp_object=True
        )
      except AssertionError:
        price = 0.0
      else:
        price = subscription_request.getPrice(None)

      is_future_balance_negative = 0
      price_information = None
      # If the payment is done by an Organisation, skip user payment process
      if (price is not None) and (price != 0) and (subscription_request.getDestinationSection() == destination_value.getRelativeUrl()):
        price_information = '%s: %s %s/%s' % (subscription_request.getSoftwareTypeTitle(), price,
          subscription_request.getPriceCurrencyShortTitle(),
          subscription_request.getQuantityUnitTitle())

        assert subscription_request.getDestinationDecision() == destination_value.getRelativeUrl()
        assert subscription_request.getLedger() == "automated"
        balance = destination_value.Entity_getDepositBalanceAmount(
          [subscription_request]
        )
        if balance - price < 0:
          is_future_balance_negative = 1

      return price_information, is_future_balance_negative

    for allocation_predicate in allocation_predicate_list:
      # Shadow user may not have access to the allocation predicates, so get the variation
      # relative url as the logged user.
      variation_category_list = allocation_predicate.getVariationCategoryList()
      price_information, is_future_balance_negative = destination_value.Person_restrictMethodAsShadowUser(
          shadow_document=destination_value,
          callable_object=wrapWithShadow,
          argument_list=[destination_value, variation_category_list, context])

      if price_information is not None:
        result += '- %s\n' % (price_information)
        is_one_future_balance_negative = is_one_future_balance_negative or is_future_balance_negative

if is_one_future_balance_negative:
  result += '\n%s\n' % translateString("You are going to be redirected to Payment")

return result
