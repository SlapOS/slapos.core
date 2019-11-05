from DateTime import DateTime
wechat_event = state_change['object']

# Get required arguments
#kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
#try:
#  vads_url_cancel = kwargs['vads_url_cancel']
#  vads_url_error = kwargs['vads_url_error']
#  vads_url_referral = kwargs['vads_url_referral']
#  vads_url_refused = kwargs['vads_url_refused']
#  vads_url_success = kwargs['vads_url_success']
#  vads_url_return = kwargs['vads_url_return']
#except KeyError:
#  raise TypeError, "PayzenEvent_generateNavigationPage takes exactly 6 arguments"

payment_transaction = wechat_event.getDestinationValue(portal_type="Payment Transaction")
now = DateTime()
payment_transaction.AccountingTransaction_updateStartDate(now)

transaction_date, transaction_id = payment_transaction.PaymentTransaction_generateWechatId()
if transaction_id is None:
  raise ValueError, "Transaction already registered"

today = now.toZone('UTC').asdatetime().strftime('%Y%m%d')
wechat_dict = {
  'out_trade_no': payment_transaction.getRelativeUrl().split('/')[1].encode('utf-8'),
  'total_fee': 1, #str(int(round((payment_transaction.PaymentTransaction_getTotalPayablePrice() * -100), 0))),
  'fee_type': "CNY", #payment_transaction.getResourceValue().Currency_getIntegrationMapping(),
  'body': "Rapid Space Virtual Machine".encode('utf-8')
  #'vads_trans_date': now.toZone('UTC').asdatetime().strftime('%Y%m%d%H%M%S'),
  #'vads_trans_id': transaction_id,
  # TODO
}

html_document = context.WechatEvent_callWechatServiceNavigation(state_change, wechat_dict)
wechat_event.newContent(
  title='Shown Page',
  portal_type='Wechat Event Message',
  text_content=html_document,
)

wechat_event.confirm()
wechat_event.acknowledge(comment='Automatic acknowledge as result of correct communication')
