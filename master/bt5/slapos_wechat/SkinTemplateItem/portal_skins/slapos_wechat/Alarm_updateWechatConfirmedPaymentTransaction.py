portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
      portal_type="Payment Transaction",
      simulation_state=["confirmed"],
      causality_state=["draft"],
      payment_mode_uid=portal.portal_categories.payment_mode.wechat.getUid(),
      method_id='PaymentTransaction_startWechatPayment',
      packet_size=1, # just one to minimise errors
      activate_kw={'tag': tag}
      )
context.activate(after_tag=tag).getId()
