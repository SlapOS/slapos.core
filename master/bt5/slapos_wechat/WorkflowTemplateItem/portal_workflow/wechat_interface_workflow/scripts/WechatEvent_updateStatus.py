wechat_event = state_change['object']
#raise NotImplementedError(wechat_event, "In WechatEvent_updateStatus")
payment_transaction = wechat_event.getDestinationValue(portal_type="Payment Transaction")

_, transaction_id = payment_transaction.PaymentTransaction_getWechatId()
if transaction_id is None:
  raise ValueError('Transaction not registered in wechat integration tool')

payment_service = wechat_event.getSourceValue(portal_type="Wechat Service")

query_dict = {'out_trade_no': transaction_id}
wechat_answer_dict = payment_service.queryWechatOrderStatus(query_dict)

# SENT over query
sent = wechat_event.newContent(
  title='Query Order Status',
  portal_type='Wechat Event Message',
  text_content=query_dict)

# Received
wechat_event.newContent(
  title='Received Order Status',
  portal_type='Wechat Event Message',
  text_content=wechat_answer_dict,
  successor_value=sent)
wechat_event.WechatEvent_processUpdate(wechat_answer_dict)
