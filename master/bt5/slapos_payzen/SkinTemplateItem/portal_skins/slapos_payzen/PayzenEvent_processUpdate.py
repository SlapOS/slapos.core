from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

def storeWorkflowComment(ctx, comment):
  portal = ctx.getPortalObject()
  workflow_tool = portal.portal_workflow
  workflow_tool.doActionFor(ctx, 'edit_action', comment=comment)

payzen_event = context
transaction = payzen_event.getDestinationValue()

if transaction is None:
  raise ValueError("Unable to find related transaction")

isTransitionPossible = context.getPortalObject().portal_workflow.isTransitionPossible

status = data_kw['status']
answer = data_kw['answer']
if status != "SUCCESS":
  error_code = answer["errorCode"]
  if error_code == "PSP_010":
    # Transaction Not Found
    # Mark on payment transaction history log that transaction was not processed yet
    transaction_date, _ = transaction.PaymentTransaction_getPayzenId()

    payzen_event.confirm()
    payzen_event.acknowledge(comment='Transaction not found on payzen side.')

    if context.PayzenEvent_isPaymentExpired(transaction_date):
      if isTransitionPossible(transaction, 'cancel'):
        transaction.cancel(comment='Aborting unknown payzen payment.')
    else:
      storeWorkflowComment(transaction,
                         'Error code PSP_010 (Not found) did not changed the document state.')
    return
  else:
  # Unknown errorCode
    # https://payzen.io/pt-BR/rest/V4.0/api/errors-reference.html
    error_message = answer.get('errorMessage', '')
    payzen_event.confirm(comment='Unknown errorCode %r, message: %s' % (error_code, error_message))
    return

transaction_list = answer["transactions"]
if len(transaction_list) != 1:
  # Unexpected Number of Transactions
  payzen_event.confirm(comment='Unexpected Number of Transaction for this order')
  return

transaction_kw = transaction_list[0]

# See Full Status list at https://payzen.io/en-EN/rest/V4.0/api/kb/status_reference.html
mark_transaction_id_list = [
  'AUTHORISED_TO_VALIDATE',
  'WAITING_AUTHORISATION',
  'WAITING_AUTHORISATION_TO_VALIDATE',
]
continue_transaction_id_list = ['AUTHORISED', 'CAPTURED', 'PARTIALLY_AUTHORISED']
cancel_transaction_id_list = ['REFUSED']

transaction_status = transaction_kw['detailedStatus']

if transaction_status in mark_transaction_id_list:
  # Mark on payment transaction history log that transaction was not processed yet
  storeWorkflowComment(transaction, 'Transaction status %s did not changed the document state' % (transaction_status))
  payzen_event.confirm()
  payzen_event.acknowledge(comment='Automatic acknowledge as result of correct communication')
  if isTransitionPossible(transaction, 'confirm'):
    transaction.confirm(comment='Confirmed as really saw in PayZen.')

elif transaction_status in continue_transaction_id_list:
  # Check authAmount and authDevise and if match, stop transaction
  auth_amount = int(transaction_kw['transactionDetails']['cardDetails']['authorizationResponse']['amount'])
  auth_devise = transaction_kw['transactionDetails']['cardDetails']['authorizationResponse']['currency']
  # XXX use currency base_unit_quantity instead
  transaction_amount = int((round(transaction.PaymentTransaction_getTotalPayablePrice() * -100, 0)))

  if transaction_amount != auth_amount:
    payzen_event.confirm(comment='Received amount (%r) does not match stored on transaction (%r)'% (auth_amount, transaction_amount))
    return

  transaction_devise = transaction.getResourceReference()
  if transaction_devise != auth_devise:
    payzen_event.confirm(comment='Received devise (%r) does not match stored on transaction (%r)'% (auth_devise, transaction_devise))
    return

  comment = 'PayZen considered as paid.'
  if isTransitionPossible(transaction, 'confirm'):
    transaction.confirm(comment=comment)
  if isTransitionPossible(transaction, 'start'):
    transaction.start(comment=comment)
  if isTransitionPossible(transaction, 'stop'):
    transaction.stop(comment=comment)

  if transaction.getSimulationState() == 'stopped':
    payzen_event.confirm()
    payzen_event.acknowledge(comment='Automatic acknowledge as result of correct communication')
  else:
    payzen_event.confirm(comment='Expected to put transaction in stopped state, but achieved only %s state' % transaction.getSimulationState())

elif transaction_status in cancel_transaction_id_list:
  payzen_event.confirm()
  payzen_event.acknowledge(comment='Refused payzen payment.')
  if isTransitionPossible(transaction, 'cancel'):
    transaction.cancel(comment='Aborting refused payzen payment.')
  return
else:
  payzen_event.confirm(comment='Transaction status %r is not supported' \
                         % (transaction_status))
  return
