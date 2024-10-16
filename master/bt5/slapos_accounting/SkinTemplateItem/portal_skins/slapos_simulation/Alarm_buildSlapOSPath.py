portal = context.getPortalObject()

kw = {}
select_dict= {'delivery_uid': None}
kw.update(
  portal_type='Simulation Movement',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  # This is an optimisation to help mariadb selecting a better index
  simulation_state=['draft', 'planned', None],
  left_join_list=select_dict.keys(),
  delivery_uid=None
)

sql_result_list = portal.portal_catalog(
  # Group by business link and trade condition,
  # as SimulationMovement_buildSlapOS will use those filters
  # to simplify grouping of simulation movements
  group_by_list=['causality_uid', 'specialise_uid'],
  **kw
)

for sql_result in sql_result_list:
  movement = sql_result.getObject()
  if not movement.checkConsistency():
    # Only build simulation movement without a consistency error
    # wait for existing packing list to be solve before aggregating more movements
    movement.activate(activity='SQLQueue', tag=tag, after_method_id='updateCausalityState').SimulationMovement_buildSlapOS(tag=tag)

# register activity on alarm object waiting for own tag in order to have only one alarm
# running in same time
context.activate(after_tag=tag).getId()
