from DateTime import DateTime
wechat_event = state_change['object']

payment_service = wechat_event.getSourceValue(portal_type="Wechat Service")
return payment_service.navigate(
  wechat_dict=wechat_dict
)
