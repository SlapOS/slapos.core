""" XXX This script expects some re-implementation to 
  rely on panel configuration for handle payment.
"""

portal = context.getPortalObject()

payment_mode = None
for accepted_currency_uid, accepted_payment_mode, is_activated in [
  (portal.currency_module.EUR.getUid(), 'payzen', portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY, 'wechat', portal.Base_getWechatServiceRelativeUrl())

]:
  if is_activated and (currency_uid == accepted_currency_uid):
    payment_mode = accepted_payment_mode

return payment_mode
