web_site = context.getWebSiteValue()
base_url = web_site.absolute_url()
# portal = context.getPortalObject()

# subscription_request = portal.subscription_request_module.get(trade_no)
context.Base_finishThePayment()
# if not subscription_request:
#   raise Exception("Order not found")

# subscription_request.confirmed()

return context.REQUEST.RESPONSE.redirect("%s/gadget_rapid_page_order_wechat_simulation_confirm.html/" % base_url)
