from DateTime import DateTime
wechat_event = state_change['object']

payment_service = wechat_event.getSourceValue(portal_type="Wechat Service")
return payment_service.navigate(
  page_template='wechat_event',
  pay='Click to pay',
  # payzen_dict=payzen_dict,
)
