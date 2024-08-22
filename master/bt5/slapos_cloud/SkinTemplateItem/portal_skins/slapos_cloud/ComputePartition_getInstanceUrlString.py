if brain is None:
  brain = context

software_instance = brain.getAggregateRelatedValue(portal_type=["Software Instance"])
if software_instance is None:
  return None

if url_dict: # If RenderJS UI
  jio_key = software_instance.getRelativeUrl()
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'slapos_panel_view',
      'jio_key': jio_key,
      'editable': 'true',
    },
    'options': {
      'jio_key': jio_key
    },
  }
else:
  return software_instance.absolute_url()
