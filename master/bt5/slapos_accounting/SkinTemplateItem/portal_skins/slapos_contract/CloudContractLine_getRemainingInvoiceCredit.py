person = context.getParentValue().getDestinationSectionValue()
amount = person.Entity_statOutstandingAmount(
  resource_uid=context.getPriceCurrencyUid())

return context.getMaximumInvoiceCredit() - amount
