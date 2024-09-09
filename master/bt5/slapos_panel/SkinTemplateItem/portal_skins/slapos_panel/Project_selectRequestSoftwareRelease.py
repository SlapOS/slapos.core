keep_items = None
portal = context.getPortalObject()

if aggregate_uid is None:
  software_product_list = [x for x in context.getPortalObject().portal_catalog(
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

    destination_value = portal.portal_membership.getAuthenticatedMember().getUserValue()
    allocation_predicate_list = context.Project_getSoftwareProductPredicateList(
      software_product=software_product,
      software_product_release=software_product_list[0],
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
          price_information = '%s %s/%s' % (price,
            subscription_request.getPriceCurrencyTitle(),
            subscription_request.getQuantityUnitTitle())

          assert subscription_request.getDestinationDecision() == destination_value.getRelativeUrl()
          assert subscription_request.getLedger() == "automated"
          balance = destination_value.Entity_getDepositBalanceAmount(
            [subscription_request]
          )
          if balance - price < 0:
            is_future_balance_negative = 1

        return price_information, is_future_balance_negative

      # Shadow user may not have access to the allocation predicates, so get the variation
      # relative url as the logged user.
      variation_category_list = allocation_predicate_list[0].getVariationCategoryList()
      price_information, is_future_balance_negative = destination_value.Person_restrictMethodAsShadowUser(
          shadow_document=destination_value,
          callable_object=wrapWithShadow,
          argument_list=[destination_value, variation_category_list, context])

      if price_information is not None:
        keep_items['is_future_balance_negative'] = is_future_balance_negative
        keep_items['price_information'] = price_information

return context.Base_renderForm(
  'Project_viewRequestInstanceTreeDialog', keep_items=keep_items
)
