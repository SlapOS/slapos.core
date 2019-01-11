if brain is None:
  brain = context

aggregate_value_parent = brain.getAggregateValue().getParent()
jio_key = aggregate_value_parent.getRelativeUrl()

url = aggregate_value_parent.absolute_url()

if url_dict:
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'view',
      'jio_key': jio_key,
    },
    'options': {
      'jio_key': jio_key
          }
         }

return url
