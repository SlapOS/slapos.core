from Products.ERP5Type.Message import translateString
payment_transaction = context

comment = translateString("Initialised by Order Builder.")
payment_transaction.confirm(comment=comment)
