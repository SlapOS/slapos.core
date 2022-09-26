portal = context.getPortalObject()

kw['portal_type'] = ["Support Request", "Upgrade Decision"]
if 'default_or_child_aggregate_uid' not in kw:
  kw['default_or_child_aggregate_uid'] = context.getUid()
kw['sort_on'] = (('modification_date', 'DESC'),)
if 'simulation_state' not in kw:
  kw['simulation_state'] = ['validated','submitted', 'suspended', 'invalidated', 
                            # Unfortunally Upgrade decision uses diferent states.
                            'confirmed', 'started', 'stopped', 'delivered']
if 'limit' not in kw:
  kw['limit'] = 30
return portal.portal_catalog(**kw)
