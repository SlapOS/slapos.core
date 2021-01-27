from Products.ERP5Type.Message import translateString
payment_transaction = context

invoice = context.getCausalityValue()
context.setStartDate(invoice.getStartDate())
context.setStopDate(invoice.getStopDate())

comment = translateString("Initialised by Order Builder.")
payment_transaction.confirm(comment=comment)

# Reindex with a tag to ensure that there will be no generation while the object isn't
# reindexed.
payment_tag ="sale_invoice_transaction_order_builder_%s" % context.getCausalityUid()
payment_transaction.activate(tag=payment_tag).immediateReindexObject()

# Set a flag on the request for prevent 2 calls on the same transaction
context.REQUEST.set(payment_tag, 1)
