kw = {}
if params is None:
  params = {}

from DateTime import DateTime

portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
      portal_type="Payment Transaction",
      simulation_state=["started"],
      causality_state=["draft"],
      payment_mode_uid=[
        portal.portal_categories.payment_mode.payzen.getUid(),
        portal.portal_categories.payment_mode.wechat.getUid()],
      method_id='PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered',
      packet_size=1, # just one to minimise errors
      activate_kw={'tag': tag},
      **kw
      )
context.activate(after_tag=tag).getId()
