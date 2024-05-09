portal = context.getPortalObject()

# Assume a default payment_mode in general
payment_mode = 'wire_transfer'
for accepted_currency_uid, accepted_payment_mode, is_activated in [
  (portal.currency_module.EUR.getUid(), 'payzen', portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY, 'wechat', portal.Base_getWechatServiceRelativeUrl())

]:
  if is_activated and (currency_uid == accepted_currency_uid):
    payment_mode = accepted_payment_mode

return payment_mode
