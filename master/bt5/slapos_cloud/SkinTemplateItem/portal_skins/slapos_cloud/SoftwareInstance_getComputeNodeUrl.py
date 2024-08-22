if brain is None:
  brain = context

partition = brain.getAggregateValue()
if partition is None:
  return None

compute_node = partition.getParent()

if url_dict: # If RenderJS UI
  jio_key = compute_node.getRelativeUrl()
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
  return compute_node.absolute_url()
