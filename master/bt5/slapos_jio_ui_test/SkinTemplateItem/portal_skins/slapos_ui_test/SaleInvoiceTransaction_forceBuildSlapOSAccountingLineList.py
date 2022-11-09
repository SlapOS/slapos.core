kw = {}
select_dict= {'delivery_uid': None}
kw.update(
  portal_type='Simulation Movement',
  # This is an optimisation to help mariadb selecting a better index
  simulation_state=['draft', 'planned', None],
  left_join_list=select_dict.keys(),
  delivery_uid=None
)

applied_rule = context.getCausalityRelated(portal_type="Applied Rule")
for simulation_movement in context.getPortalObject().portal_catalog(
  path="%%%s%%" % applied_rule, **kw):

  if simulation_movement.getDelivery() is not None:
    # movement build but not indexed, so do nothing
    continue

  root_applied_rule = simulation_movement.getRootAppliedRule()
  root_applied_rule_path = root_applied_rule.getPath()

  business_link = simulation_movement.getCausalityValue(portal_type='Business Link')
  business_link.build(path='%s/%%' % root_applied_rule_path, activate_kw={'tag': "ForceBuild"})

return "Done."
