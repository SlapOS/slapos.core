portal = context.getPortalObject()

activate_kw = {'tag': tag}
select_dict= {'causality__uid': None}

portal.portal_catalog.searchAndActivate(
  portal_type='Payment Transaction',
  simulation_state='stopped',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),

  # Only check standalone payment
  left_join_list=select_dict.keys(),
  causality__uid=None,

  method_id='PaymentTransaction_acceptDepositPayment',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)
context.activate(after_tag=tag).getId()
