if brain is None:
  brain = context

partition = brain.getAggregateValue()
if partition is None:
  return None

computer = partition.getParent()

if url_dict: # If RenderJS UI
  jio_key = computer.getRelativeUrl()
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'view',
      'jio_key': jio_key,
    },
    'options': {
      'jio_key': jio_key
    },
  }
else:
  return computer.absolute_url()
