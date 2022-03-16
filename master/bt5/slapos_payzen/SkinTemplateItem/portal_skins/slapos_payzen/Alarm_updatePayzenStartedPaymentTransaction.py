kw = {}
if params is None:
  params = {}

from DateTime import DateTime

now = DateTime()

last_active_process = context.getLastActiveProcess()
if not params.get('full', False) and last_active_process is not None:
  last_active_process_start_date = last_active_process.getStartDate()

  if (last_active_process_start_date + 0.02083) > now:
    kw['indexation_timestamp'] = '>= %s' % last_active_process_start_date.ISO()
  else:
    context.newActiveProcess().getRelativeUrl()
else:
  context.newActiveProcess().getRelativeUrl()

portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
      portal_type="Payment Transaction", 
      simulation_state=["started"],
      causality_state=["draft"],
      payment_mode_uid=portal.portal_categories.payment_mode.payzen.getUid(),
      method_id='PaymentTransaction_updateStatus',
      packet_size=1, # just one to minimise errors
      activate_kw={'tag': tag},
      **kw
      )
context.activate(after_tag=tag).getId()
