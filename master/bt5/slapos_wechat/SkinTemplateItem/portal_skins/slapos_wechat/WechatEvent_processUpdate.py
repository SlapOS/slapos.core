from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

def storeWorkflowComment(ctx, comment):
  portal = ctx.getPortalObject()
  workflow_tool = portal.portal_workflow
  workflow_tool.doActionFor(ctx, 'edit_action', comment=comment)

wechat_event = context
transaction = wechat_event.getDestinationValue()
isTransitionPossible = transaction.getPortalObject().portal_workflow.isTransitionPossible

error_code = data_kw['result_code']

if error_code == 'FAIL':
  transaction_date, _ = transaction.PaymentTransaction_getWechatId()
  # Mark on payment transaction history log that transaction was not processed yet
  wechat_event.confirm()
  wechat_event.acknowledge(comment='Error when getting transaction status: %s' % data_kw['err_code'])
  if int(DateTime()) - int(transaction_date) > 86400:
    if isTransitionPossible(transaction, 'cancel'):
      transaction.cancel(comment='Aborting failing wechat payment.')
  else:
    storeWorkflowComment(transaction,
                         'Error code FAIL did not changed the document state.')
  return

elif error_code == 'SUCCESS':
  transaction_code_mapping = {
    'SUCCESS' : 'Payment successful',
    'REFUND' : 'Order to be refunded',
    'NOTPAY' : 'Order not paid',
    'CLOSED' : 'Order closed',
    'REVOKED' : 'Order revoked',
    'USERPAYING' : 'Awaiting user to pay'
  }
  mark_transaction_id_list = ['USERPAYING', 'NOTPAY']
  continue_transaction_id_list = ['SUCCESS']
  cancel_transaction_id_list = ['REFUND', 'CLOSED']

  transaction_status = data_kw['trade_state']

  transaction_status_description = transaction_code_mapping.get(transaction_status, None)
  if transaction_status_description is None:
    wechat_event.confirm(comment='Unknown transactionStatus %r' % transaction_status)
    return

  if transaction_status in mark_transaction_id_list:
    # Mark on payment transaction history log that transaction was not processed yet
    storeWorkflowComment(transaction, 'Transaction status %s (%s) did not changed the document state' % (transaction_status, transaction_status_description))
    wechat_event.confirm()
    wechat_event.acknowledge(comment='Automatic acknowledge as result of correct communication')
    if isTransitionPossible(transaction, 'confirm'):
      transaction.confirm(comment='Confirmed as really saw in WeChat.')

    transaction_date, _ = transaction.PaymentTransaction_getWechatId()
    if transaction_status == "NOTPAY" and int(DateTime()) - int(transaction_date) > 86400:
      if isTransitionPossible(transaction, 'cancel'):
        transaction.cancel(comment='Aborting failing wechat payment.')

  elif transaction_status in continue_transaction_id_list:
    # Check authAmount and authDevise and if match, stop transaction
    auth_amount = int(data_kw['total_fee'])
    auth_devise = data_kw['fee_type']
    transaction_amount = int(round((transaction.PaymentTransaction_getTotalPayablePrice() * -100), 2))

    if transaction_amount != auth_amount:
      wechat_event.confirm(comment='Received amount (%r) does not match stored on transaction (%r)'% (auth_amount, transaction_amount))
      return

    transaction_devise = transaction.getResourceValue().Currency_getIntegrationMapping()
    if transaction_devise != auth_devise:
      wechat_event.confirm(comment='Received devise (%r) does not match stored on transaction (%r)'% (auth_devise, transaction_devise))
      return

    comment = 'WeChat considered as paid.'
    if isTransitionPossible(transaction, 'confirm'):
      transaction.confirm(comment=comment)
    if isTransitionPossible(transaction, 'start'):
      transaction.start(comment=comment)
    if isTransitionPossible(transaction, 'stop'):
      transaction.stop(comment=comment)

    if transaction.getSimulationState() == 'stopped':
      wechat_event.confirm()
      wechat_event.acknowledge(comment='Automatic acknowledge as result of correct communication')
    else:
      wechat_event.confirm(comment='Expected to put transaction in stopped state, but achieved only %s state' % transaction.getSimulationState())

  elif transaction_status in cancel_transaction_id_list:
    wechat_event.confirm()
    wechat_event.acknowledge(comment='Refused wechat payment.')
    if isTransitionPossible(transaction, 'cancel'):
      transaction.cancel(comment='Aborting refused wechat payment.')
    return
  else:
    wechat_event.confirm(comment='Transaction status %r (%r) is not supported' \
                           % (transaction_status, transaction_status_description))
    return

else:
  # Unknown errorCode
  wechat_event.confirm(comment='Unknown Wechat result_code %r' % error_code)
