payzen_event = state_change['object']
payment_transaction = payzen_event.getDestinationValue(portal_type="Payment Transaction")

transaction_date, transaction_number = payment_transaction.PaymentTransaction_getPayzenId()
if transaction_number is None:
  raise ValueError('Transaction not registered in payzen integration tool')

transaction_id = transaction_date.Date().replace("/", "") + "-" + transaction_number

payment_service = payzen_event.getSourceValue(portal_type="Payzen Service")
data_kw, sent_text, received_text = payment_service.rest_getInfo(
  transaction_date.toZone('UTC').asdatetime(),
  transaction_id)

# SENT
sent = payzen_event.newContent(
  title='Sent Data', 
  portal_type='Payzen Event Message', 
  text_content=sent_text)

# RECEIVED
payzen_event.newContent(
  title='Received Data', 
  portal_type='Payzen Event Message', 
  text_content=received_text, 
  successor_value=sent)
payzen_event.PayzenEvent_processUpdate(data_kw)
