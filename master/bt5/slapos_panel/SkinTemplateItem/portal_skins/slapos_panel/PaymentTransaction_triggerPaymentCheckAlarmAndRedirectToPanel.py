web_site = context.getWebSiteValue()
assert web_site is not None

context.Base_reindexAndSenseAlarm([
  'slapos_payzen_update_started_payment',
  'slapos_wechat_update_started_payment',
  'slapos_cancel_sale_invoice_transaction_paied_payment_list'
])

from ZTUtils import make_query
hash_dict = {
  'page': 'slapos_master_panel_external_payment_result',
  'result': result
}

base = web_site.absolute_url()
# when accessed from web_site_module/xxx_panel , absolute_url does not add the required / prefix
if not base.endswith('/'):
  base = base + '/'

return context.REQUEST.RESPONSE.redirect('%s#/?%s' % (base, make_query(hash_dict)))
