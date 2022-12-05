portal = context.getPortalObject()
invoice = context.SubscriptionRequest_verifyPaymentBalanceIsReady()

if invoice is not None:
  if invoice.SaleInvoiceTransaction_isLettered():
    # Invoice is payed
    return True
  
  person = context.getDestinationSectionValue()

  contract = portal.portal_catalog.getResultValue(
    portal_type="Cloud Contract",
    default_destination_section_uid=person.getUid(),
    validation_state=['invalidated', 'validated'],
  )

  if (contract is not None and contract.getMaximumInvoiceDelay() > 0 and \
      not (person.Entity_statSlapOSOutstandingAmount() > 0)):
    return True

# Invoice isn't payed
return False
