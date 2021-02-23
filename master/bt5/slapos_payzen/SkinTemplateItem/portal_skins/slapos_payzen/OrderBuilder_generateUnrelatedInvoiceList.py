portal = context.getPortalObject()
newTempSimulationMovement = portal.portal_trash.newContent

select_dict = {
  'causality_payment_transaction_related_uid': None,
  'causality_subscription_request_related_uid': None,
}

select_kw = kwargs.copy()
select_kw.pop('portal_type', None)
select_kw.pop('delivery_relative_url_list', None)
select_kw.update(
  portal_type='Sale Invoice Transaction',
  simulation_state='stopped',
  default_payment_mode_uid=(portal.portal_categories.payment_mode.payzen.getUid(),
                            portal.portal_categories.payment_mode.wechat.getUid()),
  limit=10, # do only some in one shot
  select_dict=select_dict,
  left_join_list=select_dict.keys(),
  causality_payment_transaction_related_uid=None,
  causality_subscription_request_related_uid=None
)

default_source_uid=portal.restrictedTraverse('account_module/receivable').getUid()
movement_list = []
_id = 1
for invoice in portal.portal_catalog(**select_kw):
  invoice.getObject().serialize() # in order to avoid selection on concurrent transactions

  payment_tag = "sale_invoice_transaction_order_builder_%s" % invoice.getObject().getUid()
  if context.REQUEST.get(payment_tag, None) is not None or \
    context.portal_activities.countMessageWithTag(payment_tag) > 0:
    # Invoice was selected before the payment be indexed or it was already created on this transaction
    # so skip the invoice for now.
    continue
  quantity = 0.
  for movement in invoice.searchFolder(portal_type='Sale Invoice Transaction Line',
    default_source_uid=default_source_uid):
    quantity += movement.getQuantity()
  temp_movement_kw = dict(
    portal_type="Simulation Movement",
    causality=invoice.getRelativeUrl(),
    source_section=invoice.getSourceSection(),
    destination_section=invoice.getDestinationSection(),
    resource=invoice.getResource(),
    price_currency=invoice.getResource(),
    start_date=invoice.getStartDate(),
    stop_date=invoice.getStopDate(),
    specialise=invoice.getSpecialise(),
    payment_mode=invoice.getPaymentMode(),
    source_payment='%s/bank_account' % invoice.getSourceSection(), # the other place defnied: business process
  )
  temp_movement_rec = newTempSimulationMovement(
    temp_object=True, id=str(_id),
    quantity=-1 * quantity,
    source='account_module/receivable',
    destination='account_module/payable',
    **temp_movement_kw
  )
  _id += 1
  temp_movement_bank = newTempSimulationMovement(
    temp_object=True, id=str(_id),
    quantity=1 * quantity,
    source='account_module/payment_to_encash',
    destination='account_module/payment_to_encash',
    **temp_movement_kw
  )
  _id += 1
  movement_list.extend([temp_movement_rec, temp_movement_bank])

return movement_list
