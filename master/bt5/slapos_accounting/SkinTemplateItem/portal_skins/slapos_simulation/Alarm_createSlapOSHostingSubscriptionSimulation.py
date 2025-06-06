portal = context.getPortalObject()

kw = {}
# Search for the related root applied rule
select_dict = {'causality__related__uid': None}
kw.update(
  portal_type='Hosting Subscription',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  # This is an optimisation to help mariadb selecting a better index
  validation_state=['validated'],

  left_join_list=select_dict.keys(),
  causality__related__uid=None,

  method_id='updateSimulation',
  packet_size=1, # Separate calls to many transactions
  method_kw={'expand_root': 1},
  activate_kw={'tag': tag},
)

portal.portal_catalog.searchAndActivate(
  **kw
)

# register activity on alarm object waiting for own tag in order to have only one alarm
# running in same time
context.activate(after_tag=tag).getId()
