from DateTime import DateTime
wechat_event = state_change['object']

payment_transaction = wechat_event.getDestinationValue(portal_type="Payment Transaction")
now = DateTime()
payment_transaction.AccountingTransaction_updateStartDate(now)

_, transaction_id = payment_transaction.PaymentTransaction_generateWechatId()
if transaction_id is None:
  raise ValueError("Transaction already registered")

wechat_dict = {
  'out_trade_no': payment_transaction.getId().encode('utf-8'),
  'total_fee': int(round((payment_transaction.PaymentTransaction_getTotalPayablePrice() * -100), 0)),
  'fee_type': payment_transaction.getResourceValue().Currency_getIntegrationMapping(),
  'body': "Rapid Space Virtual Machine".encode('utf-8')
}

base_url = context.REQUEST.get('base_url', '')
if base_url:
  wechat_dict['base_url'] = base_url


html_document = context.WechatEvent_callWechatServiceNavigation(state_change, wechat_dict)
wechat_event.newContent(
  title='Shown Page',
  portal_type='Wechat Event Message',
  text_content=html_document,
)

wechat_event.confirm()
wechat_event.acknowledge(comment='Automatic acknowledge as result of correct communication')
