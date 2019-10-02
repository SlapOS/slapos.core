wechat_event = state_change['object']
raise NotImplementedError(wechat_event, "In WechatEvent_updateStatus")
payment_transaction = wechat_event.getDestinationValue(portal_type="Payment Transaction")
portal = payment_transaction.getPortalObject()

transaction_date, transaction_id = payment_transaction.PaymentTransaction_getPayzenId()
if transaction_id is None:
  raise ValueError('Transaction not registered in wechat integration tool')

payment_service = wechat_event.getSourceValue(portal_type="Wechat Service")
data_kw, signature, sent_text, received_text = payment_service.soap_getInfo(
  transaction_date.toZone('UTC').asdatetime(),
  transaction_id)

sent = wechat_event.newContent(
  title='Sent SOAP',
  portal_type='Wechat Event Message',
  text_content=sent_text)
received = wechat_event.newContent(
  title='Received SOAP',
  portal_type='Wechat Event Message',
  text_content=received_text,
  predecessor_value=sent)
wechat_event.WechatEvent_processUpdate(data_kw, signature)
