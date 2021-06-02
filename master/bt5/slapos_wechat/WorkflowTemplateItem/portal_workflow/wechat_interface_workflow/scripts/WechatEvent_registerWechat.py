"""Registers current transaction in payment

In order to not transmit sensitive information the registration is done by looking the newest
payzen related transaction for destination_section and doing its duplicate"""

from DateTime import DateTime
wechat_event = state_change['object']
transaction = wechat_event.getDestinationValue()
payment_service = wechat_event.getSourceValue(portal_type="Wechat Service")

previous_id = transaction.PaymentTransaction_getPreviousPayzenId()
if previous_id is None:
  wechat_event.confirm(comment='No previous id found')
  return

transaction_date, transaction_id = transaction.PaymentTransaction_generatePayzenId()
if transaction_id is None:
  raise ValueError('Transaction already mapped in integration tool.')

# do causality mapping in integration_site between transaction.getRelativeUrl and today + transaction_id
payzen_dict = {}
payzen_dict.update(
  devise=transaction.getResourceValue().Currency_getIntegrationMapping(),
  amount=str(int(round((transaction.PaymentTransaction_getTotalPayablePrice() * -100), 0))),
  presentationDate=transaction.getStartDate().toZone('UTC').asdatetime(),
  newTransactionId=transaction_id,
  transmissionDate=transaction_date.asdatetime(),
  transactionId=previous_id
)

data_kw, signature, sent_text, received_text = payment_service.soap_duplicate(**payzen_dict)

# SENT
sent = wechat_event.newContent(title='Sent SOAP',
                               portal_type='Wechat Event Message',
                              text_content=sent_text)

# RECEIVED
wechat_event.newContent(title='Received SOAP',
                        text_content=received_text,
                        successor_value=sent,
                        portal_type='Wechat Event Message')

context.WechatEvent_processUpdate(state_change, data_kw, signature)
