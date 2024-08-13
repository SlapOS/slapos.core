portal = context.getPortalObject()

kw = {}
select_dict = {'causality__related__uid': None}
kw.update(
  portal_type='Sale Packing List',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  # Only payable deliveries are expanded
  # (it prevents the alarm to always those non expandable deliveries)
  source_section__uid='%',
  destination_section__uid='%',
  # This is an optimisation to help mariadb selecting a better index
  simulation_state=['delivered'],

  left_join_list=select_dict.keys(),
  causality__related__uid=None,

  method_id='updateSimulation',
  packet_size=1, # Separate calls to many transactions
  method_kw={'expand_root': 1},
  activate_kw={'tag': tag},
)

portal.portal_catalog.searchAndActivate(
  causality__portal_type=[
    # Only Packing List created to generate deposit Invoice need to be expanded
    'Payment Transaction',
    # Discount Sale Packing List
    'Subscription Request',
    'Subscription Change Request'
  ],
  **kw
)

# register activity on alarm object waiting for own tag in order to have only one alarm
# running in same time
context.activate(after_tag=tag).getId()
