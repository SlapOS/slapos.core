from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

# It is mandatory use pass a contract to skip reservation
# as annonymous can request via website knowning the user's
# email  
if contract is None:
  return

if context.SubscriptionRequest_getTransactionalUser() is not None:
  if contract is not None and contract.getMaximumInvoiceDelay() > 0:
    return True
else:
  person = context.getDestinationSectionValue()
  if person.Entity_statSlapOSOutstandingAmount() > 0:
    return
  
  if contract is not None and contract.getMaximumInvoiceDelay() > 0:
    return True
