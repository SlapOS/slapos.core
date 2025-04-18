"""
  Invoke all post upgrades in order to finish the slapos master configuration.

  All post configurations have to be placed as Constraints.
"""
with context.portal_activities.defaultActivateParameterDict({}, placeless=True):
  active_process = context.portal_activities.newActiveProcess(activate_kw={})

context.ERP5Site_checkUpgraderConsistency(fixit=1,
  active_process=active_process,
  filter_dict={"constraint_type": "post_upgrade"})

if not context.portal_alarms.isSubscribed():
  context.portal_alarms.subscribe()
