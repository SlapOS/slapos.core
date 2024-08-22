if brain is None:
  brain = context

software_instance = brain.getAggregateRelatedValue(portal_type=["Software Instance"])
if software_instance is None:
  return None

instance_tree = software_instance.getSpecialiseValue()

if url_dict: # If RenderJS UI
  jio_key = instance_tree.getRelativeUrl()
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'slapos_panel_view',
      'jio_key': jio_key,
    },
    'options': {
      'jio_key': jio_key
    },
  }
else:
  return instance_tree.absolute_url()
