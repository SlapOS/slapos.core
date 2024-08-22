if brain is None:
  brain = context

instance = brain.getAggregateRelatedValue(portal_type=["Software Instance"])
if instance is None:
  return None

owner = instance.getSpecialiseValue().getDestinationSectionValue()

if url_dict: # If RenderJS UI
  jio_key = owner.getRelativeUrl()
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
  return owner.absolute_url()
